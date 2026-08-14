from django import forms # type: ignore
from django.forms import ModelForm # type: ignore
from django.contrib.admin.widgets import FilteredSelectMultiple # type: ignore
from .models import Servicios, Promocion, Calificacion



class ServiciosForm(ModelForm):
    class Meta:
        model = Servicios
        fields=['nombre', 'precio', 'duracion','imagen', ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracion': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
class ServiciosEditarForm(ModelForm):
    class Meta:
        model = Servicios
        fields = '__all__'
        
class PromocionForm(ModelForm):
    class Meta:
        model = Promocion
        fields=['servicio', 'nombre', 'porcentaje_descuento', 'duracion', 'descripcion', 'imagen',]
        widgets = {
            'servicio': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'porcentaje_descuento': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'duracion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PromocionEditarForm(ModelForm):
    class Meta:
        model = Promocion
        fields = '__all__'
        
class CalificacionForm(ModelForm):
    class Meta:
        model = Calificacion
        fields = ['servicio', 'cliente', 'puntuacion', 'comentario']
        widgets = {
            'servicio': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'puntuacion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
           
        }

        
        

class ResponderCalificacionForm(forms.Form):
    respuesta = forms.CharField(
        label='Escribe tu respuesta',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe aquí tu respuesta al cliente...'}),
        required=True
    )
    
    


