from datetime import datetime

from django.db import models
from django.utils import timezone
from servicios.models import Servicios, Promocion
from usuarios.models import Usuario, Notificacion
from django.db.models.signals import post_save
from django.dispatch import receiver


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

    def __str__(self):
        return f"{self.profesional.get_full_name()} - {self.fecha} {self.hora_inicio} a {self.hora_fin} ({self.estado})"


# =========================
# RESERVAS
# =========================
class Reserva(models.Model):

    ESTADO_CHOICES = [
        ('reservada', 'Reservada'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    # Relaciones directas según el MER
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

    # Campo proveniente directamente del MER
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

    # Campos opcionales / soporte para clientes no registrados o histórico
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
        null=True,
        blank=True,
        verbose_name="Promoción Aplicada"
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva', '-fecha_creacion']

    def save(self, *args, **kwargs):
        # Asigna automáticamente la fecha y hora si hay un turno vinculado
        if self.turno and not self.fecha_reserva:
            self.fecha_reserva = timezone.make_aware(
                datetime.combine(self.turno.fecha, self.turno.hora_inicio)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        cliente_nombre = self.nombre_cliente or (self.cliente.get_full_name() if self.cliente else 'Sin cliente')
        fecha = self.fecha_reserva or (self.turno.fecha if self.turno else 'Sin fecha')
        return f"{cliente_nombre} - {self.servicio.nombre} ({fecha})"


# =========================
# SEÑALES (SIGNALS)
# =========================
@receiver(post_save, sender=Reserva)
def notificar_reserva(sender, instance, created, **kwargs):
    if not created:
        return

    cliente_nombre = instance.nombre_cliente or (
        instance.cliente.get_full_name() if instance.cliente else 'Cliente'
    )

    # Notificación al cliente
    if instance.cliente:
        Notificacion.objects.create(
            usuario=instance.cliente,
            tipo='reserva',
            mensaje=f"Tu reserva de {instance.servicio.nombre} fue registrada con éxito.",
            url='/perfil/'
        )

    # Notificación a los administradores
    admins = Usuario.objects.filter(rol='admin')
    for admin in admins:
        Notificacion.objects.create(
            usuario=admin,
            tipo='reserva',
            mensaje=f"Nueva reserva de {cliente_nombre} para {instance.servicio.nombre}.",
            url='/admin-reservas/'
        )