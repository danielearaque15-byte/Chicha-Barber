# facturas/models.py

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from usuarios.models import Usuario
from productos.models import Producto
from reservas.models import Reserva
from core.utils import renombrar_comprobante_factura

# ==========================================
# FACTURA
# ==========================================

class Factura(models.Model):

    METODOS_PAGO = (
        ('efectivo', 'Efectivo'),
        ('nequi', 'Nequi'),
        ('daviplata', 'Daviplata'),
        ('yape', 'Yape'),
        ('tarjeta', 'Tarjeta'),
    )

    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    )

    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name='facturas',
        null=True,
        blank=True
    )

    fecha_emision = models.DateTimeField(
        auto_now_add=True
    )

    total_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    class Meta:
        ordering = ['-fecha_emision']
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

    def __str__(self):
        return f"Factura #{self.id} - {self.cliente}"

    def actualizar_total(self):
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total_pagado = total
        self.save(update_fields=['total_pagado'])

    comprobante_pago = models.ImageField(
        upload_to=renombrar_comprobante_factura,
        null=True,
        blank=True,
        verbose_name="Comprobante de Pago"
    )

    imagen_transaccion = models.ImageField(
        upload_to='comprobantes_facturas/',
        null=True,
        blank=True,
        verbose_name="Imagen del Comprobante"
    )

    # El método __str__ ya estaba definido correctamente al inicio de la clase
    # y no hacía referencia a los campos problemáticos.
    # La segunda definición duplicada ha sido eliminada.


# ==========================================
# DETALLE FACTURA
# ==========================================

class DetalleFactura(models.Model):

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_factura'
    )

    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_factura'
    )

    cantidad = models.IntegerField(
        default=1
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False # Se vuelve automático
    )
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.producto and not self.reserva:
            raise ValidationError('Un detalle de factura debe estar asociado a un producto o a una reserva.')
        if self.producto and self.reserva:
            raise ValidationError('Un detalle de factura no puede estar asociado a un producto y a una reserva simultáneamente.')

    def save(self, *args, **kwargs):
        # El subtotal se calcula de forma dinámica antes de ir a la BD
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

        # Si el detalle está asociado a una reserva, se actualiza el estado de la reserva
        if self.reserva and self.reserva.estado != 'confirmada':
            self.reserva.estado = 'confirmada'
            self.reserva.save(update_fields=['estado'])

    def __str__(self):
        return f"Detalle Factura #{self.factura.id}"


# ==========================================
# 🔥 SIGNALS PARA ACTUALIZAR FACTURA MÁSTER
# ==========================================

@receiver(post_save, sender=DetalleFactura)
@receiver(post_delete, sender=DetalleFactura)
def recalcular_factura_al_cambiar_detalles(sender, instance, **kwargs):
    """Cada vez que agregues o borres un servicio/producto, el total se actualizará."""
    if instance.factura:
        instance.factura.actualizar_total()