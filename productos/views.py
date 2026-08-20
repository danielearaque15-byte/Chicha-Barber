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
    Inventario,
    MovimientoInventario,
    Adquisicion,
    DatosTransferencia,
    Categoria,
    Proveedor,
    Bitacora,
)
from .forms import ventaForm,detalleventaForm,ProductoForm,InventarioForm,CategoriaForm,ProveedorForm
from core.utils import enviar_correo_venta
from facturas.models import Factura, DetalleFactura
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

    productos = Producto.objects.filter(
        estado=True
    ).select_related(
        'categoria'
    )

    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    if categoria_id and categoria_id.isdigit():
        productos = productos.filter(
            categoria_id=int(categoria_id)
        )

    context = {
        'titulo': 'Galería de Productos',
        'productos': productos,
        'categorias': Categoria.objects.all().order_by('nombre'),
    }

    return render(
        request,
        'productos/productos_galeria.html',
        context
    )


# ==========================================================
# 🛒 CARRITO
# ==========================================================

@login_required
def carrito(request):
    return render(
        request,
        'productos/carrito.html'
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
        'productos/pago.html',
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
                # INVENTARIO
                # --------------------------------------

                inventario = get_object_or_404(
                    Inventario,
                    codigo_producto=producto
                )

                if inventario.cantidad_actual < cantidad:

                    raise ValueError(
                        f"No hay suficiente inventario "
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
                        precio_venta = producto.inventario.precio_venta
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
                # DESCONTAR INVENTARIO
                # --------------------------------------

                inventario.cantidad_actual -= cantidad
                inventario.save(
                    update_fields=[
                        'cantidad_actual'
                    ]
                )

                # --------------------------------------
                # MOVIMIENTO DE INVENTARIO
                # --------------------------------------

                MovimientoInventario.objects.create(
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

    productos = Producto.objects.all()

    context = {
        'titulo': 'Lista de Productos',
        'productos': productos,
        'total_productos': Producto.total_productos(),
        'activos': Producto.total_activos(),
        'inactivos': Producto.total_inactivos(),
    }

    return render(
        request,
        'productos/productos_admin.html',
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
        'productos/crear_producto.html',
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
        'productos/editar_producto.html',
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
        'productos/bitacora.html',
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
        "Los cambios se registran automáticamente al modificar inventario."
    )

    return redirect('lista_bitacora')


# ==========================================================
# 📦 INVENTARIO
# ==========================================================

def lista_inventario(request):

    inventarios = Inventario.objects.select_related(
        'codigo_producto'
    )

    inventario_total = inventarios.aggregate(
        total=Sum('cantidad_actual')
    )['total'] or 0

    inventario_critico = inventarios.filter(
        cantidad_actual__lte=5
    ).count()

    inventario_bajo = inventarios.filter(
        cantidad_actual__gt=5,
        cantidad_actual__lte=10
    ).count()

    inventario_optimo = inventarios.filter(
        cantidad_actual__gt=10
    ).count()

    context = {
        'titulo': 'Inventario',
        'inventarios': inventarios,
        'inventario_total': inventario_total,
        'inventario_critico': inventario_critico,
        'inventario_bajo': inventario_bajo,
        'inventario_optimo': inventario_optimo,
    }

    return render(
        request,
        'productos/inventario.html',
        context
    )


def editar_inventario(request, pk):

    inventario = get_object_or_404(
        Inventario,
        pk=pk
    )

    if request.method == 'POST':

        form = InventarioForm(
            request.POST,
            instance=inventario
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Inventario actualizado correctamente."
            )

            return redirect(
                'lista_inventario'
            )

    else:

        form = InventarioForm(
            instance=inventario
        )

    return render(
        request,
        'productos/editar_inventario.html',
        {
            'titulo': 'Editar Inventario',
            'form': form,
            'inventario': inventario
        }
    )


# ==========================================================
# 🔄 MOVIMIENTOS DE INVENTARIO
# ==========================================================

def lista_movimientos_inventario(request):

    movimientos = (
        MovimientoInventario.objects
        .select_related('codigo_producto')
        .order_by('-fecha')
    )

    context = {
        'titulo': 'Movimientos de Inventario',
        'movimientos': movimientos,
        'total_movimientos': movimientos.count(),
        'total_entradas': movimientos.filter(tipo='entrada').count(),
        'total_salidas': movimientos.filter(tipo='salida').count(),
    }

    return render(
        request,
        'productos/movimiento_inventario.html',
        context
    )


def registrar_movimiento_inventario(request):

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
                'registrar_movimiento_inventario'
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
                'registrar_movimiento_inventario'
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
                'registrar_movimiento_inventario'
            )

        producto = get_object_or_404(
            Producto,
            codigo_producto=producto_id
        )

        with transaction.atomic():

            inventario, creado = (
                Inventario.objects.get_or_create(
                    codigo_producto=producto,
                    defaults={
                        'cantidad_actual': 0
                    }
                )
            )

            if tipo == 'entrada':

                inventario.cantidad_actual += cantidad

            else:

                if (
                    cantidad >
                    inventario.cantidad_actual
                ):

                    messages.error(
                        request,
                        "No hay suficiente inventario."
                    )

                    return redirect(
                        'registrar_movimiento_inventario'
                    )

                inventario.cantidad_actual -= cantidad

            inventario.save()

            MovimientoInventario.objects.create(
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
            'lista_movimientos_inventario'
        )

    productos = Producto.objects.filter(
        estado=True
    )

    return render(
        request,
        'productos/movimiento_inventario_registar.html',
        {
            'productos': productos,
            'titulo': 'Registrar Movimiento'
        }
    )


def eliminar_movimiento_inventario(request, pk):

    movimiento = get_object_or_404(
        MovimientoInventario,
        pk=pk
    )

    if request.method == 'POST':

        with transaction.atomic():

            inventario = get_object_or_404(
                Inventario,
                codigo_producto=movimiento.codigo_producto
            )

            if movimiento.tipo == 'entrada':

                if (
                    inventario.cantidad_actual
                    < movimiento.cantidad
                ):

                    messages.error(
                        request,
                        "No se puede eliminar este "
                        "movimiento porque el inventario "
                        "actual es insuficiente."
                    )

                    return redirect(
                        'lista_movimientos_inventario'
                    )

                inventario.cantidad_actual -= (
                    movimiento.cantidad
                )

            elif movimiento.tipo == 'salida':

                inventario.cantidad_actual += (
                    movimiento.cantidad
                )

            inventario.save()

            movimiento.delete()

        messages.success(
            request,
            "Movimiento eliminado correctamente."
        )

    return redirect(
        'lista_movimientos_inventario'
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

    return render(
        request,
        'productos/adquisicion.html',
        {
            'adquisiciones': adquisiciones,
            'titulo': 'Adquisiciones'
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
                    precio_compra=precio_compra,
                    total=total,
                    fecha=request.POST.get('fecha')
                )
            )

            inventario, creado = (
                Inventario.objects.get_or_create(
                    codigo_producto=producto,
                    defaults={
                        'cantidad_actual': 0
                    }
                )
            )

            inventario.cantidad_actual += cantidad

            inventario.save()

            MovimientoInventario.objects.create(
                producto=producto,
                tipo='entrada',
                cantidad=cantidad,
                motivo=(
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
        'productos/crear_adquisicion.html',
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

            inventario = get_object_or_404(
                Inventario,
                codigo_producto=
                adquisicion_obj.codigo_producto
            )

            if diferencia > 0:

                inventario.cantidad_actual += (
                    diferencia
                )

            elif diferencia < 0:

                cantidad_a_restar = abs(
                    diferencia
                )

                if (
                    inventario.cantidad_actual
                    < cantidad_a_restar
                ):

                    messages.error(
                        request,
                        "No hay suficiente inventario "
                        "para reducir esta adquisición."
                    )

                    return redirect(
                        'editar_adquisicion',
                        pk=pk
                    )

                inventario.cantidad_actual -= (
                    cantidad_a_restar
                )

            inventario.save()

            adquisicion_obj.cantidad = (
                nueva_cantidad
            )

            adquisicion_obj.precio_compra = (
                nuevo_precio
            )

            adquisicion_obj.total = (
                Decimal(nueva_cantidad) *
                nuevo_precio
            )

            adquisicion_obj.save()

        messages.success(
            request,
            "Adquisición actualizada correctamente."
        )

        return redirect(
            'lista_adquisiciones'
        )

    return render(
        request,
        'productos/editar_adquisicion.html',
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

            inventario = get_object_or_404(
                Inventario,
                codigo_producto=
                adquisicion_obj.codigo_producto
            )

            if (
                inventario.cantidad_actual
                < adquisicion_obj.cantidad
            ):

                messages.error(
                    request,
                    "No se puede eliminar la adquisición "
                    "porque el inventario actual es menor "
                    "que la cantidad adquirida."
                )

                return redirect(
                    'lista_adquisiciones'
                )

            inventario.cantidad_actual -= (
                adquisicion_obj.cantidad
            )

            inventario.save()

            MovimientoInventario.objects.create(
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
        'productos/registrar_compra.html',
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
        'productos/ventas.html',
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
        'productos/detalle_venta.html',
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
        'productos/editar_datos_banco.html',
        {
            'titulo': 'Editar Datos Bancarios',
            'datos': datos
        }
    )


@login_required
def ver_datos_banco(request):

    return render(
        request,
        'productos/ver_datos_banco.html',
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
        'productos/crear_categoria.html',
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
        'productos/lista_categoria.html',
        {
            'titulo': 'Categorías',
            'categorias': categorias
        }
    )


def editar_categoria(request, id):

    categoria = get_object_or_404(
        Categoria,
        id=id
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
        'productos/editar_categoria.html',
        {
            'form': form,
            'categoria': categoria
        }
    )


def eliminar_categoria(request, id):

    categoria = get_object_or_404(
        Categoria,
        id=id
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
        'productos/crear_proveedor.html',
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
        'productos/lista_proveedores.html',
        {
            'titulo': 'Proveedores',
            'proveedores': proveedores
        }
    )


def editar_proveedor(request, id):

    proveedor = get_object_or_404(
        Proveedor,
        id=id
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
        'productos/editar_proveedor.html',
        {
            'form': form,
            'proveedor': proveedor
        }
    )


def eliminar_proveedor(request, id):

    proveedor = get_object_or_404(
        Proveedor,
        id=id
    )

    proveedor.delete()

    messages.success(
        request,
        "Proveedor eliminado."
    )

    return redirect(
        'lista_proveedores'
    )