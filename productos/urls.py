from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # 🟢 CLIENTE
    # =========================
    path('', views.productos_galeria, name='productos_galeria'),
    path('carrito/', views.carrito, name='carrito'),
    path('pago/', views.pago, name='pago'),
    path('procesar_pago_cliente/', views.procesar_pago_cliente, name='procesar_venta'),
    # =========================
    # 🔵 ADMIN PRODUCTOS
    # =========================
    path('gestion/', views.lista_productos_admin, name='lista_productos_admin'),
    path('producto/crear/', views.crear_producto, name='crear_producto'),  # 👈 NUEVO
    path('producto/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('producto/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('configuracion/datos-banco/', views.ver_datos_banco, name='ver_datos_banco'), # Para ver los datos
    path('configuracion/datos-banco/editar/', views.editar_datos_banco, name='editar_datos_banco'), # Para editar los datos
    
    # =========================
    # 🟣 CATEGORÍAS
    path('categoria/crear/',views.crear_categoria,name='crear_categoria'),
    path('categorias/',views.lista_categorias,name='lista_categorias'),
    path('categoria/editar/<int:id>/',  views.editar_categoria, name='editar_categoria'),
    path('categoria/eliminar/<int:id>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # =========================
   # 🟣 PROVEEDORES
    # =========================

   path( 'proveedores/',  views.lista_proveedores, name='lista_proveedores'),
   path('proveedor/crear/',views.crear_proveedor,name='crear_proveedor'),
   path('proveedor/editar/<int:id>/', views.editar_proveedor,name='editar_proveedor'),
   path('proveedor/eliminar/<int:id>/',views.eliminar_proveedor,name='eliminar_proveedor'),
 
    # =========================
    # 🔥 bitacora
    # =========================
    path('bitacora/', views.lista_bitacora, name='lista_bitacora'),
    path('bitacora/editar/<int:pk>/', views.editar_bitacora, name='editar_bitacora'),

    path('existencias/',views.lista_existencias, name='lista_existencias'),
    path('existencias/editar/<int:pk>/',views.editar_existencias,name='editar_existencias'),
    path('movimientos-existencias/',views.lista_movimientos_existencias,name='lista_movimientos_existencias'),
    path('movimientos-existencias/registrar/',views.registrar_movimiento_existencias,name='registrar_movimiento_existencias'),
    path('movimientos-existencias/eliminar/<int:pk>/',views.eliminar_movimiento_existencias,name='eliminar_movimiento_existencias' ), 


    path('adquisiciones/',views.lista_adquisiciones,name='lista_adquisiciones'),
    path('adquisicion/crear/',views.registrar_adquisicion,name='registrar_adquisicion'),
    path('adquisicion/editar/<int:pk>/',views.editar_adquisicion,name='editar_adquisicion'),
    path('adquisicion/eliminar/<int:pk>/',views.eliminar_adquisicion,name='eliminar_adquisicion'),
    # =========================
    # 🟡 ventaS
    # =========================
    path('registrar-venta/', views.registrar_venta, name='registrar_venta'),
    path('historial/registrar/', views.registrar_venta, name='registrar_venta'),  # ← nueva
    path('historial/', views.historial_ventas, name='historial_ventas'),
    path('historial/<int:pk>/', views.detalle_venta, name='detalle_venta'),
    path('historial/eliminar/<int:pk>/', views.eliminar_venta, name='eliminar_venta'),
    
    
  
     # =========================
     # 🟡 marcas
     # =========================
    path('marcas/', views.lista_marcas, name='lista_marcas'),
    path('marca/crear/', views.crear_marca, name='crear_marca'),
    path('marcas/editar/<int:id>/', views.editar_marca, name='editar_marca'),
    path('marcas/eliminar/<int:id>/', views.eliminar_marca, name='eliminar_marca'),

] 