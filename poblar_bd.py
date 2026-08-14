import os
import django
import random
import requests
from io import BytesIO
from django.core.files.base import ContentFile 
from django.utils import timezone
from datetime import datetime, date, time, timedelta

# 1. Configurar el entorno de Django para poder usar sus modelos desde este script externo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 2. Importar los modelos
from usuarios.models import Usuario
import servicios.models
from servicios.models import Servicios, Promocion, Calificacion
from reservas.models import Reserva, Turno
from productos.models import (
    Producto,
    Inventario,
    Bitacora,
    MovimientoInventario,
    Adquisicion,
    venta,
    detalleventa,
    Categoria,
    Proveedor,
)
from facturas.models import Factura, DetalleFactura

def limpiar_datos():
    print("Limpiando datos anteriores...")
    # Orden para evitar conflictos de FK con el modelo actual
    DetalleFactura.objects.all().delete()
    Factura.objects.all().delete()
    detalleventa.objects.all().delete()
    venta.objects.all().delete()
    MovimientoInventario.objects.all().delete()
    Bitacora.objects.all().delete()
    Adquisicion.objects.all().delete()
    Inventario.objects.all().delete()
    Producto.objects.all().delete()
    Categoria.objects.all().delete()
    Proveedor.objects.all().delete()
    servicios.models.Calificacion.objects.all().delete()
    Reserva.objects.all().delete()
    Turno.objects.all().delete()
    servicios.models.Promocion.objects.all().delete()
    servicios.models.Servicios.objects.all().delete()
    Usuario.objects.exclude(is_superuser=True).delete()

def descargar_avatar(nombre_completo, email):
    """Descarga un avatar de ejemplo usando UI Avatars API."""
    try:
        # Usar UI Avatars para generar un avatar basado en el nombre
        # Los avatares son generados automáticamente con colores consistentes
        url = f"https://ui-avatars.com/api/?name={nombre_completo.replace(' ', '+')}&background=random&size=200"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            # Crear nombre de archivo único basado en el email
            filename = f"barbero_{email.split('@')[0]}_avatar.png"
            return filename, ContentFile(response.content)
        else:
            print(f"  ⚠️ No se pudo descargar avatar para {nombre_completo}")
            return None, None
    except Exception as e:
        print(f"  ⚠️ Error descargando avatar para {nombre_completo}: {e}")
        return None, None

def poblar_usuarios():
    print("Poblando Usuarios...")
    nombres_barberos = [
        'Carlos López', 'Juan García',
    ]
    
    # Crear barberos con nombres específicos
    for idx, nombre_completo in enumerate(nombres_barberos[:2]):  # Reducido a 2 barberos
        nombre, apellido = nombre_completo.split()
        email = f"barbero{idx+1}@ejemplo.com"
        
        if not Usuario.objects.filter(email=email).exists():
            usuario = Usuario.objects.create_user(
                username=f"200000000{idx+1}",
                email=email,
                password="Password123!",
                first_name=nombre,
                last_name=apellido,
                telefono=f"310123456{idx}",
                rol='barbero',
                is_staff=True
            )
            
            # Descargar e asignar avatar
            filename, content = descargar_avatar(nombre_completo, email)
            if filename and content:
                usuario.foto_perfil.save(filename, content, save=True)
                print(f"  ✓ Avatar asignado a {nombre_completo}")
            else:
                print(f"  ⚠️ No se pudo asignar avatar a {nombre_completo}")
    
    # Crear otros usuarios (clientes y admin)
    for i in range(1, 7):  # 6 usuarios más
        email = f"usuario{i}@ejemplo.com"
        if not Usuario.objects.filter(email=email).exists():
            rol_asignado = 'cliente' if i < 5 else 'admin'
            Usuario.objects.create_user(
                username=f"100000000{i}",
                email=email,
                password="Password123!",
                first_name=f"NombrePrueba{i}",
                last_name=f"ApellidoPrueba{i}",
                telefono=f"30012345{i:02d}",
                rol=rol_asignado,
                is_staff=(rol_asignado == 'admin'),
                is_superuser=(rol_asignado == 'admin')
            )
            
    # Crear usuario específico solicitado por el usuario
    email_custom = "a@b.com"
    username_custom = "0000000000"
    if not Usuario.objects.filter(email=email_custom).exists() and not Usuario.objects.filter(username=username_custom).exists():
        Usuario.objects.create_user(
            username=username_custom,
            email=email_custom,
            password="@dmin123",
            first_name="Admin",
            last_name="Chicha",
            telefono="3000000000",
            rol="admin",
            is_staff=True,
            is_superuser=True
        )

def poblar_servicios():
    print("Poblando Servicios...")
    nombres_servicios = [
        'Corte Clásico', 'Degradado (Fade)', 'Arreglo de Barba', 
        'Corte + Barba', 'Tinte Capilar', 'Perfilado de Cejas', 
        'Corte Niño', 'Masaje Facial', 'Tratamiento Capilar', 'Limpieza Facial'
    ]
    
    for nombre in nombres_servicios:
        servicios.models.Servicios.objects.get_or_create(
            nombre=nombre,
            defaults={
                'precio': random.randint(20, 50) * 1000, # Ajustado: 20k - 50k
                'duracion': random.choice([30, 45, 60, 90]),
                'descripcion': f'Descripción detallada y profesional para el servicio de {nombre}.'
            }
        )

def poblar_promociones():
    print("Poblando Promociones...")
    lista_servicios = list(servicios.models.Servicios.objects.all())
    if not lista_servicios:
        print("  ⚠️ No se pueden crear promociones porque no hay servicios en la base de datos.")
        return

    for i in range(1, 11):
        servicios.models.Promocion.objects.get_or_create(
            nombre=f"Promo Especial {i}",
            defaults={
                'servicio': random.choice(lista_servicios),
                'porcentaje_descuento': random.choice([10, 15, 20, 25, 50]),
                'duracion': f"{random.choice([1, 2, 3])} Semanas",
                'descripcion': f"Aprovecha esta increíble promoción número {i} por tiempo limitado."
            }
        )

def poblar_turnos_disponibles():
    print("Poblando Turnos Disponibles...")
    barberos = list(Usuario.objects.filter(rol='barbero'))
    if not barberos:
        print("  ⚠️ No hay barberos registrados para crear turnos.")
        return

    # Generar turnos para los próximos 14 días
    for i in range(1, 15): # Para los próximos 14 días
        fecha_turno = date.today() + timedelta(days=i)
        
        # Evitar crear turnos en domingo si no se trabaja
        if fecha_turno.weekday() == 6: # 6 es domingo
            continue

        for barbero in barberos:
            # Crear 5 turnos por barbero por día
            for _ in range(5):
                hora_inicio_int = random.randint(8, 17) # Horas entre 8 AM y 5 PM
                hora_inicio = time(hour=hora_inicio_int, minute=random.choice([0, 30]))
                hora_fin = time(hour=hora_inicio_int + 1, minute=random.choice([0, 30]))

                # Asegurarse de que la hora de fin sea posterior a la de inicio
                if hora_fin <= hora_inicio:
                    hora_fin = time(hour=hora_inicio.hour + 1, minute=hora_inicio.minute)

                Turno.objects.get_or_create(
                    profesional=barbero,
                    fecha=fecha_turno,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    estado='disponible' # Aseguramos que estos turnos estén disponibles
                )

def poblar_reservas():
    print("Poblando Reservas...")
    estados_reserva = ['reservada', 'confirmada', 'cancelada']
    estados_turno = ['disponible', 'reservado', 'cancelado']
    
    servicios_disponibles = list(servicios.models.Servicios.objects.all())
    if not servicios_disponibles:
        print("  ⚠️ No se pueden crear reservas porque no hay servicios en la base de datos.")
        return

    barberos = list(Usuario.objects.filter(rol='barbero'))
    clientes = list(Usuario.objects.filter(rol='cliente'))
    
    if not barberos or not clientes:
        print("  ⚠️ Faltan barberos o clientes registrados para crear turnos y reservas.")
        return

    for i in range(1, 6): # Crear menos reservas para dejar más turnos disponibles
        # Crear fechas con date objects
        dias_adelante = random.randint(1, 7)
        fecha_turno = date.today() + timedelta(days=dias_adelante)
        hora_inicio = time(hour=random.randint(8, 17), minute=0)
        hora_fin = time(hour=random.randint(9, 18), minute=0)
        
        turno = Turno.objects.create(
            profesional=random.choice(barberos),
            fecha=fecha_turno,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado=random.choice(estados_turno)
        )

        servicio_asignado = random.choice(servicios_disponibles)
        Reserva.objects.create(
            turno=turno,
            cliente=random.choice(clientes),
            servicio=servicio_asignado,
            precio_historico=servicio_asignado.precio,
            estado=random.choice(estados_reserva)
        )

def poblar_calificaciones_servicios():
    print("Poblando Calificaciones de Servicios...")
    servicios = list(Servicios.objects.all())
    clientes = ["Andrés Pérez", "Marina Soler", "Kevin Duarte", "Lucía Rivas"]
    comentarios = [
        "Excelente servicio, muy profesional.",
        "Me gustó mucho el corte, volveré.",
        "Un poco demorado pero el resultado fue genial.",
        "La mejor barbería de la ciudad.",
        "Muy buena atención al cliente."
    ]

    for servicio in servicios:
        for _ in range(random.randint(1, 3)):
            Calificacion.objects.create(
                servicio=servicio,
                cliente=random.choice(clientes),
                puntuacion=random.randint(3, 5),
                comentario=random.choice(comentarios)
            )

def poblar_productos_y_bitacora():
    print("Poblando Productos, inventario y bitácora...")

    # --- Crear Categorías ---
    print("  Creando Categorías...")
    categorias_data = [
        {'nombre': 'Cuidado Capilar', 'descripcion': 'Productos para el cuidado del cabello'},
        {'nombre': 'Barba y Afeitado', 'descripcion': 'Productos para barba y afeitado profesional'},
        {'nombre': 'Accesorios', 'descripcion': 'Peines, brochas y otros accesorios'},
    ]
    categorias = []
    for cat_data in categorias_data:
        cat, _ = Categoria.objects.get_or_create(nombre=cat_data['nombre'], defaults=cat_data)
        categorias.append(cat)

    # --- Crear Proveedores ---
    print("  Creando Proveedores...")
    proveedores_data = [
        {'nombre': 'Distribuidora Barber Pros', 'telefono': '3112345678', 'correo': 'ventas@barberpros.com', 'direccion': 'Cra 45 # 20-30'},
        {'nombre': 'Suministros Estilo Total', 'telefono': '3223456789', 'correo': 'info@estilototal.com', 'direccion': 'Cll 10 # 5-40'},
    ]
    proveedores = []
    for prov_data in proveedores_data:
        prov, _ = Proveedor.objects.get_or_create(nombre=prov_data['nombre'], defaults=prov_data)
        proveedores.append(prov)

    nombres_productos = [
        'Cera Moldeadora', 'Aceite para Barba', 'Gel Fijador',
        'Shampoo de Cuidado', 'Navaja Profesional', 'Brocha de Afeitar',
        'Tónico Capilar', 'Peine de Madera', 'Bálsamo Hidratante', 'Aftershave'
    ]

    try:
        for nombre in nombres_productos:
            producto, created = Producto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': f'Producto de alta calidad para barbería: {nombre}.',
                    'codigo_categoria': random.choice(categorias),
                    'estado': True,
                }
            )

            if not created and not producto.codigo_categoria:
                producto.codigo_categoria = random.choice(categorias)
                producto.save(update_fields=['codigo_categoria'])

            inventario, _ = Inventario.objects.get_or_create(
                codigo_producto=producto,
                defaults={
                    'cantidad_actual': random.randint(15, 50),
                    'stock_min': random.randint(5, 10),
                    'stock_max': random.randint(40, 80),
                    'observaciones': 'Inventario cargado automáticamente por poblar_bd.',
                }
            )

            if not producto.codigo_inventario_id:
                producto.codigo_inventario = inventario
                producto.save(update_fields=['codigo_inventario'])

            inventario.cantidad_actual = random.randint(15, 60)
            inventario.stock_min = random.randint(5, 10)
            inventario.stock_max = random.randint(50, 100)
            inventario.save(update_fields=['cantidad_actual', 'stock_min', 'stock_max', 'fecha_actualizacion'])

            Bitacora.objects.create(
                codigo_inventario=inventario,
                codigo_producto=producto,
                codigo_usuario=None,
                tipo_cambio='entrada',
                campo_actualizado='cantidad_actual',
                valor_anterior='0',
                valor_actual=str(inventario.cantidad_actual),
                motivo='Carga inicial',
                observaciones='Registro generado por poblar_bd.',
            )
    except Exception as e:
        print(f"  ⚠️ Error al poblar productos/inventario/bitácora: {e}")

def poblar_ventas():
    print("Poblando ventas...")
    try:
        productos = list(Producto.objects.all())
        if not productos:
            print("  ⚠️ No se pueden crear ventas porque no hay productos.")
            return

        clientes = list(Usuario.objects.filter(rol='cliente'))
        if not clientes:
            clientes = [Usuario.objects.order_by('id').first()] if Usuario.objects.exists() else []

        for i in range(1, 11):
            cliente = random.choice(clientes) if clientes else None
            venta_obj = venta.objects.create(
                codigo_usuario=cliente,
                nombre_cliente=f"Cliente Prueba {i}",
                correo=f"ventador{i}@correo.com",
                telefono=f"30099900{i:02d}",
                direccion=f"Carrera {i} # {i}-{i*2}",
                metodo_pago=random.choice(['persona', 'contraentrega', 'transferencia']),
                estado_pago='completado',
            )

            detalle = detalleventa.objects.create(
                codigo_venta=venta_obj,
                codigo_producto=random.choice(productos),
                cantidad=random.randint(1, 3),
                valor_descuento=0,
            )

            venta_obj.actualizar_total()
            if detalle.codigo_movimiento_producto:
                detalle.codigo_movimiento_producto.observacion = (
                    f"Venta Online #{venta_obj.codigo_venta}"
                )
                detalle.codigo_movimiento_producto.save(update_fields=['observacion'])
    except Exception as e:
        print(f"  ⚠️ Error al poblar ventas: {e}")

def poblar_calificaciones():
    print("Poblando Calificaciones de Usuarios...")
    servicios_disponibles = list(servicios.models.Servicios.objects.all())
    clientes_disponibles = list(Usuario.objects.filter(rol='cliente'))

    if not servicios_disponibles:
        print("  ⚠️ No se pueden crear calificaciones porque no hay servicios en la base de datos.")
        return
    if not clientes_disponibles:
        print("  ⚠️ No se pueden crear calificaciones porque no hay clientes en la base de datos.")
        return

    comentarios_ejemplo = [
        "Excelente servicio, muy profesional.",
        "Me encantó el resultado, volveré pronto.",
        "Buen trabajo, pero la espera fue un poco larga.",
        "Muy amable el personal, pero el corte no fue exactamente lo que esperaba.",
        "Increíble experiencia, 5 estrellas!",
        "Rápido y eficiente, justo lo que necesitaba.",
        "El lugar es muy agradable y el servicio impecable.",
        "Podría mejorar la atención al cliente.",
        "Relación calidad-precio muy buena.",
        "No estoy del todo satisfecho con el corte."
    ]

    for _ in range(15): # Crear 15 calificaciones
        servicio = random.choice(servicios_disponibles)
        cliente_usuario = random.choice(clientes_disponibles)
        puntuacion = random.randint(1, 5)
        comentario = random.choice(comentarios_ejemplo)

        servicios.models.Calificacion.objects.create(
            servicio=servicio,
            cliente=cliente_usuario.get_full_name() or cliente_usuario.username, # Usa el nombre completo si está disponible, sino el username
            puntuacion=puntuacion,
            comentario=comentario
        )

def poblar_facturas():
    print("Poblando Facturas...")
    reservas = Reserva.objects.all()
    productos = list(Producto.objects.all())
    clientes = list(Usuario.objects.filter(rol='cliente'))
    metodos = ['efectivo', 'nequi', 'daviplata', 'tarjeta']

    if not reservas and not productos:
        print("  ⚠️ No hay datos suficientes para generar facturas.")
        return

    # 1. Facturas para las Reservas (Citas)
    for reserva in reservas:
        factura = Factura.objects.create(
            cliente=reserva.cliente if reserva.cliente else random.choice(clientes),
            total_pagado=float(reserva.precio_historico),
            metodo_pago=random.choice(metodos),
            estado='pagada' if reserva.estado == 'confirmada' else 'pendiente',
        )
        DetalleFactura.objects.create(
            factura=factura,
            reserva=reserva,
            cantidad=1,
            precio_unitario=reserva.precio_historico,
            subtotal=reserva.precio_historico
        )

    # 2. Facturas de Venta Directa (Productos)
    for i in range(5):
        cliente = random.choice(clientes) if clientes else None
        factura = Factura.objects.create(
            cliente=cliente,
            total_pagado=0,
            metodo_pago=random.choice(metodos),
            estado='pagada'
        )
        total_acumulado = 0
        for _ in range(random.randint(1, 3)):
            prod = random.choice(productos)
            cant = random.randint(1, 2)
            precio_venta = float(random.randint(10, 50) * 1000)
            sub = precio_venta * cant
            DetalleFactura.objects.create(
                factura=factura,
                producto=prod,
                cantidad=cant,
                precio_unitario=precio_venta,
                subtotal=sub
            )
            total_acumulado += sub
        factura.total_pagado = total_acumulado
        factura.save()


if __name__ == '__main__':
    print("Iniciando la inserción de datos de prueba...")
    limpiar_datos()
    poblar_usuarios()
    poblar_servicios()
    poblar_turnos_disponibles() # Ahora sí hay barberos para los turnos
    poblar_promociones()
    poblar_reservas()
    poblar_calificaciones_servicios() 
    
    poblar_productos_y_bitacora()
    poblar_ventas()
    poblar_facturas()
    poblar_calificaciones()
    print("✅ ¡Base de datos poblada con éxito!")

