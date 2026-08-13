from datetime import datetime
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from servicios.models import Servicios, Promocion
from usuarios.models import Usuario, Notificacion


# =========================
# TURNOS
# =========================
class Turno(models.Model):

    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('cancelado', 'Cancelado'),
    ]

    profesional = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='turnos',
        verbose_name='Profesional'
    )
    fecha = models.DateField(
        verbose_name='Fecha del Turno'
    )
    hora_inicio = models.TimeField(
        verbose_name='Hora de Inicio'
    )
    hora_fin = models.TimeField(
        verbose_name='Hora de Fin'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='disponible',
        verbose_name='Estado'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['fecha', 'hora_inicio']

    def clean(self):
        super().clean()
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError({
                'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio.'
            })

    def __str__(self):
        nombre_profesional = (
            self.profesional.get_full_name() 
            if hasattr(self.profesional, 'get_full_name') and self.profesional.get_full_name()
            else str(self.profesional)
        )
        return f"{nombre_profesional} - {self.fecha} ({self.hora_inicio} a {self.hora_fin}) [{self.get_estado_display()}]"


# =========================
# RESERVAS
# =========================
class Reserva(models.Model):

    ESTADO_CHOICES = [
        ('reservada', 'Reservada'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    # Relaciones según el MER
    turno = models.ForeignKey(
        Turno,
        on_delete=models.SET_NULL,
        related_name='reservas',
        null=True,
        blank=True,
        verbose_name='Turno'
    )
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='reservas_cliente',
        null=True,
        blank=True,
        verbose_name='Cliente'
    )
    servicio = models.ForeignKey(
        Servicios,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name="Servicio"
    )
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='reservada',
        verbose_name="Estado"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    # Campos para clientes invitados o historial
    nombre_cliente = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombre del Cliente (Invitado)"
    )
    correo_cliente = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo Electrónico"
    )
    telefono_cliente = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    fecha_reserva = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha y Hora de la Reserva"
    )
    precio_historico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Precio Histórico'
    )
    promocion = models.ForeignKey(
        Promocion,
        on_delete=models.SET_NULL,
        related_name='reservas',
        null=True,
        blank=True,
        verbose_name="Promoción Aplicada"
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva', '-fecha_creacion']

    def save(self, *args, **kwargs):
        # Asignación segura de fecha_reserva respetando zonas horarias
        if self.turno and not self.fecha_reserva:
            dt_naive = datetime.combine(self.turno.fecha, self.turno.hora_inicio)
            if timezone.is_naive(dt_naive):
                self.fecha_reserva = timezone.make_aware(dt_naive)
            else:
                self.fecha_reserva = dt_naive
        super().save(*args, **kwargs)

    def __str__(self):
        if self.nombre_cliente:
            cliente_nombre = self.nombre_cliente
        elif self.cliente and hasattr(self.cliente, 'get_full_name') and self.cliente.get_full_name():
            cliente_nombre = self.cliente.get_full_name()
        elif self.cliente:
            cliente_nombre = str(self.cliente)
        else:
            cliente_nombre = 'Sin cliente'

        fecha_str = (
            self.fecha_reserva.strftime('%Y-%m-%d %H:%M') 
            if self.fecha_reserva 
            else (str(self.turno.fecha) if self.turno else 'Sin fecha')
        )
        return f"{cliente_nombre} - {self.servicio.nombre} ({fecha_str})"


# =========================
# CALIFICACIONES (Según MER)
# =========================
class Calificacion(models.Model):
    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.CASCADE,
        related_name='calificacion',
        verbose_name='Reserva'
    )
    puntuacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Puntuación'
    )
    comentario = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentario'
    )
    fecha_calificacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Calificación'
    )
    mostrar_inicio = models.BooleanField(
        default=False,
        verbose_name='Mostrar en Inicio'
    )

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        ordering = ['-fecha_calificacion']

    def __str__(self):
        return f"Calificación {self.puntuacion}/5 - Reserva #{self.reserva_id}"


# =========================
# SEÑALES (SIGNALS)
# =========================
@receiver(post_save, sender=Reserva)
def notificar_reserva(sender, instance, created, **kwargs):
    if not created:
        return

    cliente_nombre = instance.nombre_cliente or (
        instance.cliente.get_full_name() 
        if instance.cliente and hasattr(instance.cliente, 'get_full_name') and instance.cliente.get_full_name()
        else 'Cliente'
    )

    # Notificación al cliente
    if instance.cliente:
        Notificacion.objects.create(
            usuario=instance.cliente,
            tipo='reserva',
            mensaje=f"Tu reserva de {instance.servicio.nombre} fue registrada con éxito.",
            url='/perfil/'
        )

    # Notificación defensiva a los administradores
    admins = Usuario.objects.filter(Q(rol='admin') | Q(is_superuser=True)).distinct()
    for admin in admins:
        Notificacion.objects.create(
            usuario=admin,
            tipo='reserva',
            mensaje=f"Nueva reserva de {cliente_nombre} para {instance.servicio.nombre}.",
            url='/admin-reservas/'
        )