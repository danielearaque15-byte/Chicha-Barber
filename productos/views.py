from decimal import Decimal, InvalidOperation
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, Q

from .models import (
    venta,
    Producto,
    detalleventa,
    existencias,
    Movimientoexistencias,
    Adquisicion,
    DatosTransferencia,
    Categoria,
    Proveedor,
    Bitacora,
    Marca,
)
from .forms import (
    ventaForm,
    detalleventaForm,
    ProductoForm,
    existenciasForm,
    CategoriaForm,
    ProveedorForm,
    AdquisicionForm,
    MarcaForm,
)
from core.utils import enviar_correo_venta

from reservas.models import Reserva


# ==========================================================
# 🟢 CLIENTE - GALERÍA DE PRODUCTOS
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
        'codigo_marca'
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
        'productos/productos/Productos_galeria.html',
        context
    )



# ==========================================================
# 🛒 CARRITO
# ==========================================================

@login_required
def carrito(request):
    return render(
        request,
        'productos/carrito/Carrito.html'
    )


# ==========================================================
# 💳 PAGO
# ==========================================================

@login_required
def pago(request):

    factura_id = request.GET.get('factura_id')

    if factura_id:
        request.session['active_factura_id'] = factura_id

    context = {
        'titulo': 'Método de Pago',
        'datos_banco': DatosTransferencia.get_solo(),
        'factura_id': request.session.get(
            'active_factura_id'
        )
    }

    return render(
        request,
        'productos/pagos/pago.html',
        context
    )


# ==========================================================
# 💳 PROCESAR PAGO CLIENTE
# ==========================================================

@login_required
def procesar_pago_cliente(request):

    if request.method != 'POST':
        return redirect('carrito')

    nombre = request.POST.get('nombre')
    correo = request.POST.get('correo')
    telefono = request.POST.get('telefono')
    metodo_pago = request.POST.get('pago')
    tipo_transferencia = request.POST.get(
        'tipo_transferencia'
    )
    factura_id = request.POST.get('factura_id')
    carrito_json = request.POST.get('carrito')

    comprobante_archivo = request.FILES.get(
        'comprobante'
    )

    if not carrito_json:
        messages.error(
            request,
            "El carrito está vacío."
        )
        return redirect('carrito')

    try:
        carrito_data = json.loads(carrito_json)
    except (json.JSONDecodeError, TypeError):
        messages.error(
            request,
            "Error en el formato del carrito."
        )
        return redirect('carrito')

    if not carrito_data:
        messages.error(
            request,
            "El carrito no contiene elementos."
        )
        return redirect('carrito')

    if (
        metodo_pago in ['transferencia', 'contraentrega']
        and not comprobante_archivo
    ):
        messages.error(
            request,
            "Debes adjuntar el comprobante."
        )
        return redirect('pago')

    try:

        with transaction.atomic():

            estado_inicial = 'pendiente_verificacion'

            metodo_factura = 'efectivo'

            if (
                metodo_pago in [
                    'transferencia',
                    'contraentrega'
                ]
                and tipo_transferencia
            ):
                metodo_factura = tipo_transferencia

            # ------------------------------------------
            # FACTURA
            # ------------------------------------------

            if factura_id:

                factura = get_object_or_404(
                    Factura,
                    id=factura_id
                )

            else:

                factura = Factura.objects.create(
                    cliente=request.user,
                    metodo_pago=metodo_factura,
                    total_pagado=0,
                    estado='pendiente',
                    imagen_transaccion=comprobante_archivo
                )

            # ------------------------------------------
            # VENTA
            # ------------------------------------------

            nueva_venta = venta.objects.create(
                usuario=request.user,
                nombre_cliente=nombre,
                correo=correo,
                telefono=telefono,
                metodo_pago=metodo_pago,
                estado_pago=estado_inicial,
                comprobante=comprobante_archivo,
                total=0
            )

            total_general = Decimal('0')

            # ------------------------------------------
            # PRODUCTOS DEL CARRITO
            # ------------------------------------------

            for item in carrito_data:

                # ======================================
                # RESERVA
                # ======================================

                if item.get('tipo') == 'reserva':

                    reserva = get_object_or_404(
                        Reserva,
                        id=item['id']
                    )

                    precio = Decimal(
                        str(item['precio'])
                    )

                    DetalleFactura.objects.create(
                        factura=factura,
                        reserva=reserva,
                        cantidad=1,
                        precio_unitario=precio,
                        subtotal=precio
                    )

                    total_general += precio

                    continue

                # ======================================
                # PRODUCTO
                # ======================================

                producto = get_object_or_404(
                    Producto,
                    codigo_producto=item['id']
                )

                cantidad = int(
                    item['cantidad']
                )

                if cantidad <= 0:
                    raise ValueError(
                        "La cantidad debe ser mayor que cero."
                    )

                # --------------------------------------
                # existencias
                # --------------------------------------

                existencias = get_object_or_404(
                    existencias,
                    codigo_producto=producto
                )

                if existencias.cantidad_actual < cantidad:

                    raise ValueError(
                        f"No hay suficiente existencias "
                        f"para {producto.nombre}."
                    )

                # --------------------------------------
                # PRECIO
                # --------------------------------------

                precio_venta = getattr(
                    producto,
                    'precio_venta',
                    None
                )

                if precio_venta is None:

                    try:
                        precio_venta = producto.existencias.precio_venta
                    except Exception:

                        raise ValueError(
                            f"El producto "
                            f"{producto.nombre} "
                            f"no tiene precio de venta."
                        )

                precio_venta = Decimal(
                    str(precio_venta)
                )

                subtotal = (
                    precio_venta * cantidad
                )

                # --------------------------------------
                # DETALLE DE VENTA
                # --------------------------------------

                detalle_venta_obj = (
                    detalleventa.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        cantidad=cantidad
                    )
                )

                # --------------------------------------
                # DESCONTAR existencias
                # --------------------------------------

                existencias.cantidad_actual -= cantidad
                existencias.save(
                    update_fields=[
                        'cantidad_actual'
                    ]
                )

                # --------------------------------------
                # MOVIMIENTO DE existencias
                # --------------------------------------

                Movimientoexistencias.objects.create(
                    producto=producto,
                    tipo='salida',
                    cantidad=cantidad,
                    motivo=(
                        f"Venta #{nueva_venta.pk}"
                    )
                )

                # --------------------------------------
                # DETALLE FACTURA
                # --------------------------------------

                DetalleFactura.objects.create(
                    factura=factura,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_venta,
                    subtotal=subtotal
                )

                total_general += subtotal

            # ------------------------------------------
            # ACTUALIZAR VENTA
            # ------------------------------------------

            nueva_venta.total = total_general

            nueva_venta.save(
                update_fields=['total']
            )

            # ------------------------------------------
            # ACTUALIZAR FACTURA
            # ------------------------------------------

            factura.total_pagado = total_general

            factura.save(
                update_fields=['total_pagado']
            )

            # ------------------------------------------
            # LIMPIAR SESIÓN
            # ------------------------------------------

            if 'active_factura_id' in request.session:

                del request.session[
                    'active_factura_id'
                ]

            request.session['carrito'] = {}
            request.session.modified = True

    except ValueError as e:

        messages.error(
            request,
            str(e)
        )

        return redirect('carrito')

    except Exception as e:

        messages.error(
            request,
            f"Error en la transacción: {str(e)}"
        )

        return redirect('carrito')

    # ----------------------------------------------
    # CORREO
    # ----------------------------------------------

    try:

        enviar_correo_venta(
            correo_cliente=correo,
            nombre=nombre,
            carrito=carrito_data,
            total=float(total_general)
        )

    except Exception as e:

        print(
            f"Error enviando correo: {e}"
        )

    if metodo_pago in [
        'transferencia',
        'contraentrega'
    ]:

        messages.success(
            request,
            "Orden registrada. "
            "El administrador verificará "
            "el comprobante."
        )

    else:

        messages.success(
            request,
            "Venta realizada con éxito."
        )

    return redirect(
        reverse('facturas') +
        '?venta_exitosa=1'
    )


# ==========================================================
# 🔵 PRODUCTOS ADMIN
# ==========================================================

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
        'productos/productos/productos_admin.html',
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

            messages.success(
                request,
                "Producto creado correctamente."
            )

            return redirect(
                'lista_productos_admin'
            )

    else:

        form = ProductoForm()

    return render(
        request,
        'productos/productos/crear_producto.html',
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

            messages.success(
                request,
                "Producto actualizado correctamente."
            )

            return redirect(
                'lista_productos_admin'
            )

    else:

        form = ProductoForm(
            instance=producto
        )

    return render(
        request,
        'productos/productos/editar_producto.html',
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

    messages.success(
        request,
        "Producto eliminado correctamente."
    )

    return redirect(
        'lista_productos_admin'
    )


# ==========================================================
# 🧾 BITÁCORA
# ==========================================================

def lista_bitacora(request):

    bitacoras = (
        Bitacora.objects
        .select_related('codigo_producto', 'codigo_usuario')
        .order_by('-fecha', '-hora')
    )

    bitacora_total = bitacoras.count()
    bitacora_entradas = bitacoras.filter(tipo_cambio__icontains='entrada').count()
    bitacora_salidas = bitacoras.filter(tipo_cambio__icontains='salida').count()

    context = {
        'titulo': 'Bitácora',
        'bitacoras': bitacoras,
        'bitacora_total': bitacora_total,
        'bitacora_entradas': bitacora_entradas,
        'bitacora_salidas': bitacora_salidas,
    }

    return render(
        request,
        'productos/bitacora/bitacora.html',
        context
    )


def editar_bitacora(request, pk):

    bitacora = get_object_or_404(
        Bitacora,
        pk=pk
    )

    messages.info(
        request,
        "La edición manual de bitácora está deshabilitada. "
        "Los cambios se registran automáticamente al modificar existencias."
    )

    return redirect('lista_bitacora')


# ==========================================================
# 📦 existencias
# ==========================================================

def lista_existencias(request):

    existenciass = existencias.objects.select_related(
        'codigo_producto'
    )

    existencias_total = existenciass.aggregate(
        total=Sum('cantidad_actual')
    )['total'] or 0

    existencias_critico = existenciass.filter(
        cantidad_actual__lte=5
    ).count()

    existencias_bajo = existenciass.filter(
        cantidad_actual__gt=5,
        cantidad_actual__lte=10
    ).count()

    existencias_optimo = existenciass.filter(
        cantidad_actual__gt=10
    ).count()

    stock_total = existencias_total
    stock_bajo = existenciass.filter(
        cantidad_actual__lte=10
    ).count()

    context = {
        'titulo': 'existencias',
        'existenciass': existenciass,
        'total_existencias': existencias_total,
        'stock_total': stock_total,
        'stock_bajo': stock_bajo,
        'existencias_total': existencias_total,
        'existencias_critico': existencias_critico,
        'existencias_bajo': existencias_bajo,
        'existencias_optimo': existencias_optimo,
    }

    return render(
        request,
        'productos/existencias/existencias.html',
        context
    )


def editar_existencias(request, pk):

    existencias = get_object_or_404(
        existencias,
        pk=pk
    )

    if request.method == 'POST':

        form = existenciasForm(
            request.POST,
            instance=existencias
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "existencias actualizado correctamente."
            )

            return redirect(
                'lista_existencias'
            )

    else:

        form = existenciasForm(
            instance=existencias
        )

    return render(
        request,
        'productos/existencias/editar_existencias.html',
        {
            'titulo': 'Editar existencias',
            'form': form,
            'existencias': existencias
        }
    )


# ==========================================================
# 🔄 MOVIMIENTOS DE existencias
# ==========================================================

def lista_movimientos_existencias(request):

    movimientos = (
        Movimientoexistencias.objects
        .select_related('codigo_producto')
        .order_by('-fecha')
    )

    context = {
        'titulo': 'Movimientos de existencias',
        'movimientos': movimientos,
        'total_movimientos': movimientos.count(),
        'total_entradas': movimientos.filter(tipo='entrada').count(),
        'total_salidas': movimientos.filter(tipo='salida').count(),
    }

    return render(
        request,
        'productos/existencias/movimiento_existencias.html',
        context
    )


def registrar_movimiento_existencias(request):

    if request.method == 'POST':

        producto_id = request.POST.get(
            'producto_id'
        )

        tipo = request.POST.get(
            'tipo'
        )

        try:

            cantidad = int(
                request.POST.get(
                    'cantidad',
                    1
                )
            )

        except (ValueError, TypeError):

            messages.error(
                request,
                "La cantidad no es válida."
            )

            return redirect(
                'registrar_movimiento_existencias'
            )

        motivo = request.POST.get(
            'motivo',
            ''
        )

        if cantidad <= 0:

            messages.error(
                request,
                "La cantidad debe ser mayor que cero."
            )

            return redirect(
                'registrar_movimiento_existencias'
            )

        if tipo not in [
            'entrada',
            'salida'
        ]:

            messages.error(
                request,
                "Tipo de movimiento inválido."
            )

            return redirect(
                'registrar_movimiento_existencias'
            )

        producto = get_object_or_404(
            Producto,
            codigo_producto=producto_id
        )

        with transaction.atomic():

            existencias, creado = (
                existencias.objects.get_or_create(
                    codigo_producto=producto,
                    defaults={
                        'cantidad_actual': 0
                    }
                )
            )

            if tipo == 'entrada':

                existencias.cantidad_actual += cantidad

            else:

                if (
                    cantidad >
                    existencias.cantidad_actual
                ):

                    messages.error(
                        request,
                        "No hay suficiente existencias."
                    )

                    return redirect(
                        'registrar_movimiento_existencias'
                    )

                existencias.cantidad_actual -= cantidad

            existencias.save()

            Movimientoexistencias.objects.create(
                codigo_producto=producto,
                tipo=tipo,
                cantidad=cantidad,
                observacion=motivo or 'Sin motivo'
            )

        messages.success(
            request,
            "Movimiento registrado correctamente."
        )

        return redirect(
            'lista_movimientos_existencias'
        )

    productos = Producto.objects.filter(
        estado=True
    )

    return render(
        request,
        'productos/existencias/movimiento_existencias_registar.html',
        {
            'productos': productos,
            'titulo': 'Registrar Movimiento'
        }
    )


def eliminar_movimiento_existencias(request, pk):

    movimiento = get_object_or_404(
        Movimientoexistencias,
        pk=pk
    )

    if request.method == 'POST':

        with transaction.atomic():

            existencias = get_object_or_404(
                existencias,
                codigo_producto=movimiento.codigo_producto
            )

            if movimiento.tipo == 'entrada':

                if (
                    existencias.cantidad_actual
                    < movimiento.cantidad
                ):

                    messages.error(
                        request,
                        "No se puede eliminar este "
                        "movimiento porque el existencias "
                        "actual es insuficiente."
                    )

                    return redirect(
                        'lista_movimientos_existencias'
                    )

                existencias.cantidad_actual -= (
                    movimiento.cantidad
                )

            elif movimiento.tipo == 'salida':

                existencias.cantidad_actual += (
                    movimiento.cantidad
                )

            existencias.save()

            movimiento.delete()

        messages.success(
            request,
            "Movimiento eliminado correctamente."
        )

    return redirect(
        'lista_movimientos_existencias'
    )


# ==========================================================
# 📥 ADQUISICIONES
# ==========================================================

def lista_adquisiciones(request):

    adquisiciones = (
        Adquisicion.objects
        .select_related(
            'codigo_proveedor',
            'codigo_producto'
        )
        .order_by('-fecha')
    )

    total_adquisiciones = adquisiciones.count()
    total_unidades = adquisiciones.aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    valor_total = adquisiciones.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0')

    return render(
        request,
        'productos/compras/adquisicion.html',
        {
            'adquisiciones': adquisiciones,
            'titulo': 'Adquisiciones',
            'total_adquisiciones': total_adquisiciones,
            'total_unidades': total_unidades,
            'valor_total': valor_total,
        }
    )


def registrar_adquisicion(request):

    if request.method == 'POST':

        proveedor_id = request.POST.get(
            'proveedor_id'
        )

        producto_id = request.POST.get(
            'producto_id'
        )

        try:

            cantidad = int(
                request.POST.get(
                    'cantidad',
                    1
                )
            )

            cantidad_venta = int(
                request.POST.get(
                    'cantidad_venta',
                    0
                )
            )

            precio_compra = Decimal(
                request.POST.get(
                    'precio_compra',
                    '0.00'
                )
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation
        ):

            messages.error(
                request,
                "Los datos de la adquisición "
                "no son válidos."
            )

            return redirect(
                'registrar_adquisicion'
            )

        if cantidad <= 0:

            messages.error(
                request,
                "La cantidad debe ser mayor que cero."
            )

            return redirect(
                'registrar_adquisicion'
            )

        if precio_compra < 0:

            messages.error(
                request,
                "El precio de compra no puede ser negativo."
            )

            return redirect(
                'registrar_adquisicion'
            )

        proveedor = get_object_or_404(
            Proveedor,
            pk=proveedor_id
        )

        producto = get_object_or_404(
            Producto,
            codigo_producto=producto_id
        )

        total = (
            Decimal(cantidad) *
            precio_compra
        )

        with transaction.atomic():

            adquisicion_obj = (
                Adquisicion.objects.create(
                    codigo_proveedor=proveedor,
                    codigo_producto=producto,
                    cantidad=cantidad,
                    cantidad_venta=cantidad_venta,
                    precio_compra=precio_compra,
                    total=total,
                )
            )

            # Actualizar precio del producto si hay cantidad_venta
            if cantidad_venta > 0:
                producto.precio = cantidad_venta
                producto.save(update_fields=['precio'])

            existencias, creado = (
                existencias.objects.get_or_create(
                    codigo_producto=producto,
                    defaults={
                        'cantidad_actual': 0,
                        'stock_min': 0,
                        'stock_max': 0,
                    }
                )
            )

            existencias.cantidad_actual += cantidad
            existencias.save(update_fields=['cantidad_actual'])

            Movimientoexistencias.objects.create(
                codigo_producto=producto,
                tipo='entrada',
                cantidad=cantidad,
                observacion=(
                    f"Adquisición #{adquisicion_obj.pk} "
                    f"a {proveedor.nombre}"
                )
            )

        messages.success(
            request,
            "Adquisición registrada con éxito."
        )

        return redirect(
            'lista_adquisiciones'
        )

    context = {
        'proveedores': Proveedor.objects.all(),
        'productos': Producto.objects.filter(
            estado=True
        ),
        'titulo': 'Registrar Adquisición'
    }

    return render(
        request,
        'productos/compras/crear_adquisicion.html',
        context
    )


def editar_adquisicion(request, pk):

    adquisicion_obj = get_object_or_404(
        Adquisicion,
        pk=pk
    )

    if request.method == 'POST':

        try:

            nueva_cantidad = int(
                request.POST.get(
                    'cantidad',
                    1
                )
            )

            nueva_cantidad_venta = int(
                request.POST.get(
                    'cantidad_venta',
                    0
                )
            )

            nuevo_precio = Decimal(
                request.POST.get(
                    'precio_compra',
                    '0.00'
                )
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation
        ):

            messages.error(
                request,
                "Los datos no son válidos."
            )

            return redirect(
                'editar_adquisicion',
                pk=pk
            )

        if nueva_cantidad <= 0:

            messages.error(
                request,
                "La cantidad debe ser mayor que cero."
            )

            return redirect(
                'editar_adquisicion',
                pk=pk
            )

        if nuevo_precio < 0:

            messages.error(
                request,
                "El precio no puede ser negativo."
            )

            return redirect(
                'editar_adquisicion',
                pk=pk
            )

        cantidad_anterior = (
            adquisicion_obj.cantidad
        )

        diferencia = (
            nueva_cantidad -
            cantidad_anterior
        )

        with transaction.atomic():

            existencias = get_object_or_404(
                existencias,
                codigo_producto=
                adquisicion_obj.codigo_producto
            )

            if diferencia > 0:

                existencias.cantidad_actual += (
                    diferencia
                )

            elif diferencia < 0:

                cantidad_a_restar = abs(
                    diferencia
                )

                if (
                    existencias.cantidad_actual
                    < cantidad_a_restar
                ):

                    messages.error(
                        request,
                        "No hay suficiente existencias "
                        "para reducir esta adquisición."
                    )

                    return redirect(
                        'editar_adquisicion',
                        pk=pk
                    )

                existencias.cantidad_actual -= (
                    cantidad_a_restar
                )

            existencias.save()

            adquisicion_obj.cantidad = (
                nueva_cantidad
            )

            adquisicion_obj.cantidad_venta = (
                nueva_cantidad_venta
            )

            adquisicion_obj.precio_compra = (
                nuevo_precio
            )

            adquisicion_obj.total = (
                Decimal(nueva_cantidad) *
                nuevo_precio
            )

            adquisicion_obj.save()

            # Actualizar precio del producto
            if nueva_cantidad_venta > 0:
                adquisicion_obj.codigo_producto.precio = nueva_cantidad_venta
                adquisicion_obj.codigo_producto.save(
                    update_fields=['precio']
                )

        messages.success(
            request,
            "Adquisición actualizada correctamente."
        )

        return redirect(
            'lista_adquisiciones'
        )

    return render(
        request,
        'productos/compras/editar_adquisicion.html',
        {
            'adquisicion': adquisicion_obj,
            'titulo': 'Editar Adquisición'
        }
    )


def eliminar_adquisicion(request, pk):

    adquisicion_obj = get_object_or_404(
        Adquisicion,
        pk=pk
    )

    if request.method == 'POST':

        with transaction.atomic():

            existencias = get_object_or_404(
                existencias,
                codigo_producto=
                adquisicion_obj.codigo_producto
            )

            if (
                existencias.cantidad_actual
                < adquisicion_obj.cantidad
            ):

                messages.error(
                    request,
                    "No se puede eliminar la adquisición "
                    "porque el existencias actual es menor "
                    "que la cantidad adquirida."
                )

                return redirect(
                    'lista_adquisiciones'
                )

            existencias.cantidad_actual -= (
                adquisicion_obj.cantidad
            )

            existencias.save()

            Movimientoexistencias.objects.create(
                producto=
                adquisicion_obj.codigo_producto,
                tipo='salida',
                cantidad=
                adquisicion_obj.cantidad,
                motivo=(
                    f"Reversión de adquisición "
                    f"#{adquisicion_obj.pk}"
                )
            )

            adquisicion_obj.delete()

        messages.success(
            request,
            "Adquisición eliminada correctamente."
        )

    return redirect(
        'lista_adquisiciones'
    )


# ==========================================================
# 🟡 VENTAS ADMIN
# ==========================================================

def registrar_venta(request):

    if request.method == 'POST':

        form_venta = ventaForm(
            request.POST
        )

        form_detalle = detalleventaForm(
            request.POST
        )

        if (
            form_venta.is_valid()
            and form_detalle.is_valid()
        ):

            nueva_venta = form_venta.save()

            detalle = form_detalle.save(
                commit=False
            )

            detalle.venta = nueva_venta

            detalle.save()

            nueva_venta.actualizar_total()

            messages.success(
                request,
                "Venta registrada exitosamente."
            )

            return redirect(
                'historial_ventas'
            )

    else:

        form_venta = ventaForm()
        form_detalle = detalleventaForm()

    context = {
        'titulo': 'Registrar Nueva Venta',
        'form_venta': form_venta,
        'form_detalle': form_detalle
    }

    return render(
        request,
        'productos/compras/registrar_compra.html',
        context
    )


def historial_ventas(request):

    ventas = (
        venta.objects
        .all()
        .order_by('-fecha')
    )

    context = {
        'titulo': 'Historial de Ventas',
        'ventas': ventas,
        'total_ventas': ventas.count(),
    }

    return render(
        request,
        'productos/ventas/ventas.html',
        context
    )


def detalle_venta(request, pk):

    venta_obj = get_object_or_404(
        venta,
        codigo_venta=pk
    )

    detalles = venta_obj.detalles.all()

    context = {
        'titulo': 'Detalle de Venta',
        'venta': venta_obj,
        'detalles': detalles,
        'total_calculado': sum(
            d.subtotal
            for d in detalles
        )
    }

    return render(
        request,
        'productos/ventas/detalle_venta.html',
        context
    )


def eliminar_venta(request, pk):

    venta_obj = get_object_or_404(
        venta,
        codigo_venta=pk
    )

    if request.method == 'POST':

        venta_obj.delete()

        messages.success(
            request,
            "Venta eliminada."
        )

    return redirect(
        'historial_ventas'
    )


# ==========================================================
# 🛒 AGREGAR AL CARRITO
# ==========================================================

def agregar_carrito(request):

    if request.method != 'POST':

        return JsonResponse({
            'ok': False
        })

    id_producto = request.POST.get(
        'id'
    )

    nombre = request.POST.get(
        'nombre'
    )

    precio = request.POST.get(
        'precio'
    )

    carrito = request.session.get(
        'carrito',
        {}
    )

    if id_producto in carrito:

        carrito[id_producto][
            'cantidad'
        ] += 1

    else:

        carrito[id_producto] = {
            'nombre': nombre,
            'precio': float(precio),
            'cantidad': 1
        }

    request.session['carrito'] = carrito
    request.session.modified = True

    return JsonResponse({
        'ok': True
    })


# ==========================================================
# 🏦 DATOS BANCARIOS
# ==========================================================

@login_required
def editar_datos_banco(request):

    if not request.user.is_staff:

        messages.error(
            request,
            "No tienes permisos."
        )

        return redirect('inicio')

    datos = DatosTransferencia.get_solo()

    if request.method == 'POST':

        datos.banco = request.POST.get(
            'banco',
            ''
        ).strip()

        datos.tipo_cuenta = request.POST.get(
            'tipo_cuenta',
            ''
        ).strip()

        datos.numero_cuenta = request.POST.get(
            'numero_cuenta',
            ''
        ).strip()

        datos.titular = request.POST.get(
            'titular',
            ''
        ).strip()

        datos.instrucciones = request.POST.get(
            'instrucciones',
            ''
        ).strip()

        datos.save()

        messages.success(
            request,
            "Datos actualizados correctamente."
        )

    return render(
        request,
        'productos/banco/editar_datos_banco.html',
        {
            'titulo': 'Editar Datos Bancarios',
            'datos': datos
        }
    )


@login_required
def ver_datos_banco(request):

    return render(
        request,
        'productos/banco/ver_datos_banco.html',
        {
            'titulo': 'Datos Bancarios',
            'datos': DatosTransferencia.get_solo()
        }
    )


# ==========================================================
# 🟣 CATEGORÍAS
# ==========================================================

def crear_categoria(request):

    if request.method == 'POST':

        form = CategoriaForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Categoría creada correctamente."
            )

            return redirect(
                'lista_categorias'
            )

    else:

        form = CategoriaForm()

    return render(
        request,
        'productos/categorias/crear_categoria.html',
        {
            'form': form
        }
    )


def lista_categorias(request):

    categorias = (
        Categoria.objects
        .all()
        .order_by('nombre')
    )

    return render(
        request,
        'productos/categorias/lista_categoria.html',
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

            messages.success(
                request,
                "Categoría actualizada correctamente."
            )

            return redirect(
                'lista_categorias'
            )

    else:

        form = CategoriaForm(
            instance=categoria
        )

    return render(
        request,
        'productos/categorias/editar_categoria.html',
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

    messages.success(
        request,
        "Categoría eliminada."
    )

    return redirect(
        'lista_categorias'
    )


# ==========================================================
# 🟣 PROVEEDORES
# ==========================================================

def crear_proveedor(request):

    if request.method == 'POST':

        form = ProveedorForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Proveedor creado correctamente."
            )

            return redirect(
                'lista_proveedores'
            )

    else:

        form = ProveedorForm()

    return render(
        request,
        'productos/proveedores/crear_proveedor.html',
        {
            'form': form
        }
    )


def lista_proveedores(request):

    proveedores = (
        Proveedor.objects
        .all()
        .order_by('nombre')
    )

    return render(
        request,
        'productos/proveedores/lista_proveedores.html',
        {
            'titulo': 'Proveedores',
            'proveedores': proveedores
        }
    )


def editar_proveedor(request, id):

    proveedor = get_object_or_404(
        Proveedor,
        codigo=id
    )

    if request.method == 'POST':

        form = ProveedorForm(
            request.POST,
            instance=proveedor
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Proveedor actualizado correctamente."
            )

            return redirect(
                'lista_proveedores'
            )

    else:

        form = ProveedorForm(
            instance=proveedor
        )

    return render(
        request,
        'productos/proveedores/editar_proveedor.html',
        {
            'form': form,
            'proveedor': proveedor
        }
    )


def eliminar_proveedor(request, id):

    proveedor = get_object_or_404(
        Proveedor,
        codigo=id
    )

    proveedor.delete()

    messages.success(
        request,
        "Proveedor eliminado."
    )

    return redirect(
        'lista_proveedores'
    )
    


# ==========================================================
# 🏷️ MARCAS
# ==========================================================

def lista_marcas(request):

    marcas = (
        Marca.objects
        .all()
        .prefetch_related('productos')
        .order_by('nombre')
    )

    total_marcas = Marca.objects.count()
    marcas_activas = Marca.objects.filter(estado=True).count()
    marcas_inactivas = Marca.objects.filter(estado=False).count()

    return render(
        request,
        'productos/marca/marca.html',
        {
            'titulo': 'Marcas',
            'marcas': marcas,
            'total_marcas': total_marcas,
            'marcas_activas': marcas_activas,
            'marcas_inactivas': marcas_inactivas,
        }
    )


# ==========================================================
# ➕ CREAR MARCA
# ==========================================================

def crear_marca(request):

    if request.method == 'POST':

        form = MarcaForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Marca creada correctamente."
            )

            return redirect(
                'lista_marcas'
            )

    else:

        form = MarcaForm()

    return render(
        request,
        'productos/marca/crear_marca.html',
        {
            'titulo': 'Crear Marca',
            'form': form,
        }
    )


# ==========================================================
# ✏️ EDITAR MARCA
# ==========================================================

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

            messages.success(
                request,
                "Marca actualizada correctamente."
            )

            return redirect(
                'lista_marcas'
            )

    else:

        form = MarcaForm(
            instance=marca
        )

    return render(
        request,
        'productos/marca/editar_marca.html',
        {
            'titulo': 'Editar Marca',
            'form': form,
            'marca': marca,
        }
    )


def eliminar_marca(request, id):

    marca = get_object_or_404(
        Marca,
        codigo=id
    )

    if request.method == 'POST':

        marca.delete()

        messages.success(
            request,
            "Marca eliminada correctamente."
        )

        return redirect(
            'lista_marcas'
        )

    return render(
        request,
        'productos/marca/eliminar_marca.html',
        {
            'titulo': 'Eliminar Marca',
            'marca': marca,
        }
    )


