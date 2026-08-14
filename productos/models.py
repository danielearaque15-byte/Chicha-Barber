from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Usuario, Notificacion


# ==========================================================
# 1. CATEGORÍA
# ==========================================================
class Categoria(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

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

    codigo = models.AutoField(
        primary_key=True
    )

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

    codigo_inventario = models.ForeignKey(
        "Inventario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="producto_principal",
        verbose_name="Inventario"
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

    # ------------------------------------------------------
    # IMPORTANTE:
    # Este campo se conserva para no romper datos existentes.
    # El precio de venta principal ahora se obtiene de
    # la última Adquisicion.
    # ------------------------------------------------------
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio"
    )

    codigo_categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Categoría"
    )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.codigo:

            self.codigo = (
                f"PROD-{self.codigo_producto:05d}"
            )

            super().save(
                update_fields=["codigo"]
            )

    @property
    def stock_actual(self):

        if self.codigo_inventario:

            return self.codigo_inventario.cantidad_actual

        try:

            return self.inventario.cantidad_actual

        except Inventario.DoesNotExist:

            return 0

    @property
    def precio_venta_actual(self):

        adquisicion = (
            self.adquisiciones
            .order_by("-fecha", "-codigo")
            .first()
        )

        if adquisicion:

            return adquisicion.precio_venta

        return 0

    @property
    def precio_compra_actual(self):

        adquisicion = (
            self.adquisiciones
            .order_by("-fecha", "-codigo")
            .first()
        )

        if adquisicion:

            return adquisicion.precio_compra

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

        return (
            f"{self.codigo} - "
            f"{self.nombre}"
        )


# ==========================================================
# 4. INVENTARIO
# ==========================================================
class Inventario(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

    codigo_producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name="inventario",
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

            return (
                f"{self.codigo_producto.nombre} - "
                f"Stock: {self.cantidad_actual}"
            )

        return (
            f"Inventario #{self.codigo}"
        )


# ==========================================================
# 5. BITÁCORA
# ==========================================================
class Bitacora(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

    codigo_inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name="bitacoras",
        verbose_name="Inventario"
    )

    codigo_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras_inventario",
        verbose_name="Usuario"
    )

    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="bitacoras",
        verbose_name="Producto"
    )

    fecha = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha"
    )

    hora = models.TimeField(
        auto_now_add=True,
        verbose_name="Hora"
    )

    tipo_cambio = models.CharField(
        max_length=50,
        verbose_name="Tipo de Cambio"
    )

    campo_actualizado = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Campo Actualizado"
    )

    valor_anterior = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Valor Anterior"
    )

    valor_actual = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Valor Actual"
    )

    motivo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Motivo"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def __str__(self):

        return (
            f"Bitácora #{self.codigo} - "
            f"{self.codigo_producto.nombre}"
        )


# ==========================================================
# 6. MOVIMIENTO DE INVENTARIO
# ==========================================================
class MovimientoInventario(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

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

    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad"
    )

    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha"
    )

    observacion = models.CharField(
        max_length=200,
        verbose_name="Observación"
    )

    def __str__(self):

        return (
            f"{self.codigo_producto.codigo} - "
            f"{self.tipo} "
            f"{self.cantidad}"
        )


# ==========================================================
# 7. ADQUISICIÓN
# ==========================================================
class Adquisicion(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

    codigo_proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="adquisiciones",
        verbose_name="Proveedor"
    )

    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="adquisiciones",
        verbose_name="Producto"
    )

    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad"
    )

    cantidad_venta = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de Venta"
    )

    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio de Compra"
    )

    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio de Venta"
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total"
    )

    fecha = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha"
    )

    def __str__(self):

        return (
            f"Adquisición #{self.codigo} - "
            f"{self.codigo_producto.nombre}"
        )


# ==========================================================
# 8. CREAR INVENTARIO AUTOMÁTICAMENTE
# ==========================================================
@receiver(post_save, sender=Producto)
def crear_inventario(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        inventario, creado = (
            Inventario.objects.get_or_create(
                codigo_producto=instance,
                defaults={
                    "cantidad_actual": 0,
                    "stock_min": 0,
                    "stock_max": 0,
                }
            )
        )

        if not instance.codigo_inventario_id:

            Producto.objects.filter(
                pk=instance.pk
            ).update(
                codigo_inventario=inventario
            )


# ==========================================================
# 9. PROMOCIÓN
# ==========================================================
class Promocion(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

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

    fecha_inicio = models.DateField(
        verbose_name="Fecha de Inicio"
    )

    fecha_fin = models.DateField(
        verbose_name="Fecha de Fin"
    )

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

    def __str__(self):

        return self.nombre


# ==========================================================
# 10. PROMOCIÓN PRODUCTO
# ==========================================================
class PromocionProducto(models.Model):

    codigo = models.AutoField(
        primary_key=True
    )

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

        return (
            f"{self.codigo_producto.nombre} - "
            f"{self.codigo_promocion.nombre}"
        )


# ==========================================================
# 11. VENTA
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

    codigo_venta = models.AutoField(
        primary_key=True
    )

    codigo_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        verbose_name="Usuario"
    )

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

    total_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total de Compra"
    )

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
# 12. DETALLE DE VENTA
# ==========================================================
class detalleventa(models.Model):

    codigo_detalle = models.AutoField(
        primary_key=True
    )

    codigo_venta = models.ForeignKey(
        venta,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Venta"
    )

    codigo_factura = models.ForeignKey(
        "facturas.Factura",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_venta",
        verbose_name="Factura"
    )

    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="detalles_venta",
        verbose_name="Producto"
    )

    codigo_movimiento_producto = models.ForeignKey(
        MovimientoInventario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_venta",
        verbose_name="Movimiento de Inventario"
    )

    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad"
    )

    valor_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor del Descuento"
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0,
        verbose_name="Subtotal"
    )

    def save(self, *args, **kwargs):

        # --------------------------------------------------
        # BUSCAR INVENTARIO
        # --------------------------------------------------
        try:

            inventario = self.codigo_producto.inventario

        except Inventario.DoesNotExist:

            raise ValueError(
                f"El producto "
                f"'{self.codigo_producto.nombre}' "
                f"no tiene inventario."
            )

        # --------------------------------------------------
        # BUSCAR ÚLTIMA ADQUISICIÓN
        # --------------------------------------------------
        adquisicion = (
            Adquisicion.objects
            .filter(
                codigo_producto=self.codigo_producto
            )
            .order_by(
                "-fecha",
                "-codigo"
            )
            .first()
        )

        # --------------------------------------------------
        # OBTENER PRECIO DE VENTA
        # --------------------------------------------------
        if adquisicion:

            precio_venta = (
                adquisicion.precio_venta
            )

        else:

            precio_venta = 0

        # --------------------------------------------------
        # CALCULAR SUBTOTAL
        # --------------------------------------------------
        subtotal = (
            self.cantidad *
            precio_venta
        )

        subtotal -= self.valor_descuento

        if subtotal < 0:

            subtotal = 0

        self.subtotal = subtotal

        # --------------------------------------------------
        # VALIDAR STOCK AL CREAR
        # --------------------------------------------------
        if not self.pk:

            if (
                self.cantidad >
                inventario.cantidad_actual
            ):

                raise ValueError(
                    f"Stock insuficiente para "
                    f"'{self.codigo_producto.nombre}'. "
                    f"Disponible: "
                    f"{inventario.cantidad_actual}"
                )

        # --------------------------------------------------
        # GUARDAR DETALLE
        # --------------------------------------------------
        super().save(*args, **kwargs)

        # --------------------------------------------------
        # CREAR MOVIMIENTO DE SALIDA
        # --------------------------------------------------
        if not self.codigo_movimiento_producto:

            movimiento = (
                MovimientoInventario.objects.create(
                    codigo_producto=self.codigo_producto,
                    tipo="salida",
                    cantidad=self.cantidad,
                    observacion=(
                        f"Venta Online #"
                        f"{self.codigo_venta.codigo_venta}"
                    )
                )
            )

            self.codigo_movimiento_producto = (
                movimiento
            )

            super().save(
                update_fields=[
                    "codigo_movimiento_producto"
                ]
            )

            # ----------------------------------------------
            # DESCONTAR INVENTARIO
            # ----------------------------------------------
            inventario.cantidad_actual -= (
                self.cantidad
            )

            inventario.save(
                update_fields=[
                    "cantidad_actual",
                    "fecha_actualizacion"
                ]
            )

    def __str__(self):

        return (
            f"{self.codigo_producto.codigo} "
            f"x {self.cantidad}"
        )


# ==========================================================
# 13. DATOS DE TRANSFERENCIA
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
# 14. NOTIFICACIÓN DE VENTA
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

    # ------------------------------------------------------
    # NOTIFICACIÓN AL CLIENTE
    # ------------------------------------------------------
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

    # ------------------------------------------------------
    # NOTIFICACIÓN A ADMINISTRADORES
    # ------------------------------------------------------
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