import json
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Factura 

# --- CORRECCIÓN DE IMPORTACIONES ---
from django.contrib.auth import get_user_model
Cliente = get_user_model() 

from productos.models import Producto    
from servicios.models import Servicios    
from servicios.models import Promocion
from reservas.models import Reserva 


# =========================
# FACTURAS CLIENTE (MODIFICADA: SOLO ÚLTIMA FACTURA)
# =========================
@login_required
def facturas(request):
    facturas = (
        request.user.facturas
        .prefetch_related(
            'detalles__producto',
            'detalles__reserva__servicio'
        )
        .select_related('cliente')
        .order_by('-fecha_emision')[:1]
    )

    context = {
        'titulo': 'Mis ventas Recientes',
        'facturas': facturas,
    }

    return render(request, 'facturas/factura.html', context)


def factura_adm(request):
    facturas = (
        Factura.objects
        .all()
        .select_related('cliente')
        .prefetch_related(
            'detalles__producto',
            'detalles__reserva__servicio'
        )
        .order_by('-fecha_emision')
    )

    query = request.GET.get('q')

    if query:
        query = query.strip()

        filtros = (
            Q(cliente__first_name__icontains=query) |
            Q(cliente__last_name__icontains=query) |
            Q(cliente__email__icontains=query) |
            Q(nombre_cliente__icontains=query) |
            Q(correo_cliente__icontains=query)
        )

        for formato in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
            try:
                fecha_objeto = datetime.strptime(query, formato).date()
                filtros |= Q(fecha_emision__date=fecha_objeto)
                break
            except ValueError:
                pass

        facturas = facturas.filter(filtros)

    context = {
        'facturas': facturas,
        'productos': Producto.objects.all(),
        'servicios': Servicios.objects.all(),
    }

    return render(request, 'facturas/factura-adm.html', context)


def crear_factura(request):
    if request.method == 'POST':
        # tu código POST sin cambios
        pass

    context = {
        'titulo': 'Crear nueva venta',
        'clientes': Cliente.objects.all(),
        'servicios': Servicios.objects.all(),
        'productos': Producto.objects.all(),
        'promociones': Promocion.objects.all(),
    }

    return render(request, 'facturas/crear-factura.html', context)


def detalle_factura(request, id):
    factura = get_object_or_404(
        Factura.objects.prefetch_related(
            'detalles__producto',
            'detalles__reserva__servicio'
        ).select_related('cliente'),
        id=id
    )

    context = {
        'titulo': 'Detalle de la venta',
        'factura': factura,
    }

    return render(request, 'facturas/detalle-factura.html', context)


def imprimir_factura(request, id):
    factura = get_object_or_404(
        Factura.objects.prefetch_related(
            'detalles__producto',
            'detalles__reserva__servicio'
        ).select_related('cliente'),
        id=id
    )

    context = {
        'titulo': 'Imprimir venta',
        'factura': factura,
    }

    return render(request, 'facturas/imprimir-factura.html', context)

# =========================
# ACTUALIZAR FACTURA 
# =========================
@csrf_protect
def actualizar_factura_adm(request, id):
    if request.method == 'POST':
        try:
            factura = get_object_or_404(Factura, id=id)

            if 'imagen_transaccion' in request.FILES:
                factura.imagen_transaccion = request.FILES['imagen_transaccion']
                factura.save()
                return JsonResponse({'status': 'success'})

            else:
                data = json.loads(request.body)
                
                if data.get('accion') == 'agregar_item':
                    tipo = data.get('tipo_item')
                    cantidad = int(data.get('cantidad', 1))
                    precio_u = data.get('precio_unitario')

                    if tipo == 'producto':
                        prod_id = data.get('producto_id')
                        producto = get_object_or_404(Producto, id=prod_id)
                        factura.detalles.create(
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=float(precio_u) if precio_u else float(producto.bitacora.precio_venta)
                        )
                    
                    elif tipo == 'servicio':
                        serv_id = data.get('servicio_id')
                        prom_id = data.get('promocion_id')
                        servicio = get_object_or_404(Servicios, id=serv_id)
                        precio_final = float(precio_u) if precio_u else float(servicio.precio)
                        
                        if prom_id:
                            promocion = get_object_or_404(Promocion, id=prom_id)
                            precio_final -= (precio_final * float(promocion.porcentaje_descuento)) / 100

                        reserva_nueva = Reserva.objects.create(
                            cliente=factura.cliente,
                            nombre_cliente=factura.nombre_cliente or factura.cliente.get_full_name(),
                            correo_cliente=factura.correo_cliente or factura.cliente.email,
                            telefono_cliente=factura.telefono_cliente or getattr(factura.cliente, 'telefono', ''),
                            servicio=servicio,
                            precio_historico=precio_final,
                            fecha_reserva=timezone.now(),
                            estado='confirmada',
                            turno=None
                        )
                        factura.detalles.create(reserva=reserva_nueva, cantidad=cantidad, precio_unitario=precio_final)

                    factura.actualizar_total()
                    return JsonResponse({'status': 'success'})

                if 'estado' in data: factura.estado = data['estado']
                if 'metodo_pago' in data: factura.metodo_pago = data['metodo_pago']
                    
                factura.save()
                return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'invalid method'}, status=405)