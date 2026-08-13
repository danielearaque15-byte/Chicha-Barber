from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Usuario, Notificacion


# ==========================================================
# 1. CATEGORÍA
# ==========================================================
class Categoria(models.Model):

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
# 3. PRODUCTO
# ==========================================================
class Producto(models.Model):

    codigo_producto = models.AutoField(
        primary_key=True
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True
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

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=False,
        verbose_name="Categoría"
    )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.codigo:

            self.codigo = f"PROD-{self.codigo_producto:05d}"

            super().save(
                update_fields=["codigo"]
            )

    @property
    def stock_actual(self):

        if hasattr(self, "bitacora") and self.bitacora:
            return self.bitacora.cantidad

        return 0

    @classmethod
    def total_productos(cls):
        return cls.objects.count()

    @classmethod
    def total_activos(cls):
        return cls.objects.filter(
            estado=True
        ).count()

    @classmethod
    def total_inactivos(cls):
        return cls.objects.filter(
            estado=False
        ).count()

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ==========================================================
# 4. BITÁCORA / INVENTARIO
# ==========================================================
class bitacora(models.Model):

    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name="bitacora"
    )

    cantidad = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad en bitácora"
    )

    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio de Venta"
    )

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras",
        verbose_name="Proveedor"
    )

    def __str__(self):

        nombre_producto = (
            self.producto.nombre
            if self.producto
            else "Sin producto"
        )

        return (
            f"{nombre_producto} - "
            f"Bitácora: {self.cantidad} | "
            f"Venta: ${self.precio_venta}"
        )


# ==========================================================
# 5. MOVIMIENTO DE INVENTARIO
# ==========================================================
class MovimientoInventario(models.Model):

    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="movimientos",
        verbose_name="Producto"
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de movimiento"
    )

    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad"
    )

    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha"
    )

    motivo = models.CharField(
        max_length=200,
        verbose_name="Motivo"
    )

    def __str__(self):

        return (
            f"{self.producto.codigo} - "
            f"{self.tipo} {self.cantidad}"
        )


# ==========================================================
# 6. CREAR BITÁCORA AUTOMÁTICAMENTE
# ==========================================================
@receiver(post_save, sender=Producto)
def crear_bitacora(sender, instance, created, **kwargs):

    if created:

        bitacora.objects.get_or_create(
            producto=instance,
            defaults={
                "cantidad": 0,
                "precio_venta": 0,
            }
        )


# ==========================================================
# 7. VENTA
#
# MER:
#
# venta
# -------------------------
# codigo_venta
# codigo_usuario (FK)
# total_compra
# fecha
# ==========================================================
class venta(models.Model):

    METODO_PAGO_CHOICES = [
        ("persona", "Pago en persona"),
        ("contraentrega", "Pago contraentrega"),
        ("transferencia", "Transferencia Bancaria"),
    ]

    ESTADO_PAGO_CHOICES = [
        (
            "pendiente_verificacion",
            "Pendiente de Verificación"
        ),
        (
            "completado",
            "Completado"
        ),
        (
            "cancelado",
            "Cancelado"
        ),
    ]

    # ------------------------------------------
    # codigo_venta
    # ------------------------------------------
    codigo_venta = models.AutoField(
        primary_key=True
    )

    # ------------------------------------------
    # codigo_usuario (FK)
    # ------------------------------------------
    codigo_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        verbose_name="Usuario"
    )

    # ------------------------------------------
    # Datos adicionales del cliente
    # ------------------------------------------
    nombre_cliente = models.CharField(
        max_length=100,
        verbose_name="Nombre del Cliente"
    )

    correo = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo Electrónico"
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )

    direccion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )

    # ------------------------------------------
    # Información del pago
    # ------------------------------------------
    metodo_pago = models.CharField(
        max_length=50,
        choices=METODO_PAGO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Método de Pago"
    )

    estado_pago = models.CharField(
        max_length=30,
        choices=ESTADO_PAGO_CHOICES,
        default="completado",
        verbose_name="Estado del Pago"
    )

    comprobante = models.FileField(
        upload_to="comprobantes/",
        null=True,
        blank=True,
        verbose_name="Comprobante"
    )

    # ------------------------------------------
    # total_compra
    # ------------------------------------------
    total_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total de Compra"
    )

    # ------------------------------------------
    # fecha
    # ------------------------------------------
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha"
    )

    def actualizar_total(self):

        self.total_compra = sum(
            detalle.subtotal
            for detalle in self.detalles.all()
        )

        self.save(
            update_fields=["total_compra"]
        )

    def __str__(self):

        return (
            f"Venta #{self.codigo_venta} - "
            f"{self.nombre_cliente}"
        )


# ==========================================================
# 8. DETALLE DE VENTA
#
# MER:
#
# detalle_venta
# -------------------------
# codigo_detalle
# codigo_venta (FK)
# codigo_factura (FK)
# codigo_producto (FK)
# codigo_movimiento_producto (FK)
# cantidad
# valor_descuento
# subtotal
# ==========================================================
class detalleventa(models.Model):

    # ------------------------------------------
    # codigo_detalle
    # ------------------------------------------
    codigo_detalle = models.AutoField(
        primary_key=True
    )

    # ------------------------------------------
    # codigo_venta (FK)
    # ------------------------------------------
    codigo_venta = models.ForeignKey(
        venta,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Venta"
    )

    # ------------------------------------------
    # codigo_factura (FK)
    # ------------------------------------------
    codigo_factura = models.ForeignKey(
        "facturas.Factura",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_venta",
        verbose_name="Factura"
    )

    # ------------------------------------------
    # codigo_producto (FK)
    # ------------------------------------------
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="detalles_venta",
        verbose_name="Producto"
    )

    # ------------------------------------------
    # codigo_movimiento_producto (FK)
    # ------------------------------------------
    codigo_movimiento_producto = models.ForeignKey(
        MovimientoInventario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_venta",
        verbose_name="Movimiento de Inventario"
    )

    # ------------------------------------------
    # cantidad
    # ------------------------------------------
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad"
    )

    # ------------------------------------------
    # valor_descuento
    # ------------------------------------------
    valor_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor del Descuento"
    )

    # ------------------------------------------
    # subtotal
    # ------------------------------------------
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0,
        verbose_name="Subtotal"
    )

    def save(self, *args, **kwargs):

        stock = self.codigo_producto.bitacora

        # ------------------------------------------
        # Calcular subtotal
        # ------------------------------------------
        subtotal = (
            self.cantidad *
            stock.precio_venta
        )

        # Aplicar descuento
        subtotal -= self.valor_descuento

        # Evitar valores negativos
        if subtotal < 0:
            subtotal = 0

        self.subtotal = subtotal

        # ------------------------------------------
        # Validar stock al crear
        # ------------------------------------------
        if not self.pk:

            if self.cantidad > stock.cantidad:

                raise ValueError(
                    f"Stock insuficiente para "
                    f"'{self.codigo_producto.nombre}'. "
                    f"Disponible: {stock.cantidad}"
                )

        # ------------------------------------------
        # Guardar detalle
        # ------------------------------------------
        super().save(*args, **kwargs)

        # ------------------------------------------
        # Crear movimiento de inventario
        # ------------------------------------------
        if not self.codigo_movimiento_producto:

            movimiento = MovimientoInventario.objects.create(
                producto=self.codigo_producto,
                tipo="salida",
                cantidad=self.cantidad,
                motivo=(
                    f"Venta Online #"
                    f"{self.codigo_venta.codigo_venta}"
                )
            )

            self.codigo_movimiento_producto = movimiento

            super().save(
                update_fields=[
                    "codigo_movimiento_producto"
                ]
            )

            # --------------------------------------
            # Descontar bitácora
            # --------------------------------------
            stock.cantidad -= self.cantidad

            stock.save(
                update_fields=["cantidad"]
            )

    def __str__(self):

        return (
            f"{self.codigo_producto.codigo} "
            f"x {self.cantidad}"
        )


# ==========================================================
# 9. DATOS DE TRANSFERENCIA
# ==========================================================
class DatosTransferencia(models.Model):

    banco = models.CharField(
        max_length=100,
        default="Banco por definir"
    )

    tipo_cuenta = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    numero_cuenta = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    titular = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    @classmethod
    def get_solo(cls):

        obj, created = cls.objects.get_or_create(
            pk=1
        )

        return obj

    def __str__(self):

        return (
            f"Datos de Transferencia - "
            f"{self.banco}"
        )


# ==========================================================
# 10. NOTIFICACIÓN DE VENTA
# ==========================================================
@receiver(post_save, sender=venta)
def notificar_venta(
    sender,
    instance,
    created,
    **kwargs
):

    if not created:
        return

    # ------------------------------------------
    # Notificación al cliente
    # ------------------------------------------
    if instance.codigo_usuario:

        Notificacion.objects.create(
            usuario=instance.codigo_usuario,
            tipo="venta",
            mensaje=(
                f"Tu venta #{instance.codigo_venta} "
                f"fue registrada con éxito."
            ),
            url="/perfil/"
        )

    # ------------------------------------------
    # Notificación a administradores
    # ------------------------------------------
    admins = Usuario.objects.filter(
        rol="admin"
    )

    for admin in admins:

        Notificacion.objects.create(
            usuario=admin,
            tipo="venta",
            mensaje=(
                f"Nueva venta de "
                f"{instance.nombre_cliente} "
                f"por ${instance.total_compra:.0f}."
            ),
            url="/admin-comprobantes/"
        )