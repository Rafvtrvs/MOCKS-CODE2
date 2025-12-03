"""
Modelos de Autenticación
Funciones relacionadas con autenticación y autorización
"""
import hashlib

def hash_password(password: str) -> str:
    """Hashea la contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def es_super_usuario(correo: str) -> bool:
    """Verifica si un correo pertenece a un super usuario"""
    if not correo:
        return False
    correo_normalizado = correo.lower()
    super_correos = {
        "rafaarodriguezjr@gmail.com",
        "alguien@example.com",
    }
    return correo_normalizado in super_correos



