"""
Servicio de Productos
Capa de lógica de negocio: operaciones de negocio sobre productos
"""
from repositories.productos_repository import ProductosRepository
from models.serializers import serializar_producto
from bson import ObjectId

class ProductosService:
    """Servicio para lógica de negocio de productos"""
    
    def __init__(self):
        self.repository = ProductosRepository()
    
    async def obtener_todos(self):
        """Obtiene todos los productos serializados"""
        productos = await self.repository.obtener_todos()
        return [serializar_producto(p) for p in productos]
    
    async def obtener_por_id(self, id_producto: str):
        """Obtiene un producto por ID"""
        producto = await self.repository.obtener_por_id(id_producto)
        if producto:
            return serializar_producto(producto)
        return None
    
    async def crear(self, producto: dict):
        """Crea un nuevo producto"""
        return await self.repository.crear(producto)
    
    async def actualizar(self, id_producto: str, producto: dict):
        """Actualiza un producto"""
        existe = await self.repository.obtener_por_id(id_producto)
        if not existe:
            return False
        return await self.repository.actualizar(id_producto, producto)
    
    async def eliminar(self, id_producto: str):
        """Elimina un producto"""
        existe = await self.repository.obtener_por_id(id_producto)
        if not existe:
            return False
        return await self.repository.eliminar(id_producto)



