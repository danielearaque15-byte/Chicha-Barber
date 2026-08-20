from django import forms

from .models import  Producto,Inventario,venta,detalleventa,Proveedor,Categoria



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
            'imagen',
            'estado'
        ]

        widgets = {

            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),

            'codigo_categoria': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'imagen': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'estado': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input'
                }
            ),
        }


# ==========================================================
# FORMULARIO INVENTARIO
# Cantidad, stock mínimo, stock máximo y observaciones
# ==========================================================

class InventarioForm(forms.ModelForm):

    class Meta:

        model = Inventario

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
# Validación de inventario
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