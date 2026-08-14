from django.test import TestCase

from productos.models import Categoria, Producto, Promocion, PromocionProducto


class ProductoRelacionMERTest(TestCase):

    def test_producto_tiene_precio_y_relacion_con_categoria(self):
        producto_fields = {field.name for field in Producto._meta.get_fields()}

        self.assertIn('precio', producto_fields)
        self.assertIn('codigo_categoria', producto_fields)
        self.assertEqual(
            Producto._meta.get_field('codigo_categoria').remote_field.model,
            Categoria
        )

    def test_promocion_producto_tiene_campos_y_relaciones_esperadas(self):
        promocion_producto_fields = {
            field.name for field in PromocionProducto._meta.get_fields()
        }

        self.assertIn('precio', promocion_producto_fields)
        self.assertIn('valor_con_descuento', promocion_producto_fields)
        self.assertEqual(
            PromocionProducto._meta.get_field('codigo_promocion').remote_field.model,
            Promocion
        )
        self.assertEqual(
            PromocionProducto._meta.get_field('codigo_producto').remote_field.model,
            Producto
        )
