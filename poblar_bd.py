import os
import django
import random
import requests

from decimal import Decimal
from datetime import date, time, timedelta

from django.core.files.base import ContentFile


# ==========================================================
# 1. CONFIGURAR DJANGO
# ==========================================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "core.settings"
)

django.setup()


# ==========================================================
# 2. IMPORTAR MODELOS
# ==========================================================

from usuarios.models import Usuario

import servicios.models

from servicios.models import (
    Servicios,
    Promocion,
    Calificacion,
)

from reservas.models import (
    Reserva,
    Turno,
)

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
    Promocion as ProductoPromocion,
    PromocionProducto,
)

from facturas.models import (
    Factura,
    DetalleFactura,
)


# ==========================================================
# 3. LIMPIAR DATOS
# ==========================================================

def limpiar_datos():

    print("\n==========================================")
    print("LIMPIANDO DATOS ANTERIORES")
    print("==========================================")

    try:

        # ----------------------------------------------
        # FACTURAS
        # ----------------------------------------------

        DetalleFactura.objects.all().delete()
        Factura.objects.all().delete()

        # ----------------------------------------------
        # VENTAS
        # ----------------------------------------------

        detalleventa.objects.all().delete()
        venta.objects.all().delete()

        # ----------------------------------------------
        # INVENTARIO
        # ----------------------------------------------

        MovimientoInventario.objects.all().delete()
        Bitacora.objects.all().delete()
        Adquisicion.objects.all().delete()

        # ----------------------------------------------
        # PRODUCTOS
        # ----------------------------------------------

        PromocionProducto.objects.all().delete()
        ProductoPromocion.objects.all().delete()

        Inventario.objects.all().delete()
        Producto.objects.all().delete()

        Categoria.objects.all().delete()
        Proveedor.objects.all().delete()

        # ----------------------------------------------
        # SERVICIOS
        # ----------------------------------------------

        servicios.models.Calificacion.objects.all().delete()
        Reserva.objects.all().delete()
        Turno.objects.all().delete()

        servicios.models.Promocion.objects.all().delete()
        servicios.models.Servicios.objects.all().delete()

        # ----------------------------------------------
        # USUARIOS
        # ----------------------------------------------

        Usuario.objects.exclude(
            is_superuser=True
        ).delete()

        print("✓ Datos anteriores eliminados correctamente.")

    except Exception as e:

        print(
            f"⚠️ Error limpiando datos: {e}"
        )


# ==========================================================
# 4. DESCARGAR AVATAR
# ==========================================================

def descargar_avatar(
    nombre_completo,
    email
):

    """
    Descarga un avatar de ejemplo
    usando UI Avatars.
    """

    try:

        url = (
            "https://ui-avatars.com/api/"
            f"?name={nombre_completo.replace(' ', '+')}"
            "&background=random"
            "&size=200"
        )

        response = requests.get(
            url,
            timeout=5
        )

        if response.status_code == 200:

            filename = (
                f"barbero_"
                f"{email.split('@')[0]}"
                f"_avatar.png"
            )

            return (
                filename,
                ContentFile(response.content)
            )

        print(
            f"⚠️ No se pudo descargar avatar "
            f"para {nombre_completo}"
        )

        return None, None

    except Exception as e:

        print(
            f"⚠️ Error descargando avatar "
            f"para {nombre_completo}: {e}"
        )

        return None, None


# ==========================================================
# 5. POBLAR USUARIOS
# ==========================================================

def poblar_usuarios():

    print("\n==========================================")
    print("POBLANDO USUARIOS")
    print("==========================================")

    nombres_barberos = [
        "Carlos López",
        "Juan García",
    ]

    # ----------------------------------------------
    # BARBEROS
    # ----------------------------------------------

    for idx, nombre_completo in enumerate(
        nombres_barberos[:2]
    ):

        partes = nombre_completo.split()

        nombre = partes[0]
        apellido = partes[-1]

        email = (
            f"barbero{idx + 1}"
            "@ejemplo.com"
        )

        if not Usuario.objects.filter(
            email=email
        ).exists():

            usuario = Usuario.objects.create_user(

                username=(
                    f"200000000"
                    f"{idx + 1}"
                ),

                email=email,

                password="Password123!",

                first_name=nombre,

                last_name=apellido,

                telefono=(
                    f"310123456{idx}"
                ),

                rol="barbero",

                is_staff=True
            )

            filename, content = (
                descargar_avatar(
                    nombre_completo,
                    email
                )
            )

            if filename and content:

                usuario.foto_perfil.save(
                    filename,
                    content,
                    save=True
                )

                print(
                    f"✓ Avatar asignado a "
                    f"{nombre_completo}"
                )

            else:

                print(
                    f"⚠️ No se pudo asignar "
                    f"avatar a {nombre_completo}"
                )

    # ----------------------------------------------
    # CLIENTES Y ADMINS
    # ----------------------------------------------

    for i in range(1, 7):

        email = (
            f"usuario{i}"
            "@ejemplo.com"
        )

        if not Usuario.objects.filter(
            email=email
        ).exists():

            rol_asignado = (
                "cliente"
                if i < 5
                else "admin"
            )

            Usuario.objects.create_user(

                username=(
                    f"100000000{i}"
                ),

                email=email,

                password="Password123!",

                first_name=(
                    f"NombrePrueba{i}"
                ),

                last_name=(
                    f"ApellidoPrueba{i}"
                ),

                telefono=(
                    f"30012345{i:02d}"
                ),

                rol=rol_asignado,

                is_staff=(
                    rol_asignado == "admin"
                ),

                is_superuser=(
                    rol_asignado == "admin"
                )
            )

    # ----------------------------------------------
    # ADMIN ESPECÍFICO
    # ----------------------------------------------

    email_custom = "a@b.com"
    username_custom = "0000000000"

    if (
        not Usuario.objects.filter(
            email=email_custom
        ).exists()
        and
        not Usuario.objects.filter(
            username=username_custom
        ).exists()
    ):

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

    print("✓ Usuarios creados.")


# ==========================================================
# 6. POBLAR SERVICIOS
# ==========================================================

def poblar_servicios():

    print("\n==========================================")
    print("POBLANDO SERVICIOS")
    print("==========================================")

    nombres_servicios = [

        "Corte Clásico",

        "Degradado (Fade)",

        "Arreglo de Barba",

        "Corte + Barba",

        "Tinte Capilar",

        "Perfilado de Cejas",

        "Corte Niño",

        "Masaje Facial",

        "Tratamiento Capilar",

        "Limpieza Facial",
    ]

    for nombre in nombres_servicios:

        Servicios.objects.get_or_create(

            nombre=nombre,

            defaults={

                "precio": (
                    random.randint(
                        20,
                        50
                    ) * 1000
                ),

                "duracion": random.choice(
                    [30, 45, 60, 90]
                ),

                "descripcion": (
                    "Descripción detallada "
                    "y profesional para el "
                    f"servicio de {nombre}."
                ),
            }
        )

    print("✓ Servicios creados.")


# ==========================================================
# 7. POBLAR PROMOCIONES DE SERVICIOS
# ==========================================================

def poblar_promociones():

    print("\n==========================================")
    print("POBLANDO PROMOCIONES")
    print("==========================================")

    lista_servicios = list(
        Servicios.objects.all()
    )

    if not lista_servicios:

        print(
            "⚠️ No hay servicios "
            "para crear promociones."
        )

        return

    for i in range(1, 11):

        Promocion.objects.get_or_create(

            nombre=f"Promo Especial {i}",

            defaults={

                "servicio": random.choice(
                    lista_servicios
                ),

                "porcentaje_descuento": (
                    random.choice(
                        [10, 15, 20, 25, 50]
                    )
                ),

                "duracion": (
                    f"{random.choice([1, 2, 3])} "
                    "Semanas"
                ),

                "descripcion": (
                    "Aprovecha esta increíble "
                    f"promoción número {i} "
                    "por tiempo limitado."
                ),
            }
        )

    print("✓ Promociones creadas.")


# ==========================================================
# 8. POBLAR TURNOS
# ==========================================================

def poblar_turnos_disponibles():

    print("\n==========================================")
    print("POBLANDO TURNOS")
    print("==========================================")

    barberos = list(
        Usuario.objects.filter(
            rol="barbero"
        )
    )

    if not barberos:

        print(
            "⚠️ No hay barberos registrados."
        )

        return

    for i in range(1, 15):

        fecha_turno = (
            date.today()
            + timedelta(days=i)
        )

        # Domingo
        if fecha_turno.weekday() == 6:
            continue

        for barbero in barberos:

            for _ in range(5):

                hora_inicio_int = random.randint(
                    8,
                    17
                )

                minuto = random.choice(
                    [0, 30]
                )

                hora_inicio = time(
                    hour=hora_inicio_int,
                    minute=minuto
                )

                hora_fin_int = (
                    hora_inicio_int + 1
                )

                if hora_fin_int > 23:
                    continue

                hora_fin = time(
                    hour=hora_fin_int,
                    minute=minuto
                )

                Turno.objects.get_or_create(

                    profesional=barbero,

                    fecha=fecha_turno,

                    hora_inicio=hora_inicio,

                    hora_fin=hora_fin,

                    defaults={
                        "estado": "disponible"
                    }
                )

    print("✓ Turnos creados.")


# ==========================================================
# 9. POBLAR RESERVAS
# ==========================================================

def poblar_reservas():

    print("\n==========================================")
    print("POBLANDO RESERVAS")
    print("==========================================")

    estados_reserva = [
        "reservada",
        "confirmada",
        "cancelada"
    ]

    estados_turno = [
        "disponible",
        "reservado",
        "cancelado"
    ]

    servicios_disponibles = list(
        Servicios.objects.all()
    )

    barberos = list(
        Usuario.objects.filter(
            rol="barbero"
        )
    )

    clientes = list(
        Usuario.objects.filter(
            rol="cliente"
        )
    )

    if not servicios_disponibles:

        print(
            "⚠️ No hay servicios."
        )

        return

    if not barberos or not clientes:

        print(
            "⚠️ Faltan barberos o clientes."
        )

        return

    for i in range(1, 6):

        dias_adelante = random.randint(
            1,
            7
        )

        fecha_turno = (
            date.today()
            + timedelta(
                days=dias_adelante
            )
        )

        hora_inicio = time(
            hour=random.randint(
                8,
                17
            ),
            minute=0
        )

        hora_fin = time(
            hour=(
                min(
                    hora_inicio.hour + 1,
                    23
                )
            ),
            minute=0
        )

        turno = Turno.objects.create(

            profesional=random.choice(
                barberos
            ),

            fecha=fecha_turno,

            hora_inicio=hora_inicio,

            hora_fin=hora_fin,

            estado=random.choice(
                estados_turno
            )
        )

        servicio_asignado = (
            random.choice(
                servicios_disponibles
            )
        )

        Reserva.objects.create(

            turno=turno,

            cliente=random.choice(
                clientes
            ),

            servicio=servicio_asignado,

            precio_historico=(
                servicio_asignado.precio
            ),

            estado=random.choice(
                estados_reserva
            )
        )

    print("✓ Reservas creadas.")


# ==========================================================
# 10. CALIFICACIONES DE SERVICIOS
# ==========================================================

def poblar_calificaciones_servicios():

    print("\n==========================================")
    print("POBLANDO CALIFICACIONES DE SERVICIOS")
    print("==========================================")

    servicios_disponibles = list(
        Servicios.objects.all()
    )

    clientes = [
        "Andrés Pérez",
        "Marina Soler",
        "Kevin Duarte",
        "Lucía Rivas",
    ]

    comentarios = [

        "Excelente servicio, muy profesional.",

        "Me gustó mucho el corte, volveré.",

        "Un poco demorado pero el resultado fue genial.",

        "La mejor barbería de la ciudad.",

        "Muy buena atención al cliente.",
    ]

    for servicio in servicios_disponibles:

        for _ in range(
            random.randint(1, 3)
        ):

            Calificacion.objects.create(

                servicio=servicio,

                cliente=random.choice(
                    clientes
                ),

                puntuacion=random.randint(
                    3,
                    5
                ),

                comentario=random.choice(
                    comentarios
                )
            )

    print(
        "✓ Calificaciones de servicios creadas."
    )


# ==========================================================
# 11. PRODUCTOS, INVENTARIO Y BITÁCORA
# ==========================================================

def poblar_productos_y_bitacora():

    print("\n==========================================")
    print("POBLANDO PRODUCTOS E INVENTARIO")
    print("==========================================")

    # ----------------------------------------------
    # CATEGORÍAS
    # ----------------------------------------------

    categorias_data = [

        {
            "nombre": "Cuidado Capilar",
            "descripcion": (
                "Productos para el "
                "cuidado del cabello"
            )
        },

        {
            "nombre": "Barba y Afeitado",
            "descripcion": (
                "Productos para barba "
                "y afeitado profesional"
            )
        },

        {
            "nombre": "Accesorios",
            "descripcion": (
                "Peines, brochas y "
                "otros accesorios"
            )
        },
    ]

    categorias = []

    for cat_data in categorias_data:

        cat, _ = Categoria.objects.get_or_create(

            nombre=cat_data["nombre"],

            defaults=cat_data
        )

        categorias.append(cat)

    # ----------------------------------------------
    # PROVEEDORES
    # ----------------------------------------------

    proveedores_data = [

        {
            "nombre": "Distribuidora Barber Pros",
            "telefono": "3112345678",
            "correo": "ventas@barberpros.com",
            "direccion": "Cra 45 # 20-30"
        },

        {
            "nombre": "Suministros Estilo Total",
            "telefono": "3223456789",
            "correo": "info@estilototal.com",
            "direccion": "Cll 10 # 5-40"
        },
    ]

    for prov_data in proveedores_data:

        Proveedor.objects.get_or_create(

            nombre=prov_data["nombre"],

            defaults=prov_data
        )

    # ----------------------------------------------
    # PRODUCTOS
    # ----------------------------------------------

    nombres_productos = [

        "Cera Moldeadora",

        "Aceite para Barba",

        "Gel Fijador",

        "Shampoo de Cuidado",

        "Navaja Profesional",

        "Brocha de Afeitar",

        "Tónico Capilar",

        "Peine de Madera",

        "Bálsamo Hidratante",

        "Aftershave",
    ]

    productos_creados = []

    for nombre in nombres_productos:

        producto, created = (
            Producto.objects.get_or_create(

                nombre=nombre,

                defaults={

                    "descripcion": (
                        "Producto de alta calidad "
                        "para barbería: "
                        f"{nombre}."
                    ),

                    "codigo_categoria": (
                        random.choice(
                            categorias
                        )
                    ),

                    "estado": True,

                    "precio": (
                        Decimal(
                            str(
                                random.randint(
                                    15000,
                                    120000
                                )
                            )
                        )
                    ),
                }
            )
        )

        if not producto.codigo_categoria_id:

            producto.codigo_categoria = (
                random.choice(
                    categorias
                )
            )

            producto.save(
                update_fields=[
                    "codigo_categoria"
                ]
            )

        if not producto.precio:

            producto.precio = Decimal(
                str(
                    random.randint(
                        15000,
                        120000
                    )
                )
            )

            producto.save(
                update_fields=[
                    "precio"
                ]
            )

        # ------------------------------------------
        # INVENTARIO
        # ------------------------------------------

        inventario, _ = (
            Inventario.objects.get_or_create(

                codigo_producto=producto,

                defaults={

                    "cantidad_actual": random.randint(
                        15,
                        50
                    ),

                    "stock_min": random.randint(
                        5,
                        10
                    ),

                    "stock_max": random.randint(
                        40,
                        80
                    ),

                    "observaciones": (
                        "Inventario cargado "
                        "automáticamente."
                    ),
                }
            )
        )

        inventario.cantidad_actual = random.randint(
            15,
            60
        )

        inventario.stock_min = random.randint(
            5,
            10
        )

        inventario.stock_max = random.randint(
            50,
            100
        )

        inventario.save(
            update_fields=[
                "cantidad_actual",
                "stock_min",
                "stock_max",
                "fecha_actualizacion"
            ]
        )

        # ------------------------------------------
        # RELACIÓN PRODUCTO → INVENTARIO
        # ------------------------------------------

        if not producto.codigo_inventario_id:

            producto.codigo_inventario = (
                inventario
            )

            producto.save(
                update_fields=[
                    "codigo_inventario"
                ]
            )

        # ------------------------------------------
        # BITÁCORA
        # ------------------------------------------

        Bitacora.objects.create(

            codigo_inventario=inventario,

            codigo_producto=producto,

            codigo_usuario=None,

            tipo_cambio="entrada",

            campo_actualizado="cantidad_actual",

            valor_anterior="0",

            valor_actual=str(
                inventario.cantidad_actual
            ),

            motivo="Carga inicial",

            observaciones=(
                "Registro generado "
                "por poblar_bd."
            )
        )

        productos_creados.append(
            producto
        )

    print(
        f"✓ {len(productos_creados)} "
        "productos creados."
    )

    # ----------------------------------------------
    # PROMOCIONES DE PRODUCTOS
    # ----------------------------------------------

    if productos_creados:

        for i in range(1, 4):

            promocion, _ = (
                ProductoPromocion.objects
                .get_or_create(

                    nombre=(
                        f"Promo Producto {i}"
                    ),

                    defaults={

                        "porcentaje_descuento": (
                            Decimal(
                                str(
                                    random.choice(
                                        [
                                            10,
                                            15,
                                            20,
                                            25
                                        ]
                                    )
                                )
                            )
                        ),

                        "descripcion": (
                            "Promoción automática "
                            "para productos."
                        ),

                        "fecha_inicio": (
                            date.today()
                        ),

                        "fecha_fin": (
                            date.today()
                            + timedelta(
                                days=30
                            )
                        ),

                        "estado": True,
                    }
                )
            )

            producto = random.choice(
                productos_creados
            )

            # Precio base del producto
            precio = Decimal(
                str(producto.precio)
            )

            porcentaje = Decimal(
                str(
                    promocion.porcentaje_descuento
                )
            )

            valor_con_descuento = (
                precio
                *
                (
                    Decimal("1")
                    -
                    (
                        porcentaje
                        / Decimal("100")
                    )
                )
            ).quantize(
                Decimal("0.01")
            )

            PromocionProducto.objects.create(

                codigo_promocion=promocion,

                codigo_producto=producto,

                precio=precio,

                valor_con_descuento=(
                    valor_con_descuento
                ),

                estado=True
            )

    print(
        "✓ Promociones de productos creadas."
    )


# ==========================================================
# 12. POBLAR ADQUISICIONES
# ==========================================================

def poblar_adquisiciones():

    print("\n==========================================")
    print("POBLANDO ADQUISICIONES")
    print("==========================================")

    try:

        productos = list(
            Producto.objects.all()
        )

        proveedores = list(
            Proveedor.objects.all()
        )

        if not productos or not proveedores:

            print(
                "⚠️ No hay productos o "
                "proveedores suficientes."
            )

            return

        for i in range(1, 16):

            producto = random.choice(
                productos
            )

            proveedor = random.choice(
                proveedores
            )

            # ------------------------------------------
            # CANTIDAD COMPRADA
            # ------------------------------------------

            cantidad = random.randint(
                10,
                40
            )

            # ------------------------------------------
            # PRECIO DE COMPRA
            # ------------------------------------------

            precio_compra = Decimal(
                str(
                    random.randint(
                        8000,
                        35000
                    )
                )
            )

            # ------------------------------------------
            # MARGEN
            # ------------------------------------------

            margen = Decimal(
                str(
                    random.choice(
                        [
                            "1.25",
                            "1.30",
                            "1.35",
                            "1.40",
                            "1.50"
                        ]
                    )
                )
            )

            # ------------------------------------------
            # PRECIO DE VENTA
            # ------------------------------------------

            precio_venta = (
                precio_compra * margen
            ).quantize(
                Decimal("0.01")
            )

            # ------------------------------------------
            # CANTIDAD DISPONIBLE PARA VENTA
            # ------------------------------------------

            cantidad_venta = cantidad

            # ------------------------------------------
            # TOTAL
            # ------------------------------------------

            total = (
                precio_compra * cantidad
            ).quantize(
                Decimal("0.01")
            )

            # ------------------------------------------
            # CREAR ADQUISICIÓN
            # ------------------------------------------

            adquisicion = (
                Adquisicion.objects.create(

                    codigo_proveedor=proveedor,

                    codigo_producto=producto,

                    cantidad=cantidad,

                    cantidad_venta=(
                        cantidad_venta
                    ),

                    precio_compra=(
                        precio_compra
                    ),

                    precio_venta=(
                        precio_venta
                    ),

                    total=total,
                )
            )

            print(

                f"✓ Adquisición "
                f"#{adquisicion.codigo} | "

                f"{producto.nombre} | "

                f"Cantidad: {cantidad} | "

                f"Compra: "
                f"${precio_compra:,.0f} | "

                f"Venta: "
                f"${precio_venta:,.0f} | "

                f"Total: "
                f"${total:,.0f}"
            )

        print(
            "✓ Adquisiciones creadas correctamente."
        )

    except Exception as e:

        print(
            f"⚠️ Error al poblar adquisiciones: {e}"
        )


# ==========================================================
# 13. OBTENER ÚLTIMA ADQUISICIÓN
# ==========================================================

def obtener_ultima_adquisicion(producto):

    return (
        Adquisicion.objects
        .filter(
            codigo_producto=producto
        )
        .order_by(
            "-fecha",
            "-codigo"
        )
        .first()
    )


# ==========================================================
# 14. POBLAR VENTAS
# ==========================================================

def poblar_ventas():

    print("\n==========================================")
    print("POBLANDO VENTAS")
    print("==========================================")

    try:

        productos = list(
            Producto.objects.all()
        )

        clientes = list(
            Usuario.objects.filter(
                rol="cliente"
            )
        )

        if not productos:

            print(
                "⚠️ No hay productos."
            )

            return

        if not clientes:

            print(
                "⚠️ No hay clientes."
            )

            return

        # ------------------------------------------
        # PRODUCTOS CON ADQUISICIÓN
        # ------------------------------------------

        productos_con_precio = []

        for producto in productos:

            adquisicion = (
                obtener_ultima_adquisicion(
                    producto
                )
            )

            if adquisicion:

                productos_con_precio.append(
                    producto
                )

        if not productos_con_precio:

            print(
                "⚠️ No hay productos "
                "con precio de venta."
            )

            return

        # ------------------------------------------
        # CREAR 10 VENTAS
        # ------------------------------------------

        for i in range(1, 11):

            # Buscar producto con stock
            producto = None

            productos_barajados = (
                productos_con_precio.copy()
            )

            random.shuffle(
                productos_barajados
            )

            for candidato in (
                productos_barajados
            ):

                try:

                    inventario = (
                        candidato.inventario
                    )

                except Inventario.DoesNotExist:

                    continue

                if (
                    inventario
                    and
                    inventario.cantidad_actual > 0
                ):

                    producto = candidato

                    break

            if not producto:

                print(
                    "⚠️ No hay stock disponible."
                )

                break

            inventario = (
                producto.inventario
            )

            # ------------------------------------------
            # CANTIDAD
            # ------------------------------------------

            cantidad_maxima = min(
                3,
                inventario.cantidad_actual
            )

            cantidad = random.randint(
                1,
                cantidad_maxima
            )

            cliente = random.choice(
                clientes
            )

            # ------------------------------------------
            # CREAR VENTA
            # ------------------------------------------

            venta_obj = venta.objects.create(

                codigo_usuario=cliente,

                nombre_cliente=(
                    cliente.get_full_name()
                    or cliente.username
                ),

                correo=cliente.email,

                telefono=getattr(
                    cliente,
                    "telefono",
                    ""
                ),

                direccion=(
                    "Dirección de prueba"
                ),

                metodo_pago=random.choice(
                    [
                        "persona",
                        "contraentrega",
                        "transferencia"
                    ]
                ),

                estado_pago="completado",
            )

            # ------------------------------------------
            # CREAR DETALLE
            # ------------------------------------------

            detalle = (
                detalleventa.objects.create(

                    codigo_venta=venta_obj,

                    codigo_producto=producto,

                    cantidad=cantidad,

                    valor_descuento=(
                        Decimal("0")
                    )
                )
            )

            # ------------------------------------------
            # ACTUALIZAR TOTAL
            # ------------------------------------------

            venta_obj.actualizar_total()

            print(

                f"✓ Venta "
                f"#{venta_obj.codigo_venta} | "

                f"{producto.nombre} | "

                f"Cantidad: {cantidad} | "

                f"Subtotal: "
                f"${detalle.subtotal:,.0f}"
            )

        print(
            "✓ Ventas creadas."
        )

    except Exception as e:

        print(
            f"⚠️ Error al poblar ventas: {e}"
        )


# ==========================================================
# 15. CALIFICACIONES DE USUARIOS
# ==========================================================

def poblar_calificaciones():

    print("\n==========================================")
    print("POBLANDO CALIFICACIONES")
    print("==========================================")

    servicios_disponibles = list(
        Servicios.objects.all()
    )

    clientes_disponibles = list(
        Usuario.objects.filter(
            rol="cliente"
        )
    )

    if not servicios_disponibles:

        print(
            "⚠️ No hay servicios."
        )

        return

    if not clientes_disponibles:

        print(
            "⚠️ No hay clientes."
        )

        return

    comentarios_ejemplo = [

        "Excelente servicio, muy profesional.",

        "Me encantó el resultado, volveré pronto.",

        "Buen trabajo, pero la espera fue un poco larga.",

        "Muy amable el personal.",

        "Increíble experiencia, 5 estrellas!",

        "Rápido y eficiente.",

        "El lugar es muy agradable.",

        "Podría mejorar la atención al cliente.",

        "Relación calidad-precio muy buena.",

        "No estoy del todo satisfecho con el corte.",
    ]

    for _ in range(15):

        servicio = random.choice(
            servicios_disponibles
        )

        cliente_usuario = random.choice(
            clientes_disponibles
        )

        puntuacion = random.randint(
            1,
            5
        )

        comentario = random.choice(
            comentarios_ejemplo
        )

        Calificacion.objects.create(

            servicio=servicio,

            cliente=(
                cliente_usuario.get_full_name()
                or cliente_usuario.username
            ),

            puntuacion=puntuacion,

            comentario=comentario
        )

    print(
        "✓ Calificaciones creadas."
    )


# ==========================================================
# 16. POBLAR FACTURAS
# ==========================================================

def poblar_facturas():

    print("\n==========================================")
    print("POBLANDO FACTURAS")
    print("==========================================")

    reservas = list(
        Reserva.objects.all()
    )

    productos = list(
        Producto.objects.all()
    )

    clientes = list(
        Usuario.objects.filter(
            rol="cliente"
        )
    )

    metodos = [
        "efectivo",
        "nequi",
        "daviplata",
        "tarjeta"
    ]

    # ----------------------------------------------
    # VALIDACIÓN
    # ----------------------------------------------

    if not reservas and not productos:

        print(
            "⚠️ No hay datos suficientes "
            "para generar facturas."
        )

        return

    # ==================================================
    # FACTURAS DE RESERVAS
    # ==================================================

    for reserva in reservas:

        cliente = reserva.cliente

        if not cliente and clientes:

            cliente = random.choice(
                clientes
            )

        factura = Factura.objects.create(

            cliente=cliente,

            total_pagado=float(
                reserva.precio_historico
            ),

            metodo_pago=random.choice(
                metodos
            ),

            estado=(
                "pagada"
                if reserva.estado == "confirmada"
                else "pendiente"
            )
        )

        DetalleFactura.objects.create(

            factura=factura,

            reserva=reserva,

            cantidad=1,

            precio_unitario=(
                reserva.precio_historico
            ),

            subtotal=(
                reserva.precio_historico
            )
        )

    # ==================================================
    # FACTURAS DE PRODUCTOS
    # ==================================================

    for i in range(5):

        cliente = (
            random.choice(clientes)
            if clientes
            else None
        )

        factura = Factura.objects.create(

            cliente=cliente,

            total_pagado=0,

            metodo_pago=random.choice(
                metodos
            ),

            estado="pagada"
        )

        total_acumulado = Decimal("0")

        productos_disponibles = []

        for producto in productos:

            adquisicion = (
                obtener_ultima_adquisicion(
                    producto
                )
            )

            if adquisicion:

                productos_disponibles.append(
                    producto
                )

        if not productos_disponibles:

            factura.delete()

            continue

        for _ in range(
            random.randint(1, 3)
        ):

            prod = random.choice(
                productos_disponibles
            )

            adquisicion = (
                obtener_ultima_adquisicion(
                    prod
                )
            )

            if not adquisicion:

                continue

            # ------------------------------------------
            # PRECIO REAL DE VENTA
            # ------------------------------------------

            precio_venta = (
                adquisicion.precio_venta
            )

            # ------------------------------------------
            # CANTIDAD
            # ------------------------------------------

            cant = random.randint(
                1,
                2
            )

            sub = (
                precio_venta * cant
            )

            # ------------------------------------------
            # DETALLE FACTURA
            # ------------------------------------------

            DetalleFactura.objects.create(

                factura=factura,

                producto=prod,

                cantidad=cant,

                precio_unitario=(
                    precio_venta
                ),

                subtotal=sub
            )

            total_acumulado += sub

        # ------------------------------------------
        # TOTAL FACTURA
        # ------------------------------------------

        factura.total_pagado = (
            total_acumulado
        )

        factura.save(
            update_fields=[
                "total_pagado"
            ]
        )

    print(
        "✓ Facturas creadas."
    )


# ==========================================================
# 17. EJECUCIÓN PRINCIPAL
# ==========================================================

if __name__ == "__main__":

    print("\n")
    print("==============================================")
    print("   CHICHA BARBER STUDIO")
    print("   CARGA DE DATOS DE PRUEBA")
    print("==============================================")

    limpiar_datos()

    # ----------------------------------------------
    # USUARIOS
    # ----------------------------------------------

    poblar_usuarios()

    # ----------------------------------------------
    # SERVICIOS
    # ----------------------------------------------

    poblar_servicios()

    poblar_turnos_disponibles()

    poblar_promociones()

    poblar_reservas()

    poblar_calificaciones_servicios()

    # ----------------------------------------------
    # PRODUCTOS
    # ----------------------------------------------

    poblar_productos_y_bitacora()

    # ----------------------------------------------
    # ADQUISICIONES
    # IMPORTANTE: ANTES DE VENTAS
    # ----------------------------------------------

    poblar_adquisiciones()

    # ----------------------------------------------
    # VENTAS
    # ----------------------------------------------

    poblar_ventas()

    # ----------------------------------------------
    # FACTURAS
    # ----------------------------------------------

    poblar_facturas()

    # ----------------------------------------------
    # CALIFICACIONES
    # ----------------------------------------------

    poblar_calificaciones()

    print("\n")
    print("==============================================")
    print("✅ ¡BASE DE DATOS POBLADA CON ÉXITO!")
    print("==============================================")