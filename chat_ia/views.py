from django.http import JsonResponse
from chat_ia.ai_service import obtener_respuesta_ia
from servicios.models import Servicios, Promocion
from productos.models import Producto, Categoria

MENSAJE_BIENVENIDA = "¡Hola! 👋 Soy **ChichaBot**, tu asistente virtual de **Chicha Barber Studio**.\n\nEstoy aquí para ayudarte con:\n• 📅 Agendar citas\n• 🛒 Comprar productos\n• 💇 Servicios disponibles\n• ❓ Cualquier duda sobre la barbería\n\n¿En qué puedo ayudarte hoy?"

def construir_contexto_dinamico():
    """Construye un contexto con datos reales de la BD para que la IA responda con info actualizada."""
    servicios = Servicios.objects.filter(estado=True)
    promociones = Promocion.objects.filter(estado=True)
    categorias = Categoria.objects.all()
    productos = Producto.objects.filter(estado=True)

    contexto_extra = "=== DATOS ACTUALES DEL SISTEMA (información real) ===\n\n"

    contexto_extra += "--- SERVICIOS DISPONIBLES ---\n"
    if servicios.exists():
        for s in servicios:
            contexto_extra += f"- {s.nombre}: ${s.precio:.0f} | Duración: {s.duracion} min | {s.descripcion}\n"
    else:
        contexto_extra += "- No hay servicios registrados actualmente.\n"

    contexto_extra += "\n--- PROMOCIONES VIGENTES ---\n"
    if promociones.exists():
        for p in promociones:
            contexto_extra += f"- {p.nombre}: {p.porcentaje_descuento}% descuento en {p.servicio.nombre} | {p.descripcion}\n"
    else:
        contexto_extra += "- No hay promociones activas en este momento.\n"

    contexto_extra += "\n--- CATEGORÍAS DE PRODUCTOS ---\n"
    if categorias.exists():
        for c in categorias:
            contexto_extra += f"- {c.nombre}: {c.descripcion or 'Sin descripción'}\n"
    else:
        contexto_extra += "- No hay categorías registradas.\n"

    contexto_extra += "\n--- PRODUCTOS EN VENTA ---\n"
    if productos.exists():
        for p in productos:
            stock = getattr(p, 'stock', None)
            precio = f"${stock.precio_venta:.0f}" if stock and stock.precio_venta else "Precio no disponible"
            cantidad = f"Stock: {stock.cantidad}" if stock else "Stock no disponible"
            contexto_extra += f"- {p.nombre} | {precio} | {cantidad} | Categoría: {p.categoria.nombre if p.categoria else 'Sin categoría'}\n"
    else:
        contexto_extra += "- No hay productos disponibles actualmente.\n"

    return contexto_extra


def vista_chat_ia(request):
    if "chat" not in request.session:
        request.session["chat"] = []
        # Agregar mensaje de bienvenida cuando se inicializa el chat
        request.session["chat"].append({"rol": "ia", "texto": MENSAJE_BIENVENIDA})
        request.session.modified = True

    if request.method == "POST":
        user_input = request.POST.get("pregunta")
        if user_input:
            chat = request.session["chat"]
            # Agregar mensaje usuario
            chat.append({"rol": "user", "texto": user_input})
            
            # Construir contexto dinámico con datos reales de la BD
            contexto_dinamico = construir_contexto_dinamico()
            
            # Obtener respuesta IA con el contexto extra
            respuesta = obtener_respuesta_ia(user_input, system_prompt_extra=contexto_dinamico)
            
            # Agregar mensaje IA
            chat.append({"rol": "ia", "texto": respuesta})
            
            request.session["chat"] = chat
            request.session.modified = True
            
            return JsonResponse({"status": "ok", "nuevo_mensaje": respuesta})

    return JsonResponse({"chat": request.session["chat"]})

