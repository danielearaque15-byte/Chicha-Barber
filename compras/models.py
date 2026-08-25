from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Importamos las entidades necesarias desde la app 'catalogo'
from catalogo.models import Proveedor, Producto, MovimientoExistencias


# ==========================================================
# 1. COMPRA / ADQUISICIÓN (Cabecera)
# ==========================================================
class Compra(models.Model):
    codigo = models.AutoField(primary_key=True)
    codigo_proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="compras",
        verbose_name="Proveedor"
    )
    fecha = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Compra"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total de la Compra"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    def actualizar_total(self):
        """Calcula el total sumando el valor de todos sus detalles."""
        self.total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save(update_fields=["total"])

    def __str__(self):
        return f"Compra #{self.codigo} - {self.codigo_proveedor.nombre}"

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"


# ==========================================================
# 2. DETALLE DE COMPRA (Desglose por producto)
# ==========================================================
class DetalleCompra(models.Model):
    codigo = models.AutoField(primary_key=True)
    codigo_compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Compra"
    )
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="adquisiciones",
        verbose_name="Producto"
    )
    codigo_movimiento_producto = models.ForeignKey(
        MovimientoExistencias,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_compra",
        verbose_name="Movimiento de Existencia"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Comprada")
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio de Compra (Unitario)"
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio de Venta Sugerido"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0,
        verbose_name="Subtotal"
    )

    def save(self, *args, **kwargs):
        # 1. Calcular subtotal
        self.subtotal = self.cantidad * self.precio_compra
        es_nuevo = self.pk is None
        
        super().save(*args, **kwargs)

        # 2. Registrar movimiento de Entrada y actualizar Stock al crear
        if es_nuevo and not self.codigo_movimiento_producto:
            movimiento = MovimientoExistencias.objects.create(
                codigo_producto=self.codigo_producto,
                tipo="entrada",
                cantidad=self.cantidad,
                observacion=f"Entrada por Compra #{self.codigo_compra.codigo}"
            )
            self.codigo_movimiento_producto = movimiento
            super().save(update_fields=["codigo_movimiento_producto"])

            # Sumar al stock actual en la app catalogo
            try:
                existencia = self.codigo_producto.existencias
                existencia.cantidad_actual += self.cantidad
                existencia.save(update_fields=["cantidad_actual", "fecha_actualizacion"])
            except Exception:
                pass

        # 3. Recalcular el total general de la compra
        self.codigo_compra.actualizar_total()

    def __str__(self):
        return f"Detalle #{self.codigo} - {self.codigo_producto.nombre} x {self.cantidad}"

    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compras"
# Create your models here.
