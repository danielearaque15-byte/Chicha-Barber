from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Importación del modelo Servicio para las promociones
from servicios.models import Servicios


# ==========================================================
# 1. CATEGORÍA
# ==========================================================
class Categoria(models.Model):
    codigo = models.AutoField(primary_key=True)
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la Categoría"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


# ==========================================================
# 2. PROVEEDOR
# ==========================================================
class Proveedor(models.Model):
    codigo = models.AutoField(primary_key=True)
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre del Proveedor"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    correo = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo Electrónico"
    )
    direccion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


# ==========================================================
# 3. MARCA
# ==========================================================
class Marca(models.Model):
    codigo = models.AutoField(primary_key=True)
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la Marca"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    estado = models.BooleanField(
        default=True,
        verbose_name="Estado"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"


# ==========================================================
# 4. PRODUCTO
# ==========================================================
class Producto(models.Model):
    codigo_producto = models.AutoField(primary_key=True)
    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )
    codigo_detalle_producto = models.ForeignKey(
        "DetalleProducto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="producto_principal",
        verbose_name="Detalle de Producto"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Producto"
    )
    descripcion = models.TextField(
        verbose_name="Descripción"
    )
    imagen = models.ImageField(
        upload_to="productos/",
        null=True,
        blank=True,
        verbose_name="Imagen"
    )
    estado = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio Base"
    )
    codigo_categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True,
        verbose_name="Categoría"
    )
    codigo_marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        related_name="productos",
        null=True,
        blank=True,
        verbose_name="Marca"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            self.codigo = f"PROD-{self.codigo_producto:05d}"
            super().save(update_fields=["codigo"])

    @property
    def stock_actual(self):
        if self.codigo_detalle_producto:
            return self.codigo_detalle_producto.cantidad_actual
        try:
            return self.detalle_producto.cantidad_actual
        except DetalleProducto.DoesNotExist:
            return 0

    @property
    def precio_venta_actual(self):
        adquisicion = self.adquisiciones.order_by("-fecha", "-codigo").first()
        if adquisicion:
            return adquisicion.precio_venta
        return self.precio

    @property
    def precio_compra_actual(self):
        adquisicion = self.adquisiciones.order_by("-fecha", "-codigo").first()
        if adquisicion:
            return adquisicion.precio_compra
        return 0

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


# ==========================================================
# 5. DETALLE PRODUCTO
# ==========================================================
class DetalleProducto(models.Model):
    codigo = models.AutoField(primary_key=True)
    codigo_producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name="detalle_producto",
        null=True,
        blank=True,
        verbose_name="Producto"
    )
    cantidad_actual = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad Actual"
    )
    stock_min = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock Mínimo"
    )
    stock_max = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock Máximo"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def __str__(self):
        if self.codigo_producto:
            return f"{self.codigo_producto.nombre} - Stock: {self.cantidad_actual}"
        return f"Detalle Producto #{self.codigo}"

    class Meta:
        verbose_name = "Detalle de Producto"
        verbose_name_plural = "Detalles de Productos"


# ==========================================================
# 6. MOVIMIENTO DE PRODUCTO
# ==========================================================
class MovimientoProducto(models.Model):
    codigo = models.AutoField(primary_key=True)
    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
    ]
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="movimientos",
        verbose_name="Producto"
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha"
    )
    observacion = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Observación"
    )

    def __str__(self):
        return f"{self.codigo_producto.codigo} - {self.tipo} {self.cantidad}"

    class Meta:
        verbose_name = "Movimiento de Producto"
        verbose_name_plural = "Movimientos de Productos"


# ==========================================================
# 7. SEÑAL PARA CREAR DETALLE PRODUCTO AUTOMÁTICAMENTE
# ==========================================================
@receiver(post_save, sender=Producto)
def crear_detalle_producto(sender, instance, created, **kwargs):
    if created:
        detalle_obj, creado = DetalleProducto.objects.get_or_create(
            codigo_producto=instance,
            defaults={
                "cantidad_actual": 0,
                "stock_min": 0,
                "stock_max": 0,
            }
        )
        if not instance.codigo_detalle_producto_id:
            Producto.objects.filter(pk=instance.pk).update(
                codigo_detalle_producto=detalle_obj
            )


# ==========================================================
# 8. PROMOCIÓN
# ==========================================================
class Promocion(models.Model):
    codigo = models.AutoField(primary_key=True)
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Porcentaje de Descuento"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    imagen = models.ImageField(
        upload_to="promociones/",
        blank=True,
        null=True,
        verbose_name="Imagen"
    )
    estado = models.BooleanField(
        default=True,
        verbose_name="Estado"
    )
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promociones_directas",
        verbose_name="Producto Asociado"
    )
    codigo_servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promociones",
        verbose_name="Servicio Asociado"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"


# ==========================================================
# 9. PROMOCIÓN PRODUCTO
# ==========================================================
class PromocionProducto(models.Model):
    codigo = models.AutoField(primary_key=True)
    codigo_promocion = models.ForeignKey(
        Promocion,
        on_delete=models.CASCADE,
        related_name="productos_promocion",
        verbose_name="Promoción"
    )
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="promociones",
        verbose_name="Producto"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio"
    )
    estado = models.BooleanField(
        default=True,
        verbose_name="Estado"
    )
    valor_con_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor con Descuento"
    )

    def __str__(self):
        return f"{self.codigo_producto.nombre} - {self.codigo_promocion.nombre}"

    class Meta:
        verbose_name = "Promoción de Producto"
        verbose_name_plural = "Promociones de Productos"