from django import forms

from .models import (
    Producto,
    existencias,
    venta,
    detalleventa,
    Proveedor,
    Categoria,
    Adquisicion,
    Marca,
)


# ==========================================================
# FORMULARIO PRODUCTO
# Solo información del catálogo
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
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Descripción del producto',
                }
            ),

            'codigo_categoria': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),

            'codigo_marca': forms.Select(
                attrs={
                    'class': 'form-select',
                }
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
                attrs={
                    'class': 'form-control',
                }
            ),

            'estado': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
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


# ==========================================================
# FORMULARIO existencias
# Cantidad, stock mínimo, stock máximo y observaciones
# ==========================================================

class existenciasForm(forms.ModelForm):

    class Meta:

        model = existencias

        fields = [
            'cantidad_actual',
            'stock_min',
            'stock_max',
            'observaciones'
        ]

        widgets = {

            'cantidad_actual': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0'
                }
            ),

            'stock_min': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0'
                }
            ),

            'stock_max': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0'
                }
            ),

            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
        }


# ==========================================================
# FORMULARIO VENTA
# ==========================================================

class ventaForm(forms.ModelForm):

    class Meta:
        model = venta

        fields = [
            'nombre_cliente',
            'correo',
            'telefono',
            'direccion',
            'metodo_pago'
        ]

        widgets = {

            'nombre_cliente': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'correo': forms.EmailInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'direccion': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'metodo_pago': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
        }


# ==========================================================
# FORMULARIO DETALLE VENTA
# Validación de existencias
# ==========================================================

class detalleventaForm(forms.ModelForm):

    class Meta:

        model = detalleventa

        fields = [
            'codigo_producto',
            'cantidad'
        ]

        widgets = {

            'codigo_producto': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'cantidad': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1'
                }
            ),
        }

        labels = {

            'codigo_producto': 'Producto',

            'cantidad': 'Cantidad'
        }


# ==========================================================
# FORMULARIO CATEGORÍA
# ==========================================================

class CategoriaForm(forms.ModelForm):

    class Meta:

        model = Categoria

        fields = [
            'nombre',
            'descripcion'
        ]

        widgets = {

            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control border-secondary',
                    'placeholder': (
                        'Ingrese el nombre de la categoría'
                    )
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control border-secondary',
                    'placeholder': (
                        'Descripción de la categoría'
                    ),
                    'rows': 4
                }
            ),
        }

        labels = {

            'nombre': 'Nombre de Categoría',

            'descripcion': 'Descripción'
        }


# ==========================================================
# FORMULARIO PROVEEDOR
# ==========================================================

class ProveedorForm(forms.ModelForm):

    class Meta:

        model = Proveedor

        fields = [
            'nombre',
            'telefono',
            'correo',
            'direccion'
        ]

        widgets = {

            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'correo': forms.EmailInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'direccion': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }


# ==========================================================
# FORMULARIO ADQUISICIÓN
# ==========================================================

class AdquisicionForm(forms.ModelForm):

    class Meta:

        model = Adquisicion

        fields = [
            'codigo_proveedor',
            'codigo_producto',
            'cantidad',
            'cantidad_venta',
            'precio_compra',
            'total'
        ]

        widgets = {

            'codigo_proveedor': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'codigo_producto': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'cantidad': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1'
                }
            ),

            'cantidad_venta': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0'
                }
            ),

            'precio_compra': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '0.01'
                }
            ),

            'total': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '0.01'
                }
            ),
        }
        
# ==========================================================
# 🏷️ FORMULARIO MARCA
# ==========================================================

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
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Descripción de la marca',
                    'rows': 3,
                }
            ),

            'estado': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
        }

    def clean_nombre(self):

        nombre = self.cleaned_data.get(
            'nombre'
        )

        if not nombre:
            raise forms.ValidationError(
                'El nombre de la marca es obligatorio.'
            )

        nombre = nombre.strip()

        if len(nombre) < 2:
            raise forms.ValidationError(
                'El nombre debe tener al menos 2 caracteres.'
            )

        return nombre

