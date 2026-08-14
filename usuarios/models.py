from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.Model):
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    tipo_rol = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Tipo de rol"
    )

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.tipo_rol

from django.contrib.auth.models import AbstractUser, UserManager


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        if not extra_fields.get('rol'):
            rol_admin, _ = Rol.objects.get_or_create(tipo_rol='admin')
            extra_fields['rol'] = rol_admin
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)
    
class Usuario(AbstractUser):
    objects = UsuarioManager()
    # El documento será el 'username' interno de Django
    username = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Documento",
    )
    email = models.EmailField(unique=True)

    # segundo_nombre y segundo_apellido: AbstractUser solo trae
    # first_name y last_name, el MER pide 4 campos de nombre.
    segundo_nombre = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Segundo nombre"
    )
    segundo_apellido = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Segundo apellido"
    )

    telefono = models.CharField(max_length=15, verbose_name="Teléfono")

    # FK real a Rol (antes era CharField con choices)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name='usuarios',
        verbose_name='Rol'
    )

    estado = models.BooleanField(default=True, verbose_name='Estado')
    tema = models.CharField(
        max_length=10,
        default='dark',
        choices=[('light', 'Claro'), ('dark', 'Oscuro')]
    )

    # Campo específico para barberos
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    foto_perfil = models.ImageField(
        upload_to='usuarios/',
        blank=True,
        null=True,
        verbose_name='Foto de perfil'
    )

    # Configuración de Login: Entrarán con el EMAIL
    USERNAME_FIELD = 'email'
    # Campos que pide 'createsuperuser' (no incluyas EMAIL ni PASSWORD)
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.rol.tipo_rol})"

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class RegistroActividad(models.Model):
    TIPO_CHOICES = (
        ('usuario', 'Usuario'),
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
        ('reserva', 'Reserva'),
        ('promocion', 'Promoción'),
        ('sesion', 'Sesión'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='actividades',
        verbose_name='Usuario que realizó la acción'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de actividad'
        verbose_name_plural = 'Registros de actividad'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario} - {self.descripcion} ({self.fecha:%d/%m/%Y %H:%M})"


class Notificacion(models.Model):
    TIPO_CHOICES = (
        ('venta', 'venta'),
        ('reserva', 'Reserva'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Destinatario'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensaje = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True, null=True)
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario} - {self.mensaje}"