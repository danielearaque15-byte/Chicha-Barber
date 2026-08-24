from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario, RegistroActividad, Notificacion
from .forms import CrearUsuarioAdminForm


# =========================================================
# ADMINISTRACIÓN DE USUARIOS
# =========================================================

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    # =====================================================
    # FORMULARIO PARA CREAR USUARIOS
    # =====================================================

    add_form = CrearUsuarioAdminForm

    add_fieldsets = (
        (
            'Información de acceso',
            {
                'fields': (
                    'username',
                    'email',
                    'password1',
                    'password2',
                )
            }
        ),

        (
            'Información personal',
            {
                'fields': (
                    'tipo_documento',
                    'first_name',
                    'segundo_nombre',
                    'last_name',
                    'segundo_apellido',
                    'telefono',
                    'foto_perfil',
                )
            }
        ),

        (
            'Rol y configuración',
            {
                'fields': (
                    'rol',
                    'estado',
                    'especialidad',
                    'tema',
                    'is_staff',
                )
            }
        ),
    )

    # =====================================================
    # LISTADO DE USUARIOS
    # =====================================================

    list_display = (
        'username',
        'tipo_documento',
        'first_name',
        'last_name',
        'email',
        'telefono',
        'rol',
        'estado',
        'date_joined',
    )

    # =====================================================
    # FILTROS
    # =====================================================

    list_filter = (
        'rol',
        'estado',
        'tipo_documento',
        'is_staff',
    )

    # =====================================================
    # BÚSQUEDA
    # =====================================================

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'telefono',
    )

    # =====================================================
    # ORDEN
    # =====================================================

    ordering = ('-date_joined',)

    # =====================================================
    # CAMPOS DE SOLO LECTURA
    # =====================================================

    readonly_fields = (
        'last_login',
        'date_joined',
    )

    # =====================================================
    # FORMULARIO PARA EDITAR USUARIOS
    # =====================================================

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'username',
                    'password',
                    'tipo_documento',
                )
            }
        ),

        (
            'Información personal',
            {
                'fields': (
                    'first_name',
                    'segundo_nombre',
                    'last_name',
                    'segundo_apellido',
                    'email',
                    'telefono',
                    'foto_perfil',
                )
            }
        ),

        (
            'Rol y estado',
            {
                'fields': (
                    'rol',
                    'estado',
                    'especialidad',
                    'tema',
                )
            }
        ),

        (
            'Permisos',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            }
        ),

        (
            'Fechas',
            {
                'fields': (
                    'last_login',
                    'date_joined',
                )
            }
        ),
    )

    # =====================================================
    # GUARDAR USUARIO
    # =====================================================

    def save_model(self, request, obj, form, change):
        # Mantener sincronizado el estado personalizado
        # con el estado de autenticación de Django.
        obj.is_active = obj.estado

        super().save_model(request, obj, form, change)


# =========================================================
# REGISTRO DE ACTIVIDADES
# =========================================================

@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'tipo',
        'descripcion',
        'fecha',
    )

    list_filter = (
        'tipo',
        'fecha',
    )

    search_fields = (
        'descripcion',
        'usuario__username',
        'usuario__email',
    )


# =========================================================
# NOTIFICACIONES
# =========================================================

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'tipo',
        'mensaje',
        'leida',
        'fecha',
    )

    list_filter = (
        'tipo',
        'leida',
        'fecha',
    )

    search_fields = (
        'mensaje',
        'usuario__username',
        'usuario__email',
    )