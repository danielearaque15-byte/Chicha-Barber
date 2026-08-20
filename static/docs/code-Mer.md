erDiagram
    %% ================= MÓDULO: USUARIOS =================
    USUARIO ||--o{ TURNO : "Ofrece (Rol: BARBERO)"
    USUARIO ||--o{ RESERVA : "Realiza (Rol: CLIENTE)"
    USUARIO ||--o{ FACTURA : "Se le asigna"
    USUARIO ||--o{ venta : "Registra (Venta Online)"
    USUARIO }o--o{ SERVICIO : "Tiene especialidad (Rol: BARBERO)"

    USUARIO {
        int id PK
        string username
        string first_name
        string last_name
        string email
        string telefono
        string rol
        boolean estado
        image foto_perfil
    }

    %% ================= MÓDULO: RESERVAS =================
    TURNO ||--o| RESERVA : "Asignado a"
    RESERVA ||--|| SERVICIO : "Solicita"
    RESERVA |o--o| PROMOCION : "Aplica (Opcional)"
    RESERVA ||--o| CALIFICACION : "Es evaluada"

    TURNO {
        int id PK
        int profesional_id FK
        date fecha
        time hora_inicio
        time hora_fin
        string estado
        datetime fecha_creacion
    }

    RESERVA {
        int id PK
        int turno_id FK
        int cliente_id FK
        int servicio_id FK
        int promocion_id FK
        float precio_historico
        string estado
        datetime fecha_creacion
    }

    %% ================= MÓDULO: SERVICIOS =================
    SERVICIO ||--o{ PROMOCION : "Tiene"

    SERVICIO {
        int id PK
        string nombre
        decimal precio
        int duracion
        text descripcion
        image imagen
        boolean estado
    }

    PROMOCION {
        int id PK
        int servicio_id FK
        string nombre
        decimal porcentaje_descuento
        string duracion
        text descripcion
        date fecha_inicio
        date fecha_fin
        image imagen
        boolean estado
    }

    CALIFICACION {
        int id PK
        int reserva_id FK
        int puntuacion
        text comentario
        datetime fecha_calificacion
        boolean mostrar_en_inicio
    }

    %% ================= MÓDULO: PRODUCTOS E existencias =================
    CATEGORIA ||--o{ PRODUCTO : "Clasifica"
    PROVEEDOR ||--o{ bitacora : "Suministra"

    PRODUCTO ||--|| bitacora : "Tiene"
    PRODUCTO ||--o{ MOVIMIENTO_existencias : "Genera"
    PRODUCTO ||--o{ DETALLE_venta : "Se incluye en"

    CATEGORIA {
        int id PK
        string nombre
        text descripcion
    }

    PROVEEDOR {
        int id PK
        string nombre
        string telefono
        string correo
        string direccion
    }

    PRODUCTO {
        int codigo_producto PK
        string codigo
        string nombre
        text descripcion
        image imagen
        boolean estado
        int categoria_id FK
    }

    bitacora {
        int id PK
        int producto_id FK
        int proveedor_id FK
        int cantidad
        decimal precio_venta
        decimal precio_venta
    }

    MOVIMIENTO_existencias {
        int id PK
        int producto_id FK
        string tipo
        int cantidad
        string motivo
        datetime fecha
    }

    %% ================= MÓDULO: ventaS =================
    venta ||--o{ DETALLE_venta : "Contiene"

    venta {
        int codigo_venta PK
        int usuario_id FK
        string nombre_cliente
        string correo
        string telefono
        string direccion
        decimal total
        string metodo_pago
        string estado_pago
        file comprobante
        datetime fecha_venta
    }

    DETALLE_venta {
        int codigo_detalle PK
        int venta_id FK
        int producto_id FK
        int cantidad
        decimal precio_unitario
        decimal subtotal
    }

    %% ================= MÓDULO: FACTURACIÓN =================
    FACTURA ||--o{ DETALLE_FACTURA : "Contiene"
    DETALLE_FACTURA |o--o| PRODUCTO : "Cobra"
    DETALLE_FACTURA |o--o| RESERVA : "Cobra"

    FACTURA {
        int id PK
        int cliente_id FK
        datetime fecha_emision
        float total_pagado
        string metodo_pago
        string estado
        image comprobante_pago
        image imagen_transaccion
    }

    DETALLE_FACTURA {
        int id PK
        int factura_id FK
        int producto_id FK
        int reserva_id FK
        int cantidad
        decimal precio_unitario
        decimal subtotal
    }

    %% ================= MÓDULO: CONFIGURACIÓN =================

    DATOS_TRANSFERENCIA {
        int id PK
        string banco
        string tipo_cuenta
        string numero_cuenta
        string titular
        text instructions
    }

    CARRUSEL {
        int id PK
        datetime fecha_creacion
        datetime fecha_modificacion
        string nombre
        string imagen
        string texto
        boolean estado
    }