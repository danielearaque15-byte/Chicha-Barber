from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from .models import Producto, Categoria, Marca, Promocion, DetalleProducto
from .forms import ProductoForm, CategoriaForm, MarcaForm, PromocionForm


# ==========================================================
# 🛍️ PRODUCTOS
# ==========================================================

def productos_galeria(request):
    factura_id = request.GET.get('factura_id')

    if factura_id:
        request.session['active_factura_id'] = factura_id

    buscar = request.GET.get('buscar', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    marca_id = request.GET.get('marca', '').strip()

    productos = Producto.objects.filter(
        estado=True
    ).select_related(
        'codigo_categoria',
        'codigo_marca',
        'codigo_detalle_producto'
    )

    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) |
            Q(descripcion__icontains=buscar) |
            Q(codigo_categoria__nombre__icontains=buscar) |
            Q(codigo_marca__nombre__icontains=buscar)
        )

    if categoria_id and categoria_id.isdigit():
        productos = productos.filter(
            codigo_categoria_id=int(categoria_id)
        )

    if marca_id and marca_id.isdigit():
        productos = productos.filter(
            codigo_marca_id=int(marca_id)
        )

    context = {
        'titulo': 'Galería de Productos',
        'productos': productos,
        'categorias': Categoria.objects.all().order_by('nombre'),
        'marcas': Marca.objects.filter(estado=True).order_by('nombre'),
        'categoria_seleccionada': int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
        'marca_seleccionada': int(marca_id) if marca_id and marca_id.isdigit() else None,
        'buscar': buscar,
    }

    return render(
        request,
        'catalogo/productos/productos_galeria.html',
        context
    )


def lista_productos_admin(request):
    productos = Producto.objects.select_related('codigo_categoria', 'codigo_marca').all()

    context = {
        'titulo': 'Lista de Productos',
        'productos': productos,
        'total_productos': Producto.total_productos(),
        'activos': Producto.total_activos(),
        'inactivos': Producto.total_inactivos(),
    }

    return render(
        request,
        'catalogo/productos/productos_admin.html',
        context
    )


def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect('catalogo:lista_productos_admin')
    else:
        form = ProductoForm()

    return render(
        request,
        'catalogo/productos/crear_producto.html',
        {
            'titulo': 'Crear Producto',
            'form': form
        }
    )


def editar_producto(request, pk):
    producto = get_object_or_404(
        Producto,
        codigo_producto=pk
    )

    if request.method == 'POST':
        form = ProductoForm(
            request.POST,
            request.FILES,
            instance=producto
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect('catalogo:lista_productos_admin')
    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        'catalogo/productos/editar_producto.html',
        {
            'titulo': 'Editar Producto',
            'form': form,
            'producto': producto
        }
    )


def eliminar_producto(request, pk):
    producto = get_object_or_404(
        Producto,
        codigo_producto=pk
    )
    producto.delete()
    messages.success(request, "Producto eliminado correctamente.")
    return redirect('catalogo:lista_productos_admin')


# ==========================================================
# 🟣 CATEGORÍAS
# ==========================================================

def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect('catalogo:lista_categorias')
    else:
        form = CategoriaForm()

    return render(
        request,
        'catalogo/categorias/crear_categoria.html',
        {'form': form}
    )


def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')

    return render(
        request,
        'catalogo/categorias/lista_categoria.html',
        {
            'titulo': 'Categorías',
            'categorias': categorias
        }
    )


def editar_categoria(request, id):
    categoria = get_object_or_404(
        Categoria,
        codigo=id
    )

    if request.method == 'POST':
        form = CategoriaForm(
            request.POST,
            instance=categoria
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect('catalogo:lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)

    return render(
        request,
        'catalogo/categorias/editar_categoria.html',
        {
            'form': form,
            'categoria': categoria
        }
    )


def eliminar_categoria(request, id):
    categoria = get_object_or_404(
        Categoria,
        codigo=id
    )
    categoria.delete()
    messages.success(request, "Categoría eliminada.")
    return redirect('catalogo:lista_categorias')


# ==========================================================
# 🏷️ MARCAS
# ==========================================================

def lista_marcas(request):
    marcas = Marca.objects.all().prefetch_related('productos').order_by('nombre')

    total_marcas = Marca.objects.count()
    marcas_activas = Marca.objects.filter(estado=True).count()
    marcas_inactivas = Marca.objects.filter(estado=False).count()

    return render(
        request,
        'catalogo/marca/marca.html',
        {
            'titulo': 'Marcas',
            'marcas': marcas,
            'total_marcas': total_marcas,
            'marcas_activas': marcas_activas,
            'marcas_inactivas': marcas_inactivas,
        }
    )


def crear_marca(request):
    if request.method == 'POST':
        form = MarcaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Marca creada correctamente.")
            return redirect('catalogo:lista_marcas')
    else:
        form = MarcaForm()

    return render(
        request,
        'catalogo/marca/crear_marca.html',
        {
            'titulo': 'Crear Marca',
            'form': form,
        }
    )


def editar_marca(request, id):
    marca = get_object_or_404(
        Marca,
        codigo=id
    )

    if request.method == 'POST':
        form = MarcaForm(
            request.POST,
            instance=marca
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Marca actualizada correctamente.")
            return redirect('catalogo:lista_marcas')
    else:
        form = MarcaForm(instance=marca)

    return render(
        request,
        'catalogo/marca/editar_marca.html',
        {
            'titulo': 'Editar Marca',
            'form': form,
            'marca': marca
        }
    )


def eliminar_marca(request, id):
    marca = get_object_or_404(
        Marca,
        codigo=id
    )
    marca.delete()
    messages.success(request, "Marca eliminada correctamente.")
    return redirect('catalogo:lista_marcas')


# ==========================================================
# 🎁 PROMOCIONES
# ==========================================================

def lista_promociones(request):
    promociones = Promocion.objects.select_related('codigo_producto', 'codigo_servicio').all()
    return render(
        request,
        'catalogo/promociones/lista_promociones.html',
        {
            'titulo': 'Promociones',
            'promociones': promociones
        }
    )


def crear_promocion(request):
    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción creada correctamente.")
            return redirect('catalogo:lista_promociones')
    else:
        form = PromocionForm()

    return render(
        request,
        'catalogo/promociones/crear_promocion.html',
        {'titulo': 'Crear Promoción', 'form': form}
    )


def editar_promocion(request, id):
    promocion = get_object_or_404(Promocion, codigo=id)
    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES, instance=promocion)
        if form.is_valid():
            form.save()
            messages.success(request, "Promoción actualizada correctamente.")
            return redirect('catalogo:lista_promociones')
    else:
        form = PromocionForm(instance=promocion)

    return render(
        request,
        'catalogo/promociones/editar_promocion.html',
        {'titulo': 'Editar Promoción', 'form': form, 'promocion': promocion}
    )


def eliminar_promocion(request, id):
    promocion = get_object_or_404(Promocion, codigo=id)
    promocion.delete()
    messages.success(request, "Promoción eliminada correctamente.")
    return redirect('catalogo:lista_promociones')