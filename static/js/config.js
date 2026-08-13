function permitirSoloTextoSeguro(input) {
    // Borra cualquier cosa que NO sea letras (a-z, A-Z), números (0-9), acentos estándar o espacios
    input.value = input.value.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]/g, '');
}