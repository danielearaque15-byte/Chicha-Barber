import os
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.utils import timezone
import pytz #es la calculadora que hace el cambio de moneda exacto entre la hora global del servidor y la hora de tu barbería.
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8') # Para Linux/macOS
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES') # Para Windows
    except:
        pass # Fallback al locale por defecto si no están instalados

def renombrar_comprobante_factura(instance, filename):
    ext = filename.split('.')[-1]
    # Genera una ruta como: comprobantes/factura_5.png
    return os.path.join('comprobantes/', f"factura_{instance.pk}.{ext}")

def enviar_correo_cancelacion_admin(correo_cliente, nombre, servicio, fecha):
    subject = f"IMPORTANTE: Cambio en tu cita - Chicha Barber Studio"
    
    # 1. Convertimos la fecha a la zona horaria de Colombia explícitamente
    zona_local = pytz.timezone('America/Bogota')
    
    # Si la fecha ya tiene zona horaria, la convertimos. Si no, la localizamos.
    if timezone.is_aware(fecha):
        fecha_local = fecha.astimezone(zona_local)
    else:
        fecha_local = zona_local.localize(fecha)
    
    # 2. Formateamos usando la fecha local
    # %H:%M para formato 24h o %I:%M %p para 12h con AM/PM
    fecha_formateada = fecha_local.strftime('%A %d de %B a las %I:%M %p')
    
    message = f"""
    Hola, {nombre}.
    
    Te escribimos de Chicha Barber Studio para informarte que, debido a motivos de fuerza mayor, 
    no podremos atender tu cita de {servicio} programada para el {fecha_formateada}.
    
    Lamentamos mucho los inconvenientes que esto pueda causarte. Queremos invitarte a que 
    programes una nueva cita a través de nuestra web en un horario que te sea cómodo.
    
    ¡Estamos listos para dejarte con el mejor estilo apenas regreses!
    
    Atentamente,
    El equipo de Chicha Barber Studio ✂️💈
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [correo_cliente],
        fail_silently=False
    )


def enviar_correo_venta(correo_cliente, nombre, carrito, total):

    asunto = 'Confirmación de venta 💈'
    # Formatear total con puntos de miles
    total_formateado = "{:,.0f}".format(total).replace(",", ".")

    productos_html = ""

    for item in carrito:
        precio_item = "{:,.0f}".format(float(item['precio'])).replace(",", ".")
        productos_html += f"""
        <tr>
            <td style="padding:12px; border-bottom:1px solid #ddd;">
                {item['nombre']}
            </td>

            <td style="padding:12px; border-bottom:1px solid #ddd; text-align:center;">
                {item.get('cantidad', 1)}
            </td>

            <td style="padding:12px; border-bottom:1px solid #ddd; text-align:right;">
                ${precio_item}
            </td>
        </tr>
        """

    html_content = f"""
    <div style="
        background:#f4f4f4;
        padding:40px;
        font-family:Arial;
    ">

        <div style="
            max-width:700px;
            margin:auto;
            background:white;
            border-radius:15px;
            overflow:hidden;
            box-shadow:0 0 15px rgba(0,0,0,.1);
        ">

            <!-- HEADER -->
            <div style="
                background:black;
                color:white;
                padding:35px;
                text-align:center;
            ">

                <h1 style="margin-top:15px;">
                    Chicha Barber 💈
                </h1>

                <p>
                    Confirmación de venta
                </p>

            </div>

            <!-- BODY -->
            <div style="padding:35px;">

                <h2>Hola {nombre} 👋</h2>

                <p>
                    Gracias por realizar tu venta en nuestra barbería.
                </p>

                <h3 style="margin-top:30px;">
                    🛒 Resumen de venta
                </h3>

                <table style="
                    width:100%;
                    border-collapse:collapse;
                    margin-top:20px;
                ">

                    <thead>

                        <tr style="background:#f1f1f1;">

                            <th style="padding:15px;">
                                Producto
                            </th>

                            <th style="padding:15px;">
                                Cantidad
                            </th>

                            <th style="padding:15px;">
                                Precio
                            </th>

                        </tr>

                    </thead>

                    <tbody>
                        {productos_html}
                    </tbody>

                </table>

                <h2 style="
                    margin-top:30px;
                    text-align:right;
                    color:#28a745;
                ">
                    Total: ${total_formateado}
                </h2>

                <p style="margin-top:40px;">
                    ✂️ Gracias por confiar en nosotros.
                </p>

            </div>

            <!-- FOOTER -->
            <div style="
                background:#111;
                color:#bbb;
                text-align:center;
                padding:20px;
                font-size:14px;
            ">
                © 2026 Chicha Barber
            </div>

        </div>

    </div>
    """

    email = EmailMultiAlternatives(
        asunto,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [correo_cliente]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

#reservas correo
def enviar_correo_reserva(correo_cliente, nombre, servicio, fecha):

    asunto = 'Confirmación de tu reserva 💈'
    
    # Localizar fecha a Colombia
    zona_local = pytz.timezone('America/Bogota')
    if timezone.is_aware(fecha):
        fecha_local = fecha.astimezone(zona_local)
    else:
        fecha_local = zona_local.localize(fecha)
    
    fecha_formateada = fecha_local.strftime('%A %d de %B a las %I:%M %p')
    # Formatear precio
    precio_formateado = "{:,.0f}".format(servicio.precio).replace(",", ".")

    html_content = f"""
    <div style="
        background:#f4f4f4;
        padding:40px;
        font-family:Arial;
    ">

        <div style="
            max-width:700px;
            margin:auto;
            background:white;
            border-radius:15px;
            overflow:hidden;
            box-shadow:0 0 15px rgba(0,0,0,.1);
        ">

            <!-- HEADER -->
            <div style="
                background:black;
                color:white;
                padding:35px;
                text-align:center;
            ">

                <h1 style="margin-top:15px;">
                    Chicha Barber 💈
                </h1>

                <p>
                    Confirmación de reserva
                </p>

            </div>

            <!-- BODY -->
            <div style="padding:35px;">

                <h2>Hola {nombre} 👋</h2>

                <p>
                    Tu reserva ha sido registrada correctamente.
                </p>

                <h3 style="margin-top:25px;">
                    📅 Detalles de la cita
                </h3>

                <p><strong>Servicio:</strong> {servicio.nombre}</p>

                <p><strong>Fecha:</strong> {fecha_formateada}</p>
                
                <p><strong>Precio:</strong> ${precio_formateado}</p>
                
                <p style="margin-top:30px;">
                    Te esperamos en nuestra barbería ✂️
                </p>

            </div>

            <!-- FOOTER -->
            <div style="
                background:#111;
                color:#bbb;
                text-align:center;
                padding:20px;
                font-size:14px;
            ">
                © 2026 Chicha Barber
            </div>

        </div>

    </div>  
    """

    email = EmailMultiAlternatives(
        asunto,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [correo_cliente]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
    
def enviar_correo_recuperacion(correo_cliente, nombre, reset_url):

    asunto = 'Restablece tu contraseña - Chicha Barber Studio'

    html_content = f"""
    <div style="background:#f4f4f4; padding:40px; font-family:Arial;">
        <div style="max-width:700px; margin:auto; background:white; border-radius:15px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,.1);">

            <!-- HEADER -->
            <div style="background:black; color:white; padding:35px; text-align:center;">
                <h1 style="margin-top:15px;">Chicha Barber 💈</h1>
                <p>Restablecimiento de contraseña</p>
            </div>

            <!-- BODY -->
            <div style="padding:35px;">
                <h2>Hola {nombre} 👋</h2>
                <p style="color:#555;">
                    Recibimos una solicitud para restablecer la contraseña de tu cuenta en
                    <strong>Chicha Barber Studio</strong>.
                </p>
                <p style="color:#555;">Haz clic en el botón para crear una nueva contraseña:</p>

                <div style="text-align:center; margin:30px 0;">
                    <a href="{reset_url}"
                       style="background:#c9a84c; color:#1a1a1a; padding:14px 36px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:15px;">
                        RESTABLECER CONTRASEÑA
                    </a>
                </div>

                <p style="color:#888; font-size:13px; text-align:center;">
                    Este enlace expira en <strong style="color:#c9a84c;">24 horas</strong>.
                </p>
                <p style="color:#aaa; font-size:12px; text-align:center; margin-top:20px;">
                    Si no solicitaste este cambio, puedes ignorar este correo.
                </p>
            </div>

            <!-- FOOTER -->
            <div style="background:#111; color:#bbb; text-align:center; padding:20px; font-size:14px;">
                © 2026 Chicha Barber
            </div>

        </div>
    </div>
    """

    email = EmailMultiAlternatives(
        asunto,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [correo_cliente]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    
def enviar_correo_calificacion(correo_cliente, nombre, servicio, link_calificacion):
    asunto = '¿Cómo fue tu experiencia? Califica tu servicio 💈'

    html_content = f"""
    <div style="background:#f4f4f4; padding:40px; font-family:Arial;">
        <div style="max-width:700px; margin:auto; background:white; border-radius:15px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,.1);">

            <div style="background:black; color:white; padding:35px; text-align:center;">
                <h1 style="margin-top:15px;">Chicha Barber 💈</h1>
                <p>Tu opinión nos importa</p>
            </div>

            <div style="padding:35px;">
                <h2>Hola {nombre} 👋</h2>
                <p style="color:#555;">
                    Gracias por visitarnos. Esperamos que tu experiencia con el servicio de
                    <strong>{servicio}</strong> haya sido excelente.
                </p>
                <p style="color:#555;">
                    Te invitamos a calificar tu servicio. Solo toma un momento y nos ayuda mucho a mejorar.
                </p>

                <div style="text-align:center; margin:35px 0;">
                    <a href="{link_calificacion}"
                       style="background:#c9a84c; color:#1a1a1a; padding:16px 40px; border-radius:8px;
                              text-decoration:none; font-weight:bold; font-size:16px;">
                        ⭐ Calificar mi servicio
                    </a>
                </div>

                <p style="color:#aaa; font-size:12px; text-align:center;">
                    Este enlace es de un solo uso y expira una vez que envíes tu calificación.
                </p>
            </div>

            <div style="background:#111; color:#bbb; text-align:center; padding:20px; font-size:14px;">
                © 2026 Chicha Barber
            </div>
        </div>
    </div>
    """

    email = EmailMultiAlternatives(asunto, '', settings.DEFAULT_FROM_EMAIL, [correo_cliente])
    email.attach_alternative(html_content, "text/html")
    email.send()