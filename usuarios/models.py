from django.contrib.auth.models import AbstractUser
from django.db import models

# Definimos los roles fuera o dentro de la clase, está bien así.
ROLES = (
    ('cliente', 'Cliente'),
    ('barbero', 'Barbero'),
    ('admin', 'Administrador'),
)

class Usuario(AbstractUser):
    # El documento será el 'username' interno de Django
    username = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Número de Documento"
    )
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    estado = models.BooleanField(default=True, verbose_name='Estado')
    tema = models.CharField(max_length=10, default='dark', choices=[('light', 'Claro'), ('dark', 'Oscuro')])
    
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
    # Campos que pide el comando 'createsuperuser' (no incluyas el EMAIL ni el PASSWORD aquí)
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

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