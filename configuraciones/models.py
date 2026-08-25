import os

from django.db import models
from django.utils.text import slugify
from PIL import Image


# ============================================================
# CARRUSEL
# ============================================================

def carrusel_view(instance, filename):
    ext = filename.split('.')[-1]
    nombre_limpio = slugify(instance.nombre)

    return os.path.join(
        'carrusel/',
        f'{nombre_limpio}_{instance.pk}.{ext}'
    )


class Carrusel(models.Model):

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de modificación'
    )

    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre'
    )

    imagen = models.ImageField(
        upload_to=carrusel_view,
        null=True,
        blank=True,
        verbose_name='Imagen del carrusel'
    )

    texto = models.TextField(
        verbose_name='Texto alternativo (Alt)',
        default='Imagen de carrusel',
        help_text='Descripción para accesibilidad y SEO'
    )

    estado = models.BooleanField(
        default=True,
        verbose_name='Estado'
    )

    class Meta:
        verbose_name = 'Carrusel'
        verbose_name_plural = 'Carruseles'
        db_table = 'carrusel'

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):

        # ----------------------------------------------------
        # Guardar primero para obtener el ID
        # ----------------------------------------------------
        if self.pk is None and self.imagen:

            imagen_temporal = self.imagen
            self.imagen = None

            super().save(*args, **kwargs)

            self.imagen = imagen_temporal
            super().save(update_fields=['imagen'])

        else:
            super().save(*args, **kwargs)

        # ----------------------------------------------------
        # Mantener máximo 4 carruseles activos
        # ----------------------------------------------------
        if self.estado:

            carruseles_activos = (
                Carrusel.objects
                .filter(estado=True)
                .order_by('fecha_modificacion')
            )

            cantidad = carruseles_activos.count()

            if cantidad > 4:

                ids_desactivar = list(
                    carruseles_activos
                    .exclude(pk=self.pk)
                    .values_list('pk', flat=True)[:cantidad - 4]
                )

                if ids_desactivar:

                    Carrusel.objects.filter(
                        pk__in=ids_desactivar
                    ).update(estado=False)

        # ----------------------------------------------------
        # Redimensionar imagen
        # ----------------------------------------------------
        if self.imagen:

            try:

                img = Image.open(self.imagen.path)

                target_size = (1200, 500)

                if img.size != target_size:

                    from PIL import ImageOps

                    if hasattr(Image, 'Resampling'):
                        resample_filter = Image.Resampling.LANCZOS
                    else:
                        resample_filter = Image.LANCZOS

                    img = ImageOps.fit(
                        img,
                        target_size,
                        method=resample_filter
                    )

                    if (
                        img.mode in ('RGBA', 'P')
                        and self.imagen.path.lower().endswith(
                            ('.jpg', '.jpeg')
                        )
                    ):
                        img = img.convert('RGB')

                    img.save(self.imagen.path)

            except Exception as e:

                print(
                    f'Error al redimensionar la imagen: {e}'
                )


# ============================================================
# CONFIGURACIÓN
# ============================================================

def configuracion_imagen_path(instance, filename):
    ext = filename.split('.')[-1]
    nombre_limpio = slugify(instance.nombre)

    return os.path.join(
        'configuracion/',
        f'{nombre_limpio}_{instance.pk}.{ext}'
    )


class Configuracion(models.Model):

    codigo = models.AutoField(
        primary_key=True,
        verbose_name='Código'
    )

    fecha_realizacion = models.DateTimeField(
        verbose_name='Fecha de realización'
    )

    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre'
    )

    descripcion = models.TextField(
        verbose_name='Descripción'
    )

    imagen = models.ImageField(
        upload_to=configuracion_imagen_path,
        null=True,
        blank=True,
        verbose_name='Imagen'
    )

    estado = models.BooleanField(
        default=True,
        verbose_name='Estado'
    )

    class Meta:
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'
        db_table = 'configuracion'

    def __str__(self):
        return self.nombre


# ============================================================
# FUNCIONES PARA ARCHIVOS DE CARRUSEL
# ============================================================

def eliminar_carrusel(instance, filename):
    ext = filename.split('.')[-1]
    nombre_limpio = slugify(instance.nombre)

    return os.path.join(
        'carrusel/',
        f'{nombre_limpio}_{instance.pk}_quitar.{ext}'
    )


def editar_carrusel(instance, filename):
    ext = filename.split('.')[-1]
    nombre_limpio = slugify(instance.nombre)

    return os.path.join(
        'carrusel/',
        f'{nombre_limpio}_{instance.pk}_editar.{ext}'
    )