import re
from django import forms
from .models import Producto, Categoria, Marca, Promocion
from servicios.models import Servicio


# ==========================================================
# VALIDACIONES GENERALES
# ==========================================================

def validar_texto(valor, campo):
    if not valor:
        raise forms.ValidationError(f'El campo {campo} es obligatorio.')

    valor = valor.strip()

    if not re.fullmatch(r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+', valor):
        raise forms.ValidationError(
            f'El campo {campo} solo puede contener letras, números y espacios.'
        )

    return valor


def validar_descripcion(valor, campo):
    if not valor:
        return valor

    valor = valor.strip()

    if not re.fullmatch(r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+', valor):
        raise forms.ValidationError(
            f'El campo {campo} solo puede contener letras, números y espacios.'
        )

    return valor


# ==========================================================
# FORMULARIOS APP CATÁLOGO
# ==========================================================

class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'descripcion',
            'codigo_categoria',
            'codigo_marca',
            'precio',
            'imagen',
            'estado',
        ]
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del producto',
                    'pattern': r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$',
                    'title': 'El nombre solo puede contener letras, números y espacios.',
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Descripción del producto',
                    'pattern': r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$',
                    'title': 'La descripción solo puede contener letras, números y espacios.',
                }
            ),
            'codigo_categoria': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'codigo_marca': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'precio': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '0.01',
                    'placeholder': 'Precio',
                }
            ),
            'imagen': forms.ClearableFileInput(
                attrs={'class': 'form-control'}
            ),
            'estado': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'codigo_categoria': 'Categoría',
            'codigo_marca': 'Marca',
            'precio': 'Precio',
            'imagen': 'Imagen',
            'estado': 'Activo',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        return validar_texto(nombre, 'nombre del producto')

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        return validar_descripcion(descripcion, 'descripción')

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio < 0:
            raise forms.ValidationError('El precio no puede ser negativo.')
        return precio


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = [
            'nombre',
            'descripcion',
        ]
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control border-secondary',
                    'placeholder': 'Ingrese el nombre de la categoría',
                    'pattern': r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$',
                    'title': 'Solo se permiten letras, números y espacios.',
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control border-secondary',
                    'placeholder': 'Descripción de la categoría',
                    'rows': 4,
                    'pattern': r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$',
                    'title': 'Solo se permiten letras, números y espacios.',
                }
            ),
        }
        labels = {
            'nombre': 'Nombre de Categoría',
            'descripcion': 'Descripción',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        return validar_texto(nombre, 'nombre de la categoría')

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        return validar_descripcion(descripcion, 'descripción')


class MarcaForm(forms.ModelForm):

    class Meta:
        model = Marca
        fields = [
            'nombre',
            'descripcion',
            'estado',
        ]
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre de la marca',
                    'pattern': r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$',
                    'title': 'El nombre solo puede contener letras, números y espacios.',
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Descripción de la marca',
                    'rows': 3,
                    'pattern': r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$',
                    'title': 'La descripción solo puede contener letras, números y espacios.',
                }
            ),
            'estado': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'nombre': 'Nombre de la Marca',
            'descripcion': 'Descripción',
            'estado': 'Activo',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        if not nombre:
            raise forms.ValidationError('El nombre de la marca es obligatorio.')

        nombre = nombre.strip()

        if len(nombre) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')

        if not re.fullmatch(r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras, números y espacios.')

        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        return validar_descripcion(descripcion, 'descripción')


# ==========================================================
# FORMULARIO DE PROMOCIONES (PRODUCTO / SERVICIO)
# ==========================================================

class PromocionForm(forms.ModelForm):

    class Meta:
        model = Promocion
        fields = [
            'nombre',
            'porcentaje_descuento',
            'descripcion',
            'fecha_inicio',
            'fecha_fin',
            'imagen',
            'estado',
            'codigo_producto',
            'codigo_servicio',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la promoción'}),
            'porcentaje_descuento': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'codigo_producto': forms.Select(attrs={'class': 'form-select'}),
            'codigo_servicio': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        producto = cleaned_data.get("codigo_producto")
        servicio = cleaned_data.get("codigo_servicio")

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise forms.ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        if not producto and not servicio:
            raise forms.ValidationError("Debe asociar la promoción a al menos un Producto o un Servicio.")

        return cleaned_data