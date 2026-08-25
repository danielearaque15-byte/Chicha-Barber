from django.db import models
from usuarios.models import Usuario
from catalogo.models import Producto, MovimientoProducto


# ==========================================================
# 1. BITÁCORA DE ACTIVIDAD GENERAL
# ==========================================================
class Bitacora(models.Model):
    codigo = models.AutoField(primary_key=True)
    codigo_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras",
        verbose_name="Usuario"
    )
    accion = models.CharField(
        max_length=150,
        verbose_name="Acción Realizada"
    )
    modulo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Módulo/App"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción Detallada"
    )
    ip_origen = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="Dirección IP"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    )

    def __str__(self):
        usuario_str = self.codigo_usuario.username if self.codigo_usuario else "Sistema/Anonimo"
        return f"[{self.fecha.strftime('%Y-%m-%d %H:%M')}] {usuario_str} - {self.accion}"

    class Meta:
        verbose_name = "Bitácora"
        verbose_name_plural = "Bitácoras"
        ordering = ["-fecha"]


# ==========================================================
# 2. HISTORIAL AUDITADO DE STOCK
# ==========================================================
class HistorialStock(models.Model):
    codigo = models.AutoField(primary_key=True)
    codigo_producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="historiales_stock",
        verbose_name="Producto"
    )
    codigo_movimiento = models.ForeignKey(
        MovimientoProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historiales",
        verbose_name="Movimiento Asociado"
    )
    stock_anterior = models.PositiveIntegerField(
        verbose_name="Stock Anterior"
    )
    cantidad_cambio = models.IntegerField(
        verbose_name="Cantidad Modificada"
    )
    stock_nuevo = models.PositiveIntegerField(
        verbose_name="Stock Resultante"
    )
    motivo = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Motivo / Justificación"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    def __str__(self):
        return f"{self.codigo_producto.nombre}: {self.stock_anterior} -> {self.stock_nuevo}"

    class Meta:
        verbose_name = "Historial de Stock"
        verbose_name_plural = "Historiales de Stock"
        ordering = ["-fecha"]