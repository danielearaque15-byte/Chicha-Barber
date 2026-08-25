from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum

from catalogo.models import Proveedor, Producto
from .models import Compra, DetalleCompra


def lista_compras(request):
    compras = (
        Compra.objects
        .select_related('codigo_proveedor')
        .prefetch_related('detalles__codigo_producto')
        .order_by('-fecha')
    )

    total_compras = compras.count()
    total_unidades = DetalleCompra.objects.aggregate(total=Sum('cantidad'))['total'] or 0
    valor_total = compras.aggregate(total=Sum('total'))['total'] or Decimal('0.00')

    return render(
        request,
        'compras/compra.html',
        {
            'compras': compras,
            'titulo': 'Compras',
            'total_compras': total_compras,
            'total_unidades': total_unidades,
            'valor_total': valor_total,
        }
    )


def registrar_compra(request):
    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        producto_id = request.POST.get('producto_id')

        try:
            cantidad = int(request.POST.get('cantidad', 1))
            precio_venta = Decimal(request.POST.get('cantidad_venta', '0.00'))
            precio_compra = Decimal(request.POST.get('precio_compra', '0.00'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, "Los datos ingresados no son válidos.")
            return redirect('registrar_compra')

        if cantidad <= 0:
            messages.error(request, "La cantidad debe ser mayor a cero.")
            return redirect('registrar_compra')

        if precio_compra < 0:
            messages.error(request, "El precio de compra no puede ser negativo.")
            return redirect('registrar_compra')

        proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
        producto = get_object_or_404(Producto, codigo_producto=producto_id)

        with transaction.atomic():
            # 1. Crear la cabecera
            compra_obj = Compra.objects.create(
                codigo_proveedor=proveedor,
                observaciones=request.POST.get('observaciones', '')
            )

            # 2. Crear el detalle (save() maneja subtotal, movimiento y stock)
            DetalleCompra.objects.create(
                codigo_compra=compra_obj,
                codigo_producto=producto,
                cantidad=cantidad,
                precio_compra=precio_compra,
                precio_venta=precio_venta
            )

            # 3. Actualizar precio del producto si se definió precio de venta
            if precio_venta > 0:
                producto.precio = precio_venta
                producto.save(update_fields=['precio'])

        messages.success(request, f"Compra #{compra_obj.codigo} registrada con éxito.")
        return redirect('lista_compras')

    context = {
        'proveedores': Proveedor.objects.all(),
        'productos': Producto.objects.filter(estado=True),
        'titulo': 'Registrar Compra'
    }
    return render(request, 'productos/compras/crear_compra.html', context)


def editar_compra(request, pk):
    compra_obj = get_object_or_404(Compra, pk=pk)
    # Suponiendo flujo de 1 detalle por compra actual
    detalle_obj = compra_obj.detalles.first()

    if request.method == 'POST':
        try:
            nueva_cantidad = int(request.POST.get('cantidad', 1))
            nuevo_precio_venta = Decimal(request.POST.get('cantidad_venta', '0.00'))
            nuevo_precio_compra = Decimal(request.POST.get('precio_compra', '0.00'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, "Los datos no son válidos.")
            return redirect('editar_compra', pk=pk)

        if nueva_cantidad <= 0 or nuevo_precio_compra < 0:
            messages.error(request, "La cantidad y precios deben ser valores válidos.")
            return redirect('editar_compra', pk=pk)

        cantidad_anterior = detalle_obj.cantidad
        diferencia = nueva_cantidad - cantidad_anterior

        with transaction.atomic():
            producto = detalle_obj.codigo_producto
            existencia = getattr(producto, 'existencias', None)

            # Validar stock si la cantidad se está reduciendo
            if diferencia < 0 and existencia:
                if existencia.cantidad_actual < abs(diferencia):
                    messages.error(
                        request,
                        "No hay suficientes existencias para reducir esta compra."
                    )
                    return redirect('editar_compra', pk=pk)

            # Ajustar existencias y registrar el movimiento correspondientes al cambio
            if existencia and diferencia != 0:
                existencia.cantidad_actual += diferencia
                existencia.save(update_fields=['cantidad_actual', 'fecha_actualizacion'])

                tipo_mov = 'entrada' if diferencia > 0 else 'salida'
                MovimientoExistencias.objects.create(
                    codigo_producto=producto,
                    tipo=tipo_mov,
                    cantidad=abs(diferencia),
                    observacion=f"Ajuste por edición en Compra #{compra_obj.codigo}"
                )

            # Actualizar detalle y recalcular
            detalle_obj.cantidad = nueva_cantidad
            detalle_obj.precio_compra = nuevo_precio_compra
            detalle_obj.precio_venta = nuevo_precio_venta
            detalle_obj.save()  # recalcula subtotal y actualiza total de la compra

            compra_obj.observaciones = request.POST.get('observaciones', compra_obj.observaciones)
            compra_obj.save(update_fields=['observaciones'])

            if nuevo_precio_venta > 0:
                producto.precio = nuevo_precio_venta
                producto.save(update_fields=['precio'])

        messages.success(request, "Compra actualizada correctamente.")
        return redirect('lista_compras')

    return render(
        request,
        'productos/compras/editar_compra.html',
        {
            'compra': compra_obj,
            'detalle': detalle_obj,
            'titulo': 'Editar Compra'
        }
    )


def eliminar_compra(request, pk):
    compra_obj = get_object_or_404(Compra, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            for detalle in compra_obj.detalles.all():
                producto = detalle.codigo_producto
                existencia = getattr(producto, 'existencias', None)

                if existencia:
                    if existencia.cantidad_actual < detalle.cantidad:
                        messages.error(
                            request,
                            f"No se puede anular la compra. El producto '{producto.nombre}' tiene menos stock del ingresado."
                        )
                        return redirect('lista_compras')

                    # Revertir stock
                    existencia.cantidad_actual -= detalle.cantidad
                    existencia.save(update_fields=['cantidad_actual', 'fecha_actualizacion'])

                    # Registrar la salida por reversión
                    MovimientoExistencias.objects.create(
                        codigo_producto=producto,
                        tipo='salida',
                        cantidad=detalle.cantidad,
                        observacion=f"Reversión por anulación de Compra #{compra_obj.codigo}"
                    )

            # Eliminar la compra elimina sus detalles en cascada (on_delete=CASCADE)
            compra_obj.delete()

        messages.success(request, "Compra anula y eliminada correctamente.")

    return redirect('lista_compras')