"""
Modelos y Serializadores
Capa de modelos: funciones para serializar datos
"""
from bson import ObjectId

def serializar_producto(prod):
    """Serializa un producto de MongoDB a formato JSON"""
    return {
        "_id": str(prod["_id"]),
        "nombre": prod["nombre"],
        "precio": prod["precio"],
        "categoria": prod["categoria"],
        "imagen": prod.get("imagen", ""),
        "estado": prod.get("estado", "N/A")
    }

def serializar_carrito(item):
    """Serializa un item del carrito de MongoDB a formato JSON"""
    return {
        "_id": str(item["_id"]),
        "nombre": item["nombre"],
        "precio": item["precio"],
        "imagen": item.get("imagen", "")
    }

def serializar_favorito(fav):
    """Serializa un favorito de MongoDB a formato JSON"""
    return {
        "_id": str(fav["_id"]),
        "nombre": fav["nombre"],
        "precio": fav["precio"],
        "categoria": fav["categoria"],
        "imagen": fav.get("imagen", ""),
        "estado": fav.get("estado", "N/A")
    }

def serializar_usuario(usuario, es_super_usuario_func):
    """Serializa un usuario, excluyendo la contraseña"""
    correo = usuario.get("correo", "")
    return {
        "_id": str(usuario["_id"]),
        "nombres": usuario.get("nombres", ""),
        "apellidos": usuario.get("apellidos", ""),
        "rut": usuario.get("rut", ""),
        "domicilio": usuario.get("domicilio", ""),
        "correo": correo,
        "telefono": usuario.get("telefono", ""),
        "usuario": usuario.get("usuario", ""),
        "imagen_perfil": usuario.get("imagen_perfil", ""),
        "es_super_usuario": es_super_usuario_func(correo),
        "latitud": usuario.get("latitud"),
        "longitud": usuario.get("longitud")
    }



