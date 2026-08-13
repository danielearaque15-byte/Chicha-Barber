from multiprocessing import context
from django.contrib import messages  # type: ignore


from django.shortcuts import render,redirect, get_object_or_404 # type: ignore
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


from servicios.forms import ServiciosEditarForm, ServiciosForm, PromocionForm
from servicios.models import Promocion
from usuarios.forms import CustomLoginForm

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = CustomLoginForm
    
    def get_success_url(self):
        url = self.get_redirect_url()
        if url:
            return url
        # Redirigir al panel si es administrador, de lo contrario al inicio
        if self.request.user.rol == 'admin':
            return reverse_lazy('inicio_admin')
        return reverse_lazy('inicio')

from configuraciones.models import Carrusel

from servicios.models import Calificacion

def inicio(request):
    carruseles = Carrusel.objects.filter(estado=True).order_by('-fecha_modificacion')[:4]
    testimonios = Calificacion.objects.filter(puntuacion=5, mostrar_en_inicio=True).order_by('-fecha_calificacion')[:6]
    nombre = "Santiago"
    context = {
        'nombre': nombre,
        'carruseles': carruseles,
        'testimonios': testimonios,
    }
    return render(request, 'index-clientes.html', context)

def inicio_admin(request):
    if not request.user.is_authenticated or request.user.rol not in ['admin', 'barbero']:
        return redirect('login')
        
    from usuarios.models import Usuario
    from servicios.models import Servicios
    from reservas.models import Reserva
    from productos.models import Producto, Inventario
    from facturas.models import Factura
    from django.db.models import Sum

    # Estadísticas
    total_clientes = Usuario.objects.filter(rol='cliente').count()
    total_barberos = Usuario.objects.filter(rol='barbero').count()
    total_servicios = Servicios.objects.count()
    total_productos = Producto.objects.count()
    total_reservas = Reserva.objects.exclude(estado='cancelada').count()
    reservas_pendientes = Reserva.objects.filter(estado='reservada').count()
    total_ingresos = Factura.objects.filter(estado='pagada').aggregate(total=Sum('total_pagado'))['total'] or 0
    total_facturas = Factura.objects.count()

    # Listas
    reservas_recientes = Reserva.objects.all().order_by('-id')[:5]
    facturas_recientes = Factura.objects.all().order_by('-fecha_emision')[:5]
    productos_bajo_bitacora = Inventario.objects.filter(cantidad_actual__lt=15).select_related('codigo_producto')[:5]

    context = {
        'nombre': request.user.first_name or request.user.username,
        'total_clientes': total_clientes,
        'total_barberos': total_barberos,
        'total_servicios': total_servicios,
        'total_productos': total_productos,
        'total_reservas': total_reservas,
        'reservas_pendientes': reservas_pendientes,
        'total_ingresos': total_ingresos,
        'total_facturas': total_facturas,
        'reservas_recientes': reservas_recientes,
        'facturas_recientes': facturas_recientes,
        'productos_bajo_bitacora': productos_bajo_bitacora,
    }
    return render(request, 'index-admin.html', context)


def crear_promocion(request):
    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES)
        if form.is_valid():
            promocion = form.save()
            messages.success(request, 'Promoción creada exitosamente.')
            return redirect('crear_promocion')
        else:
            messages.error(request, 'Error al crear la promoción. Por favor, inténtalo de nuevo.')
            
            
  
