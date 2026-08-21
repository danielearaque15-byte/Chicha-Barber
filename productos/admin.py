from django.contrib import admin
from .models import (
    Producto, existencias, Bitacora, Movimientoexistencias,
    Adquisicion, Promocion, PromocionProducto, Categoria,
    Proveedor, venta, detalleventa, DatosTransferencia, Marca
)

admin.site.register(Producto)
admin.site.register(Marca)
admin.site.register(existencias)
admin.site.register(Bitacora)
admin.site.register(Movimientoexistencias)
admin.site.register(Adquisicion)
admin.site.register(Promocion)
admin.site.register(PromocionProducto)
admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(venta)
admin.site.register(detalleventa)
admin.site.register(DatosTransferencia)


