from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, RegistroActividad, Notificacion


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        'username', 'tipo_documento', 'first_name', 'last_name',
        'email', 'telefono', 'rol', 'estado', 'date_joined',
    )
    list_filter = ('rol', 'estado', 'tipo_documento', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'telefono')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password', 'tipo_documento')}),
        ('Información personal', {
            'fields': (
                'first_name', 'segundo_nombre',
                'last_name', 'segundo_apellido',
                'email', 'telefono', 'foto_perfil',
            )
        }),
        ('Rol y estado', {'fields': ('rol', 'estado', 'especialidad', 'tema')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'descripcion', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('descripcion', 'usuario__username', 'usuario__email')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'mensaje', 'leida', 'fecha')
    list_filter = ('tipo', 'leida', 'fecha')
    search_fields = ('mensaje', 'usuario__username', 'usuario__email')