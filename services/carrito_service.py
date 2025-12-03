"""
Servicio de Carrito
Capa de lógica de negocio: operaciones de negocio sobre carrito
"""
from repositories.carrito_repository import CarritoRepository
from models.serializers import serializar_carrito

class CarritoService:
    """Servicio para lógica de negocio de carrito"""
    
    def __init__(self):
        self.repository = CarritoRepository()
    
    async def obtener_por_usuario(self, usuario_email: str = None):
        """Obtiene el carrito de un usuario serializado"""
        if usuario_email:
            items = await self.repository.obtener_por_usuario(usuario_email)
        else:
            items = await self.repository.obtener_todos()
        return [serializar_carrito(item) for item in items]
    
    async def agregar_item(self, item: dict):
        """Agrega un item al carrito con validaciones"""
        if "usuario_email" not in item:
            raise ValueError("usuario_email es requerido")
        
        # Verificar si ya existe
        existente = await self.repository.buscar_item(
            item["usuario_email"],
            item.get("nombre")
        )
        if existente:
            raise ValueError("El producto ya está en el carrito")
        
        return await self.repository.agregar_item(item)
    
    async def eliminar_item(self, id_item: str, usuario_email: str = None):
        """Elimina un item del carrito"""
        return await self.repository.eliminar_item(id_item, usuario_email)
    
    async def vaciar_carrito(self, usuario_email: str = None):
        """Vacía el carrito"""
        await self.repository.vaciar_carrito(usuario_email)



