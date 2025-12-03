"""
Repositorio de Carrito
Capa de acceso a datos: operaciones CRUD sobre carrito
"""
from bson import ObjectId
from repositories.database import carrito_col

class CarritoRepository:
    """Repositorio para operaciones con carrito"""
    
    async def obtener_por_usuario(self, usuario_email: str):
        """Obtiene el carrito de un usuario"""
        items = []
        async for item in carrito_col.find({"usuario_email": usuario_email}):
            items.append(item)
        return items
    
    async def obtener_todos(self):
        """Obtiene todos los items del carrito"""
        items = []
        async for item in carrito_col.find():
            items.append(item)
        return items
    
    async def agregar_item(self, item: dict):
        """Agrega un item al carrito"""
        result = await carrito_col.insert_one(item)
        return result.inserted_id
    
    async def buscar_item(self, usuario_email: str, nombre: str):
        """Busca un item específico en el carrito del usuario"""
        return await carrito_col.find_one({
            "usuario_email": usuario_email,
            "nombre": nombre
        })
    
    async def eliminar_item(self, id_item: str, usuario_email: str = None):
        """Elimina un item del carrito"""
        query = {"_id": ObjectId(id_item)}
        if usuario_email:
            query["usuario_email"] = usuario_email
        result = await carrito_col.delete_one(query)
        return result.deleted_count > 0
    
    async def vaciar_carrito(self, usuario_email: str = None):
        """Vacía el carrito de un usuario o todos"""
        query = {}
        if usuario_email:
            query["usuario_email"] = usuario_email
        await carrito_col.delete_many(query)



