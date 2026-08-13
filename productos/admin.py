from django.contrib import admin
from .models import (
    Producto, Inventario, Bitacora, MovimientoInventario,
    Adquisicion, Promocion, PromocionProducto, Categoria,
    Proveedor, venta, detalleventa, DatosTransferencia
)

admin.site.register(Producto)
admin.site.register(Inventario)
admin.site.register(Bitacora)
admin.site.register(MovimientoInventario)
admin.site.register(Adquisicion)
admin.site.register(Promocion)
admin.site.register(PromocionProducto)
admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(venta)
admin.site.register(detalleventa)
admin.site.register(DatosTransferencia)

