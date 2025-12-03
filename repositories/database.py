"""
Repositorio de Base de Datos
Capa de acceso a datos: conexión y colecciones de MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient

# Conexión a MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["tienda"]

# Colecciones
productos_col = db["productos"]
carrito_col = db["carrito"]
favoritos_col = db["favoritos"]
usuarios_col = db["usuarios"]
empleados_col = db["empleados"]
cupones_col = db["cupones"]
ordenes_col = db["ordenes"]
tokens_recuperacion_col = db["tokens_recuperacion"]  # Tokens para cambio de contraseña

