from multiprocessing import context

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages # type: ignore
from django.core.mail import send_mail

from usuarios.forms import RegistroForm
from usuarios.models import Usuario, Rol
from .models import Servicios, Promocion, Calificacion
from .forms import PromocionEditarForm, PromocionForm, ServiciosForm, ServiciosEditarForm, calificacionForm, ResponderCalificacionForm

def servicios(request):
    servicios = Servicios.objects.all()
    context = {
        'titulo': 'Nuestros Servicios',
        'servicios': servicios 
    }
    return render(request, 'servicios/servicios.html', context)

def registro(request, servicio_pk):
    servicio = get_object_or_404(Servicios, pk=servicio_pk)

    # Si el usuario ya está autenticado, lo enviamos directo a la reserva
    if request.user.is_authenticated:
        return redirect('crear_reserva', servicio_id=servicio.pk)

    # Capturamos la URL de destino original (si existe)
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Corrección: rol ahora es FK, no string
            user.rol = Rol.objects.get(tipo_rol='cliente')

            # Seguridad extra
            user.is_staff = False
            user.is_superuser = False

            user.save()

            messages.success(
                request,
                "✅ Usuario registrado como cliente con éxito."
            )
            
            # Si no hay un destino explícito, lo mandamos a la reserva del servicio actual
            if not next_url:
                next_url = reverse('crear_reserva', args=[servicio.pk])

            return redirect(f"{reverse('login')}?next={next_url}")
        
    else:
        form = RegistroForm()
        
    context = {
        'titulo': f'Registro para {servicio.nombre}',
        'servicio': servicio,
        'form': form,
        'next': next_url # Pasamos 'next' al contexto para el template
    }
    return render(request, 'usuarios/registro.html', context)


def login(request):
    context = {
        'titulo': 'Iniciar Sesión'
    }
    return render(request, 'login/reservas.html', context)

@login_required
def crear_servicios(request):
    if not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado. Solo administradores.")
        return redirect('listado-admin')

    if request.method == 'POST':
        form = ServiciosForm(request.POST, request.FILES)
        if form.is_valid():
            # Limpiamos lógica innecesaria y guardamos directamente
            form.save()
            messages.success(request, "Servicio creado con éxito.")
            return redirect('listado-admin') 
        else:
            messages.error(request, "Error al crear el servicio. Revisa los campos.")
    else:
        form = ServiciosForm()
    
    return render(request, 'servicios/agregar_servicios.html', {
        'form': form,
        'titulo': 'Crear Nuevo Servicio'
    })
def promocion(request):
    promociones = Promocion.objects.all()
    context = {
        'titulo': 'Promociones',
        'promociones': promociones
    }
    return render(request, 'servicios/promocion.html', context)

def listado_admin(request):
    servicios = Servicios.objects.all()
    activos = Servicios.objects.filter(estado=True).count()
    inactivos = Servicios.objects.filter(estado=False).count()
    context = {
        'titulo': 'Listado de Servicios',
        'servicios': servicios,
        'total_servicios': servicios.count(),
        'activos': activos,
        'inactivos': inactivos,
    }
    return render(request, 'servicios/listado-admin.html', context)

def listado_promocion(request):
    promociones = Promocion.objects.all()
    context = {
        'titulo': 'Listado de Promociones',
        'promociones': promociones,
        'total_promociones': promociones.count(),
        'activas': promociones.filter(estado=True).count(),
        'inactivas': promociones.filter(estado=False).count(),
    }
    return render(request, 'servicios/listado-promocion.html', context)

@login_required
def editar_servicios(request, pk):
    if not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado.")
        return redirect('listado-admin')

    servicio = get_object_or_404(Servicios, pk=pk)
    if request.method == 'POST':
        # ERROR CORREGIDO: se debe usar 'servicio' (el objeto), no 'servicios' (la clase/modelo)
        form = ServiciosEditarForm(request.POST, request.FILES, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, f"Servicio {servicio.nombre} actualizado.")
            return redirect('listado-admin')
    else:
        form = ServiciosEditarForm(instance=servicio)
    context = {
        'form': form,
        'servicio': servicio
        }

    return render(request, 'servicios/editar_servicios.html', context)

@login_required
def eliminar_servicios(request, pk):
    if not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado.")
        return redirect('listado-admin')

    servicio = get_object_or_404(Servicios, pk=pk)
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'Servicio eliminado.')
        return redirect('listado-admin')
    context = {
        'servicio': servicio
    }
    return render(request, 'servicios/eliminar_servicios.html', context)

@login_required
def crear_promocion(request):
    if not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado.")
        return redirect('listado-promocion')

    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES)
        if form.is_valid():
            # ERROR CORREGIDO: No uses "Promocion = ..." porque borras la clase del Modelo
            nueva_promo = form.save() 
            messages.success(request, "Promoción creada exitosamente.")
            return redirect('listado-promocion')
        else:
            messages.error(request, "Error al crear la promoción.")
    else:
        form = PromocionForm()
    
    return render(request, 'servicios/agregar_promocion.html', {
        'form': form,
        'titulo': 'Crear Nueva Promoción'
    })

@login_required
def editar_promocion(request, pk):
    if not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado.")
        return redirect('listado-promocion')

    promocion = get_object_or_404(Promocion, pk=pk)
    if request.method == 'POST':
        form = PromocionEditarForm(request.POST, request.FILES, instance=promocion)
        if form.is_valid():
            form.save()
            messages.success(request, f"Promoción {promocion.nombre} actualizada.")
            return redirect('listado-promocion')
    else:
        # ERROR CORREGIDO: Aquí usabas PromocionForm en lugar de Editar si correspondía
        form = PromocionEditarForm(instance=promocion)

    return render(request, 'servicios/editar_promocion.html', {'form': form, 'promocion': promocion})

@login_required
def eliminar_promocion(request, pk):
    if not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado.")
        return redirect('listado-promocion')

    promocion = get_object_or_404(Promocion, pk=pk)
    if request.method == 'POST':
        promocion.delete()
        messages.success(request, 'Promoción eliminada.')
        return redirect('listado-promocion')
    return render(request, 'servicios/eliminar_promocion.html', {'promocion': promocion})

def calificacion_view(request):
    calificaciones = Calificacion.objects.all()
    context = {
        'titulo': 'Califica Nuestros Servicios',
        'calificaciones': calificaciones
    }
    return render(request, 'servicios/calificacion.html', context)

def listado_calificacion(request):
    calificaciones = Calificacion.objects.all()
    context = {
        'titulo': 'Listado de Calificaciones',
        'calificaciones': calificaciones,
        'total_calificaciones': calificaciones.count(),
        'titulo': 'Listado de Calificaciones'
        
        
    }
    return render(request, 'servicios/listado-calificacion.html', context)

def responder_calificacion(request, pk):
    # Seguridad: Solo administradores
    if not request.user.is_authenticated or not (request.user.is_staff or getattr(getattr(request.user, 'rol', None), 'tipo_rol', None) == 'admin'):
        messages.error(request, "Acceso denegado. Solo los administradores pueden responder calificaciones.")
        return redirect('listado-calificacion')

    calificacion = get_object_or_404(Calificacion, pk=pk)
    form = ResponderCalificacionForm(request.POST or None)

    # Corrección: cliente ahora es FK directa a Usuario (o None si no se pudo enlazar).
    # Ya no hace falta buscar por nombre.
    nombre_cliente = calificacion.cliente.get_full_name() if calificacion.cliente else calificacion.cliente_nombre
    correo_destino = calificacion.cliente.email if calificacion.cliente else None

    if request.method == 'POST':
        if form.is_valid():
            texto_respuesta = form.cleaned_data['respuesta']

            if correo_destino:
                asunto = "Respuesta a tu calificación - ChichaBarber"
                cuerpo = f"Hola {nombre_cliente},\n\nEl administrador respondió: {texto_respuesta}"
                try:
                    send_mail(
                        asunto, cuerpo, 'chichabarber39@gmail.com',
                        [correo_destino], fail_silently=False
                    )
                    messages.success(request, f"Respuesta enviada a {correo_destino}")
                except Exception as e:
                    messages.error(request, f"Error al enviar correo: {e}")
            else:
                messages.warning(request, "Se procesó la respuesta, pero no se encontró un correo para este cliente.")
            
            return redirect('listado-calificacion')
            
    else:
        form = ResponderCalificacionForm()
    
    context = {
        'form': form,
        'calificacion': calificacion,
        'titulo': f'Responder a {nombre_cliente}'
    }
    return render(request, 'servicios/responder-calificacion.html', context)

def guardar_calificacion_view(request):
    if request.method == 'POST':
        form = calificacionForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)

            # Corrección: si el cliente tiene sesión iniciada, se enlaza
            # directamente a su cuenta; si no, solo queda el nombre de respaldo.
            if request.user.is_authenticated:
                calificacion.cliente = request.user
                if not calificacion.cliente_nombre:
                    calificacion.cliente_nombre = request.user.get_full_name() or request.user.username

            calificacion.save()
            messages.success(request, "✅ ¡Gracias por tu calificación!")
            return redirect('calificacion')
    return redirect('calificacion')

def eliminar_calificacion(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk)

    nombre_cliente = calificacion.cliente.get_full_name() if calificacion.cliente else calificacion.cliente_nombre

    if request.method == 'POST':
        calificacion.delete()
        messages.success(request, 'Calificación eliminada.')
        return redirect('listado-calificacion')
    
    context = {
        'calificacion': calificacion,
        'titulo': f'Eliminar calificación de {nombre_cliente}'
    }
    return render(request, 'servicios/eliminar_calificacion.html', context)