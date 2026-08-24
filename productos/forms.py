import re

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
# VALIDACIÓN GENERAL DE TEXTOS
# ==========================================================

def validar_texto(valor, campo):
    """
    Permite:
    - Letras
    - Números
    - Espacios
    - Tildes
    - Ñ

    No permite caracteres especiales.
    """

    if not valor:
        raise forms.ValidationError(
            f'El campo {campo} es obligatorio.'
        )

    valor = valor.strip()

    if not re.fullmatch(
        r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+',
        valor
    ):
        raise forms.ValidationError(
            f'El campo {campo} solo puede contener '
            'letras, números y espacios.'
        )

    return valor


# ==========================================================
# VALIDACIÓN DE DESCRIPCIONES
# ==========================================================

def validar_descripcion(valor, campo):
    """
    Valida descripciones permitiendo:
    - Letras
    - Números
    - Espacios
    - Tildes
    - Ñ

    No permite caracteres especiales.
    """

    if not valor:
        return valor

    valor = valor.strip()

    if not re.fullmatch(
        r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+',
        valor
    ):
        raise forms.ValidationError(
            f'El campo {campo} solo puede contener '
            'letras, números y espacios.'
        )

    return valor


# ==========================================================
# FORMULARIO PRODUCTO
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
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'El nombre solo puede contener '
                        'letras, números y espacios.'
                    ),
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Descripción del producto',
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'La descripción solo puede contener '
                        'letras, números y espacios.'
                    ),
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

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        return validar_texto(
            nombre,
            'nombre del producto'
        )

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')

        return validar_descripcion(
            descripcion,
            'descripción'
        )

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')

        if precio is not None and precio < 0:
            raise forms.ValidationError(
                'El precio no puede ser negativo.'
            )

        return precio


# ==========================================================
# FORMULARIO EXISTENCIAS
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
                    'min': '0',
                    'step': '1',
                }
            ),

            'stock_min': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '1',
                }
            ),

            'stock_max': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '1',
                }
            ),

            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Observaciones',
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'Solo se permiten letras, números '
                        'y espacios.'
                    ),
                }
            ),
        }

    def clean_cantidad_actual(self):
        cantidad = self.cleaned_data.get(
            'cantidad_actual'
        )

        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError(
                'La cantidad actual no puede ser negativa.'
            )

        return cantidad

    def clean_stock_min(self):
        stock_min = self.cleaned_data.get(
            'stock_min'
        )

        if stock_min is not None and stock_min < 0:
            raise forms.ValidationError(
                'El stock mínimo no puede ser negativo.'
            )

        return stock_min

    def clean_stock_max(self):
        stock_max = self.cleaned_data.get(
            'stock_max'
        )

        if stock_max is not None and stock_max < 0:
            raise forms.ValidationError(
                'El stock máximo no puede ser negativo.'
            )

        return stock_max

    def clean_observaciones(self):
        observaciones = self.cleaned_data.get(
            'observaciones'
        )

        return validar_descripcion(
            observaciones,
            'observaciones'
        )

    def clean(self):
        cleaned_data = super().clean()

        stock_min = cleaned_data.get('stock_min')
        stock_max = cleaned_data.get('stock_max')

        if (
            stock_min is not None
            and stock_max is not None
            and stock_max < stock_min
        ):
            raise forms.ValidationError(
                'El stock máximo no puede ser menor '
                'que el stock mínimo.'
            )

        return cleaned_data


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
                    'class': 'form-control',
                    'placeholder': 'Nombre del cliente',
                    'pattern': (
                        r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'El nombre solo puede contener '
                        'letras y espacios.'
                    ),
                }
            ),

            'correo': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'correo@ejemplo.com',
                }
            ),

            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '3001234567',
                    'pattern': r'^[0-9]+$',
                    'inputmode': 'numeric',
                    'title': (
                        'El teléfono solo puede contener '
                        'números.'
                    ),
                }
            ),

            'direccion': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Calle 10 # 20-30',
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s#./-]+$'
                    ),
                    'title': (
                        'La dirección puede contener letras, '
                        'números, espacios y los caracteres '
                        '# . / -'
                    ),
                }
            ),

            'metodo_pago': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
        }

    def clean_nombre_cliente(self):
        nombre = self.cleaned_data.get(
            'nombre_cliente'
        )

        if not nombre:
            raise forms.ValidationError(
                'El nombre del cliente es obligatorio.'
            )

        nombre = nombre.strip()

        if not re.fullmatch(
            r'[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+',
            nombre
        ):
            raise forms.ValidationError(
                'El nombre solo puede contener '
                'letras y espacios.'
            )

        return nombre

    def clean_telefono(self):
        telefono = self.cleaned_data.get(
            'telefono'
        )

        if not telefono:
            raise forms.ValidationError(
                'El teléfono es obligatorio.'
            )

        telefono = telefono.strip()

        if not telefono.isdigit():
            raise forms.ValidationError(
                'El teléfono solo puede contener números.'
            )

        if len(telefono) < 7 or len(telefono) > 15:
            raise forms.ValidationError(
                'El teléfono debe tener entre 7 y 15 números.'
            )

        return telefono

    def clean_direccion(self):
        direccion = self.cleaned_data.get(
            'direccion'
        )

        if not direccion:
            return direccion

        direccion = direccion.strip()

        if not re.fullmatch(
            r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s#./-]+',
            direccion
        ):
            raise forms.ValidationError(
                'La dirección contiene caracteres '
                'no permitidos.'
            )

        return direccion


# ==========================================================
# FORMULARIO DETALLE VENTA
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
                    'min': '1',
                    'step': '1',
                }
            ),
        }

        labels = {
            'codigo_producto': 'Producto',
            'cantidad': 'Cantidad'
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get(
            'cantidad'
        )

        if cantidad is None:
            raise forms.ValidationError(
                'La cantidad es obligatoria.'
            )

        if cantidad < 1:
            raise forms.ValidationError(
                'La cantidad debe ser mínimo 1.'
            )

        return cantidad


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
                    ),
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'Solo se permiten letras, números '
                        'y espacios.'
                    ),
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control border-secondary',
                    'placeholder': (
                        'Descripción de la categoría'
                    ),
                    'rows': 4,
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'Solo se permiten letras, números '
                        'y espacios.'
                    ),
                }
            ),
        }

        labels = {
            'nombre': 'Nombre de Categoría',
            'descripcion': 'Descripción'
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        return validar_texto(
            nombre,
            'nombre de la categoría'
        )

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get(
            'descripcion'
        )

        return validar_descripcion(
            descripcion,
            'descripción'
        )


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
                    'class': 'form-control',
                    'placeholder': 'Nombre del proveedor',
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'Solo se permiten letras, números '
                        'y espacios.'
                    ),
                }
            ),

            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '3001234567',
                    'pattern': r'^[0-9]+$',
                    'inputmode': 'numeric',
                    'title': (
                        'El teléfono solo puede contener '
                        'números.'
                    ),
                }
            ),

            'correo': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'correo@ejemplo.com',
                }
            ),

            'direccion': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Calle 10 # 20-30',
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s#./-]+$'
                    ),
                    'title': (
                        'La dirección puede contener letras, '
                        'números, espacios y # . / -'
                    ),
                }
            ),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        return validar_texto(
            nombre,
            'nombre del proveedor'
        )

    def clean_telefono(self):
        telefono = self.cleaned_data.get(
            'telefono'
        )

        if not telefono:
            raise forms.ValidationError(
                'El teléfono es obligatorio.'
            )

        telefono = telefono.strip()

        if not telefono.isdigit():
            raise forms.ValidationError(
                'El teléfono solo puede contener números.'
            )

        if len(telefono) < 7 or len(telefono) > 15:
            raise forms.ValidationError(
                'El teléfono debe tener entre 7 y 15 números.'
            )

        return telefono

    def clean_direccion(self):
        direccion = self.cleaned_data.get(
            'direccion'
        )

        if not direccion:
            return direccion

        direccion = direccion.strip()

        if not re.fullmatch(
            r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s#./-]+',
            direccion
        ):
            raise forms.ValidationError(
                'La dirección contiene caracteres '
                'no permitidos.'
            )

        return direccion


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
                    'min': '1',
                    'step': '1'
                }
            ),

            'cantidad_venta': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '1'
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

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get(
            'cantidad'
        )

        if cantidad is None or cantidad < 1:
            raise forms.ValidationError(
                'La cantidad debe ser mínimo 1.'
            )

        return cantidad

    def clean_cantidad_venta(self):
        cantidad = self.cleaned_data.get(
            'cantidad_venta'
        )

        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError(
                'La cantidad de venta no puede ser negativa.'
            )

        return cantidad

    def clean_precio_compra(self):
        precio = self.cleaned_data.get(
            'precio_compra'
        )

        if precio is not None and precio < 0:
            raise forms.ValidationError(
                'El precio de compra no puede ser negativo.'
            )

        return precio

    def clean_total(self):
        total = self.cleaned_data.get('total')

        if total is not None and total < 0:
            raise forms.ValidationError(
                'El total no puede ser negativo.'
            )

        return total


# ==========================================================
# FORMULARIO MARCA
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
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'El nombre solo puede contener '
                        'letras, números y espacios.'
                    ),
                }
            ),

            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Descripción de la marca',
                    'rows': 3,
                    'pattern': (
                        r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$'
                    ),
                    'title': (
                        'La descripción solo puede contener '
                        'letras, números y espacios.'
                    ),
                }
            ),

            'estado': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
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
            raise forms.ValidationError(
                'El nombre de la marca es obligatorio.'
            )

        nombre = nombre.strip()

        if len(nombre) < 2:
            raise forms.ValidationError(
                'El nombre debe tener al menos 2 caracteres.'
            )

        if not re.fullmatch(
            r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+',
            nombre
        ):
            raise forms.ValidationError(
                'El nombre solo puede contener '
                'letras, números y espacios.'
            )

        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get(
            'descripcion'
        )

        return validar_descripcion(
            descripcion,
            'descripción'
        )