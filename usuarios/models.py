from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


# ---------------------------------------------------------------------------
# Choices reutilizables
# ---------------------------------------------------------------------------

class TipoDocumento(models.TextChoices):
    CC = 'CC', 'Cédula de ciudadanía'
    TI = 'TI', 'Tarjeta de identidad'
    CE = 'CE', 'Cédula de extranjería'
    PA = 'PA', 'Pasaporte'


class RolUsuario(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    BARBERO = 'barbero', 'Barbero'
    CLIENTE = 'cliente', 'Cliente'


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('rol', RolUsuario.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    objects = UsuarioManager()

    # --- Campos heredados de AbstractUser, re-declarados solo para
    #     traducir el nombre de columna en MySQL (db_column) ---
    password = models.CharField(
        max_length=128,
        verbose_name='Contraseña',
        db_column='contrasena'
    )
    last_login = models.DateTimeField(
        blank=True, null=True,
        verbose_name='Último acceso',
        db_column='ultimo_acceso'
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name='Es superusuario',
        db_column='es_superusuario'
    )
    first_name = models.CharField(
        max_length=150, blank=True,
        verbose_name='Primer nombre',
        db_column='primer_nombre'
    )
    last_name = models.CharField(
        max_length=150, blank=True,
        verbose_name='Primer apellido',
        db_column='primer_apellido'
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Es staff',
        db_column='es_staff'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        db_column='activo'
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación de la cuenta',
        db_column='fecha_creacion'
    )

    # El documento será el 'username' interno de Django
    username = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de documento',
        db_column='numero_documento'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Correo electrónico',
        db_column='correo_electronico'
    )

    # segundo_nombre y segundo_apellido: AbstractUser solo trae
    # first_name y last_name, el MER pide 4 campos de nombre.
    segundo_nombre = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Segundo nombre',
        db_column='segundo_nombre'
    )
    segundo_apellido = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Segundo apellido',
        db_column='segundo_apellido'
    )

    # --- Nuevo: tipo de documento ---
    tipo_documento = models.CharField(
        max_length=2,
        choices=TipoDocumento.choices,
        default=TipoDocumento.CC,
        verbose_name='Tipo de documento',
        db_column='tipo_documento'
    )

    telefono = models.CharField(
        max_length=15,
        verbose_name='Teléfono',
        db_column='telefono'
    )

    # --- Rol como atributo (antes era FK a una tabla aparte) ---
    rol = models.CharField(
        max_length=20,
        choices=RolUsuario.choices,
        default=RolUsuario.CLIENTE,
        verbose_name='Rol',
        db_column='rol'
    )

    estado = models.BooleanField(
        default=True,
        verbose_name='Estado (activo/inactivo)',
        db_column='estado'
    )
    tema = models.CharField(
        max_length=10,
        default='dark',
        choices=[('light', 'Claro'), ('dark', 'Oscuro')],
        verbose_name='Tema',
        db_column='tema'
    )

    # Campo específico para barberos
    especialidad = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Especialidad',
        db_column='especialidad'
    )
    foto_perfil = models.ImageField(
        upload_to='usuarios/',
        blank=True,
        null=True,
        verbose_name='Foto de perfil',
        db_column='foto_perfil'
    )

    # Configuración de Login: Entrarán con el EMAIL
    USERNAME_FIELD = 'email'
    # Campos que pide 'createsuperuser' (no incluyas EMAIL ni PASSWORD)
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios'


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
        verbose_name='Usuario que realizó la acción',
        db_column='usuario_id'
    )
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES,
        verbose_name='Tipo',
        db_column='tipo'
    )
    descripcion = models.CharField(
        max_length=255,
        verbose_name='Descripción',
        db_column='descripcion'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha',
        db_column='fecha'
    )

    class Meta:
        verbose_name = 'Registro de actividad'
        verbose_name_plural = 'Registros de actividad'
        db_table = 'registros_actividad'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario} - {self.descripcion} ({self.fecha:%d/%m/%Y %H:%M})"


class Notificacion(models.Model):
    TIPO_CHOICES = (
        ('venta', 'Venta'),
        ('reserva', 'Reserva'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Destinatario',
        db_column='usuario_id'
    )
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES,
        verbose_name='Tipo',
        db_column='tipo'
    )
    mensaje = models.CharField(
        max_length=255,
        verbose_name='Mensaje',
        db_column='mensaje'
    )
    url = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='URL',
        db_column='url'
    )
    leida = models.BooleanField(
        default=False,
        verbose_name='Leída',
        db_column='leida'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha',
        db_column='fecha'
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        db_table = 'notificaciones'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario} - {self.mensaje}"