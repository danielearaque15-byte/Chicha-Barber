from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Usuario, Notificacion
from catalogo.models import Producto, MovimientoProducto


# ==========================================================
# 1. VENTA (Cabecera)
# ==========================================================
class Venta(models.Model):
    METODO_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta de Crédito / Débito"),
        ("transferencia", "Transferencia Directa"),
    ]

    ESTADO_PAGO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("completado", "Completado"),
        ("cancelado", "Cancelado"),
    ]

    codigo_venta = models.AutoField(primary_key=True)
    codigo_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        verbose_name="Usuario / Cliente"
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
        verbose_name="Dirección de Entrega"
    )
    metodo_pago = models.CharField(
        max_length=50,
        choices=METODO_PAGO_CHOICES,
        default="efectivo",
        verbose_name="Método de Pago"
    )
    estado_pago = models.CharField(
        max_length=30,
        choices=ESTADO_PAGO_CHOICES,
        default="completado",
        verbose_name="Estado del Pago"
    )
    total_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total de Venta"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha"
    )

    def actualizar_total(self):
        self.total_compra = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save(update_fields=["total_compra"])

    def __str__(self):
        return f"Venta #{self.codigo_venta} - {self.nombre_cliente}"

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"


# ==========================================================
# 2. DETALLE DE VENTA
# ==========================================================
class DetalleVenta(models.Model):
    codigo_detalle = models.AutoField(primary_key=True)
    codigo_venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Venta"
    )
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_venta",
        verbose_name="Producto"
    )
    codigo_movimiento_producto = models.ForeignKey(
        MovimientoProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_venta",
        verbose_name="Movimiento de Producto"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
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
        # 1. Obtener la referencia a DetalleProducto
        try:
            detalle_prod_obj = self.codigo_producto.detalle_producto
        except Exception:
            raise ValueError(f"El producto '{self.codigo_producto.nombre}' no tiene detalle ni stock registrado.")

        # 2. Validar disponibilidad al crear
        if not self.pk:
            if self.cantidad > detalle_prod_obj.cantidad_actual:
                raise ValueError(
                    f"Stock insuficiente para '{self.codigo_producto.nombre}'. "
                    f"Disponible: {detalle_prod_obj.cantidad_actual}"
                )

        # 3. Obtener precio y calcular subtotal
        precio_venta = self.codigo_producto.precio_venta_actual
        subtotal_calculado = (self.cantidad * precio_venta) - self.valor_descuento
        self.subtotal = max(subtotal_calculado, 0)

        super().save(*args, **kwargs)

        # 4. Crear Movimiento de Salida y descontar Stock
        if not self.codigo_movimiento_producto:
            movimiento = MovimientoProducto.objects.create(
                codigo_producto=self.codigo_producto,
                tipo="salida",
                cantidad=self.cantidad,
                observacion=f"Salida por Venta #{self.codigo_venta.codigo_venta}"
            )
            self.codigo_movimiento_producto = movimiento
            super().save(update_fields=["codigo_movimiento_producto"])

            # Descontar stock en DetalleProducto
            detalle_prod_obj.cantidad_actual -= self.cantidad
            detalle_prod_obj.save(update_fields=["cantidad_actual", "fecha_actualizacion"])

        # 5. Actualizar el total general de la Venta
        self.codigo_venta.actualizar_total()

    def __str__(self):
        return f"{self.codigo_producto.nombre} x {self.cantidad}"

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"


# ==========================================================
# 3. NOTIFICACIONES DE VENTA
# ==========================================================
@receiver(post_save, sender=Venta)
def notificar_venta(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.codigo_usuario:
        Notificacion.objects.create(
            usuario=instance.codigo_usuario,
            tipo="venta",
            mensaje=f"Tu compra #{instance.codigo_venta} fue registrada con éxito.",
            url="/perfil/"
        )

    admins = Usuario.objects.filter(rol="admin")
    for admin in admins:
        Notificacion.objects.create(
            usuario=admin,
            tipo="venta",
            mensaje=f"Nueva venta a {instance.nombre_cliente} por ${instance.total_compra:.2f}.",
            url="/ventas/"
        )