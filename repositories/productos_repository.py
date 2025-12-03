"""
Repositorio de Productos
Capa de acceso a datos: operaciones CRUD sobre productos
"""
from bson import ObjectId
from repositories.database import productos_col

class ProductosRepository:
    """Repositorio para operaciones con productos"""
    
    async def obtener_todos(self):
        """Obtiene todos los productos"""
        productos = []
        async for p in productos_col.find():
            productos.append(p)
        return productos
    
    async def obtener_por_id(self, id_producto: str):
        """Obtiene un producto por su ID"""
        return await productos_col.find_one({"_id": ObjectId(id_producto)})
    
    async def crear(self, producto: dict):
        """Crea un nuevo producto"""
        result = await productos_col.insert_one(producto)
        return result.inserted_id
    
    async def actualizar(self, id_producto: str, producto: dict):
        """Actualiza un producto existente"""
        result = await productos_col.update_one(
            {"_id": ObjectId(id_producto)}, 
            {"$set": producto}
        )
        return result.matched_count > 0
    
    async def eliminar(self, id_producto: str):
        """Elimina un producto"""
        result = await productos_col.delete_one({"_id": ObjectId(id_producto)})
        return result.deleted_count > 0



