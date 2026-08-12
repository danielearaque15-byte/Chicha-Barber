from django.contrib import admin
from .models import Producto, bitacora, venta, detalleventa

admin.site.register(Producto)
admin.site.register(bitacora)
admin.site.register(venta)
admin.site.register(detalleventa)
# Register your models here.
