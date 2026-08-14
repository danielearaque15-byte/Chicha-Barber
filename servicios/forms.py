from django import forms # type: ignore
from django.forms import ModelForm # type: ignore
from django.contrib.admin.widgets import FilteredSelectMultiple # type: ignore
from .models import Servicios, Promocion, Calificacion


class ServiciosForm(ModelForm):
    class Meta:
        model = Servicios
        fields=['nombre', 'precio', 'duracion','imagen', ]
        
class ServiciosEditarForm(ModelForm):
    class Meta:
        model = Servicios
        fields = '__all__'
        
class PromocionForm(ModelForm):
    class Meta:
        model = Promocion
        fields=['servicio', 'nombre', 'porcentaje_descuento', 'duracion', 'descripcion', 'imagen',]
        
class PromocionEditarForm(ModelForm):
    class Meta:
        model = Promocion
        fields = '__all__'
        
class calificacionForm(ModelForm):
    class Meta:
        model = Calificacion
        # Corrección: se quita 'cliente' — ahora se asigna automáticamente
        # en la vista con request.user, no lo llena el usuario a mano.
        fields = ['servicio', 'puntuacion', 'comentario']
        widgets = {
            'servicio': forms.Select(attrs={'class': 'form-control'}),
            'puntuacion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ResponderCalificacionForm(forms.Form):
    respuesta = forms.CharField(
        label='Escribe tu respuesta',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe aquí tu respuesta al cliente...'}),
        required=True
    )