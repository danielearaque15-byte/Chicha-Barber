from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import Usuario, Rol
from core.validators import validar_password_fuerte

# ==========================================
# VALIDADORES REUTILIZABLES
# ==========================================

# Permite letras (con tildes y ñ) y un único espacio intermedio
validador_nombre = RegexValidator(
    regex=r'^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ]+(?:\s[A-Za-zÁÉÍÓÚÜáéíóúüÑñ]+)*$',
    message='Este campo solo puede contener letras, sin números, símbolos ni espacios dobles.'
)

# Solo dígitos sin ningún tipo de espacios
validador_solo_numeros = RegexValidator(
    regex=r'^\d+$',
    message='Solo se permiten números, sin espacios ni letras.'
)


# ==========================================
# FORMULARIOS DE AUTENTICACIÓN Y REGISTRO
# ==========================================

class RegistroForm(UserCreationForm):
    username = forms.CharField(
        max_length=20,
        min_length=6,
        label="Número de Documento",
        validators=[validador_solo_numeros],
        help_text="Entre 6 y 20 dígitos. Solo números, sin espacios ni letras.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': r'^\d+$',
            'title': 'Solo se permiten números, sin espacios.'
        })
    )

    first_name = forms.CharField(
        max_length=150,
        validators=[validador_nombre],
        help_text="Solo letras, sin números ni símbolos.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        max_length=150,
        validators=[validador_nombre],
        help_text="Solo letras, sin números ni símbolos.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    telefono = forms.CharField(
        max_length=15,
        min_length=7,
        validators=[validador_solo_numeros],
        help_text="10 dígitos. Solo números, sin espacios.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': r'^\d+$'
        })
    )

    email = forms.EmailField(
        help_text="Correo válido y no registrado antes. Ej: nombre@dominio.com",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'telefono',
            'password1',
            'password2'
        )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError("Ya existe una cuenta registrada con este número de documento.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validar_password_fuerte(password1)
        return password1


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            # Forzar en tiempo real la eliminación de espacios y paso a minúsculas
            'oninput': "this.value = this.value.toLowerCase().replace(/\s/g, '')"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        # Se remueven espacios y se pasa a minúsculas para asegurar coincidencia exacta
        return username.strip().lower()


# ==========================================
# FORMULARIOS ADMINISTRATIVOS Y DE PERFIL
# ==========================================

class CrearUsuarioAdminForm(UserCreationForm):
    username = forms.CharField(
        max_length=20,
        min_length=6,
        label="Número de Documento",
        validators=[validador_solo_numeros],
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'^\d+$'})
    )

    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        validators=[validador_nombre],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        validators=[validador_nombre],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    telefono = forms.CharField(
        max_length=15,
        min_length=7,
        label="Teléfono",
        validators=[validador_solo_numeros],
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'^\d+$'})
    )

    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        label="Rol",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_staff = forms.BooleanField(
        required=False,
        label="Acceso al panel admin",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'telefono', 'rol', 'is_staff',
            'password1', 'password2'
        )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError("Ya existe una cuenta registrada con este número de documento.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validar_password_fuerte(password1)
        return password1


class EditarUsuarioForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        validators=[validador_nombre],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        validators=[validador_nombre],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    telefono = forms.CharField(
        max_length=15,
        min_length=7,
        label="Teléfono",
        validators=[validador_solo_numeros],
        widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'^\d+$'})
    )

    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    is_staff = forms.BooleanField(
        required=False,
        label="Acceso al panel admin",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    estado = forms.BooleanField(
        required=False,
        label="Usuario activo",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'telefono', 'is_staff', 'estado')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = Usuario.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe otra cuenta registrada con este correo electrónico.")
        return email
    
class EditarPerfilForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        validators=[validador_nombre],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre(s)'})
    )

    last_name = forms.CharField(
        max_length=150,
        validators=[validador_nombre],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido(s)'})
    )

    telefono = forms.CharField(
        max_length=15,
        min_length=7,
        validators=[validador_solo_numeros],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono', 'pattern': r'^\d+$'})
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefono', 'email', 'foto_perfil']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = Usuario.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe otra cuenta registrada con este correo electrónico.")
        return email


# ==========================================
# FORMULARIO DE RECUPERACIÓN DE CONTRASEÑA
# ==========================================

class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe tu correo registrado',
            'oninput': "this.value = this.value.toLowerCase().replace(/\s/g, '')"
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Validación estricta: Si no se encuentra en la Base de Datos, detiene el proceso.
        if not Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("No existe ninguna cuenta registrada con este correo electrónico.")
        return email