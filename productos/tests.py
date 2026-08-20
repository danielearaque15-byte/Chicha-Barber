from decimal import Decimal

from django.test import TestCase

from usuarios.models import Usuario
from productos.models import (
    Producto,
    bitacora,
    venta,
    detalleventa,
    MovimientoInventario
)


class ProductoventaTest(TestCase):

    def setUp(self):
        self.usuario = Usuario.objects.first() or Usuario.objects.create_user(
            username='123456789',
            email='test_usuario@correo.com',
            password='Test1234*',
            first_name='Admin',
            last_name='User',
            telefono='3001234567',
            rol='admin'
        )

        self.producto = Producto.objects.create(
            nombre="Cerveza Poker",
            descripcion="Cerveza de prueba",
            estado=True
        )

        # El signal crea automáticamente el bitacora
        self.producto.refresh_from_db()

        self.producto.bitacora.cantidad = 20
        self.producto.bitacora.precio_venta = Decimal("3000.00")
        self.producto.bitacora.precio_venta = Decimal("5000.00")
        self.producto.bitacora.save()

    def test_crear_producto(self):

        print("\n========== PRODUCTO ==========")
        print("Código:", self.producto.codigo)
        print("Nombre:", self.producto.nombre)
        print("Precio venta:", self.producto.bitacora.precio_venta)
        print("Precio Venta:", self.producto.bitacora.precio_venta)
        print("bitacora:", self.producto.bitacora.cantidad)

        self.assertEqual(self.producto.bitacora.cantidad, 20)

    def test_crear_venta(self):

        v = venta.objects.create(
            codigo_usuario=self.usuario,
            nombre_cliente="Pedro",
            correo="pedro@gmail.com",
            telefono="3001234567",
            direccion="Bogotá",
            metodo_pago="persona",
            estado_pago="completado"
        )

        detalle = detalleventa.objects.create(
            codigo_venta=v,
            codigo_producto=self.producto,
            cantidad=3
        )

        v.actualizar_total()

        v.refresh_from_db()
        self.producto.bitacora.refresh_from_db()

        print("\n========== venta ==========")
        print("venta:", v.codigo_venta)
        print("Cliente:", v.nombre_cliente)
        print("Total:", v.total_compra)

        print("\n========== DETALLE ==========")
        print("Producto:", detalle.codigo_producto.nombre)
        print("Cantidad:", detalle.cantidad)
        print("Subtotal:", detalle.subtotal)

        print("\n========== bitacora ==========")
        print("bitacora restante:", self.producto.bitacora.cantidad)

        self.assertEqual(detalle.subtotal, Decimal("15000.00"))
        self.assertEqual(v.total_compra, Decimal("15000.00"))
        self.assertEqual(self.producto.bitacora.cantidad, 17)

    def test_movimiento_inventario(self):

        v = venta.objects.create(
            codigo_usuario=self.usuario,
            nombre_cliente="Pedro",
            metodo_pago="persona",
            estado_pago="completado"
        )

        detalleventa.objects.create(
            codigo_venta=v,
            codigo_producto=self.producto,
            cantidad=2
        )

        movimiento = MovimientoInventario.objects.last()

        print("\n========== MOVIMIENTO ==========")
        print("Producto:", movimiento.producto.nombre)
        print("Tipo:", movimiento.tipo)
        print("Cantidad:", movimiento.cantidad)
        print("Motivo:", movimiento.motivo)

        self.assertEqual(movimiento.tipo, "salida")
        self.assertEqual(movimiento.cantidad, 2)

    def test_bitacora_insuficiente(self):

        v = venta.objects.create(
            codigo_usuario=self.usuario,
            nombre_cliente="Pedro",
            metodo_pago="persona",
            estado_pago="completado"
        )

        with self.assertRaises(ValueError):

            detalleventa.objects.create(
                codigo_venta=v,
                codigo_producto=self.producto,
                cantidad=100
            )

        print("\n[OK] Se detectó correctamente el bitacora insuficiente.")

# Create your tests here.
