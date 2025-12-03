"""
Repositorio de Usuarios
Capa de acceso a datos: operaciones CRUD sobre usuarios
"""
from repositories.database import usuarios_col

class UsuariosRepository:
    """Repositorio para operaciones con usuarios"""
    
    async def obtener_por_correo(self, correo: str):
        """Obtiene un usuario por su correo"""
        return await usuarios_col.find_one({"correo": correo})
    
    async def obtener_por_rut(self, rut: str):
        """Obtiene un usuario por su RUT"""
        return await usuarios_col.find_one({"rut": rut})
    
    async def crear(self, usuario: dict):
        """Crea un nuevo usuario"""
        result = await usuarios_col.insert_one(usuario)
        return await usuarios_col.find_one({"_id": result.inserted_id})
    
    async def actualizar(self, correo: str, datos: dict):
        """Actualiza los datos de un usuario"""
        result = await usuarios_col.update_one(
            {"correo": correo},
            {"$set": datos}
        )
        if result.matched_count > 0:
            return await usuarios_col.find_one({"correo": correo})
        return None
    
    async def actualizar_password(self, correo: str, password_hash: str):
        """Actualiza la contraseña de un usuario"""
        await usuarios_col.update_one(
            {"correo": correo},
            {"$set": {"password_hash": password_hash}}
        )



