from django.urls import path
from . import views# =========================
    # 🟠 COMPRAS
    # =========================
    from django.urls import path

from catalogo import views


path('compras/', views.lista_compras, name='lista_compras'),
    path('compra/crear/', views.registrar_compra, name='registrar_compra'),
    path('compra/editar/<int:pk>/', views.editar_compra, name='editar_compra'),
    path('compra/eliminar/<int:pk>/', views.eliminar_compra, name='eliminar_compra'),
    path('compra/<int:pk>/detalle/', views.detalle_compra, name='detalle_compra'),