from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.shortcuts import render

from .models import Usuario, RegistroActividad, Notificacion, Rol
from .forms import (
    RegistroForm,
    CustomLoginForm,
    CrearUsuarioAdminForm,
    EditarUsuarioForm,
    EditarPerfilForm,
    RecuperarPasswordForm,
)

from core.utils import enviar_correo_recuperacion
from core.validators import validar_password_fuerte
from reservas.models import Reserva
from productos.models import venta
from facturas.models import Factura
from datetime import datetime, timedelta
import re

def inicio(request):

    context = {
        'titulo': 'Inicio',
        'usuario': request.user
    }

    return render(request,'index.html', context)


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido de nuevo, {user.first_name}!")
            if next_url:
                return redirect(next_url)
            return redirect('inicio')
        else:
            messages.error(request, "❌ Correo o contraseña incorrectos. Por favor, verifica los datos.")
    else:
        form = CustomLoginForm()
        
        context = {
            'form': form,
            'text': next_url,
            'titulo': 'Iniciar Sesión'
            }
        return render(request,'registration/login.html',context)

def registro_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # 🔥 CORRECCIÓN: Asignamos un tema por defecto para evitar el IntegrityError (NOT NULL)
            user.tema = 'light'
            # Corrección: rol ahora es FK, no string. Se asigna el objeto Rol correspondiente.
            user.rol = Rol.objects.get(tipo_rol='cliente')
            user.is_staff = False
            user.is_superuser = False
            user.save()

            # Inicio de sesión automático
            login(request, user)

            messages.success(
                request,
                "✅ ¡Usuario registrado con éxito! Tu sesión ha sido iniciada."
            )

            if next_url:
                return redirect(next_url)

            return redirect('inicio')
    else:
        form = RegistroForm()
        
    context = {
        'form': form,
        'next': next_url,
        'titulo': 'Registro'
    }
    return render(request, 'usuarios/registro.html', context)


def lista_usuarios(request):
    rol_filtro = request.GET.get('rol')

    if rol_filtro:
        # Corrección: rol es FK, se filtra por el campo relacionado tipo_rol
        usuarios = Usuario.objects.filter(rol__tipo_rol=rol_filtro)
    else:
        usuarios = Usuario.objects.all()

    usuarios = usuarios.order_by('first_name', 'last_name')

    context = {
        'usuarios': usuarios,

        'titulo': (
            rol_filtro.capitalize()
            if rol_filtro
            else 'Todos los Usuarios'
        ),

        'total_usuarios': Usuario.objects.count(),

        'total_clientes': Usuario.objects.filter(
            rol__tipo_rol='cliente'
        ).count(),

        'total_barberos': Usuario.objects.filter(
            rol__tipo_rol='barbero'
        ).count(),

        'total_admins': Usuario.objects.filter(
            rol__tipo_rol='admin'
        ).count(),

        'rol_filtro': rol_filtro,
    }

    return render(request, 'usuarios/lista_usuarios.html', context)


def crear_usuario_admin(request):
    if request.method == 'POST':
        form = CrearUsuarioAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.tema = 'light'
            # form.cleaned_data['rol'] ya es un objeto Rol (ModelChoiceField)
            user.rol = form.cleaned_data['rol']
            user.is_staff = form.cleaned_data.get('is_staff', False)
            user.is_superuser = False
            user.save()

            RegistroActividad.objects.create(
                usuario=request.user,
                tipo='usuario',
                # Corrección: get_rol_display() ya no existe (era de choices)
                descripcion=f'Creó el usuario "{user.get_full_name()}" con rol {user.rol.tipo_rol}'
            )

            messages.success(request, "✅ Usuario creado con éxito.")
            return redirect('lista_usuarios')
    else:
        form = CrearUsuarioAdminForm()

    context = {'form': form, 'titulo': 'Crear Usuario'}
    return render(request, 'usuarios/crear_usuario.html', context)


def cambiar_tema(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    user.tema = 'dark' if getattr(user, 'tema', 'light') == 'light' else 'light'
    user.save()
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))


def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            RegistroActividad.objects.create(
                usuario=request.user,
                tipo='usuario',
                descripcion=f'Editó el usuario "{usuario.get_full_name()}"'
            )
            messages.success(request, f"✅ Usuario {usuario.get_full_name()} actualizado con éxito.")
            return redirect('lista_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)

    context = {
        'form': form,
        'usuario': usuario,
        'titulo': 'Editar Usuario'
    }
    return render(request, 'usuarios/editar_usuario.html', context)

def recuperar_password_view(request):
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                usuario = Usuario.objects.get(email__iexact=email)
            except Usuario.DoesNotExist:
                messages.error(request, "❌ No existe una cuenta registrada con ese correo.")
                context = {
                    'form': form,
                    'titulo': 'Recuperar Contraseña'
                }
                return render(request, 'registration/recuperar.html', context)

            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            reset_url = request.build_absolute_uri(
                f'/recuperar/{uid}/{token}/'
            )

            try:
                enviar_correo_recuperacion(
                    correo_cliente=usuario.email,
                    nombre=usuario.first_name,
                    reset_url=reset_url
                )
            except Exception:
                messages.error(
                    request,
                    "❌ No se pudo enviar el correo de recuperación. Intenta nuevamente."
                )
                context = {
                    'form': form,
                    'titulo': 'Recuperar Contraseña'
                }
                return render(request, 'registration/recuperar.html', context)

            return redirect('password_reset_done')
        else:
            context = {
                'form': form,
                'titulo': 'Recuperar Contraseña'
            }
            return render(request, 'registration/recuperar.html', context)
    else:
        form = RecuperarPasswordForm()
        context = {
            'form': form,
            'titulo': 'Recuperar Contraseña'
        }
        return render(request, 'registration/recuperar.html', context)
    

@login_required
def perfil(request):
    form = EditarPerfilForm(instance=request.user)  # valor por defecto (GET)

    if request.method == 'POST':
        if 'editar_perfil' in request.POST:
            form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                RegistroActividad.objects.create(
                    usuario=request.user,
                    tipo='usuario',
                    descripcion='Actualizó su perfil'
                )
                messages.success(request, "✅ Perfil actualizado con éxito.")
                return redirect('perfil')
            else:
                messages.error(request, "❌ Revisa los datos del formulario, hay errores.")

        elif 'cambiar_password' in request.POST:
            actual = request.POST.get('password_actual', '')
            nueva = request.POST.get('password_nueva', '')
            confirmar = request.POST.get('password_confirmar', '')

            if not request.user.check_password(actual):
                messages.error(request, "❌ La contraseña actual es incorrecta.")
            elif nueva != confirmar:
                messages.error(request, "❌ Las contraseñas nuevas no coinciden.")
            else:
                try:
                    validar_password_fuerte(nueva)
                    request.user.set_password(nueva)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    RegistroActividad.objects.create(
                        usuario=request.user,
                        tipo='sesion',
                        descripcion='Cambió su contraseña'
                    )
                    messages.success(request, "✅ Contraseña actualizada. Inicia sesión de nuevo.")
                    return redirect('perfil')
                except ValidationError as e:
                    for error in e.messages:
                        messages.error(request, f"❌ {error}")

    reservas = Reserva.objects.filter(cliente=request.user).order_by('-fecha_reserva')
    ventas = venta.objects.filter(correo=request.user.email).order_by('-fecha')
    facturas = Factura.objects.filter(cliente=request.user).order_by('-fecha_emision')

    context = {
        'form': form,
        'reservas': reservas,
        'ventas': ventas,
        'facturas': facturas,
    }

    # Corrección: rol es FK, se compara contra el campo tipo_rol
    if request.user.rol.tipo_rol == 'admin':
        context['actividades'] = RegistroActividad.objects.all()[:20]

    return render(request, 'private/perfil.html', context)


@login_required
def marcar_notificaciones_leidas(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))

@login_required
def detalle_notificacion(request, pk):
    notificacion = get_object_or_404(Notificacion, pk=pk, usuario=request.user)

    if not notificacion.leida:
        notificacion.leida = True
        notificacion.save()

    match = re.search(r'#(\d+)', notificacion.mensaje)
    rel_id = match.group(1) if match else None

    # ---- ADMIN / BARBERO: va directo a la tabla correspondiente ----
    # Corrección: rol es FK, se compara contra tipo_rol
    if request.user.rol.tipo_rol in ('admin', 'barbero'):
        if notificacion.tipo == 'reserva':
            return redirect('ver_agenda')

        elif notificacion.tipo == 'venta':
            if rel_id:
                try:
                    venta.objects.get(pk=rel_id)
                    return redirect('detalle_venta', pk=rel_id)
                except venta.DoesNotExist:
                    pass
            return redirect('historial_ventas')

    # ---- CLIENTE: página de detalle bonita ----
    objeto_relacionado = None
    if rel_id:
        try:
            if notificacion.tipo == 'venta':
                objeto_relacionado = venta.objects.get(pk=rel_id, correo=request.user.email)
            elif notificacion.tipo == 'reserva':
                objeto_relacionado = Reserva.objects.get(pk=rel_id, cliente=request.user)
        except (venta.DoesNotExist, Reserva.DoesNotExist):
            objeto_relacionado = None

    context = {
        'notificacion': notificacion,
        'objeto_relacionado': objeto_relacionado,
        'titulo': 'Detalle de Notificación',
    }
    return render(request, 'private/detalle_notificacion.html', context)