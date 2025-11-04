from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from database import db  # asegúrate que en database.py está la conexión MongoDB

router = APIRouter(prefix="/carrito", tags=["Carrito"])

class ItemCarrito(BaseModel):
    producto_id: str
    nombre: str
    precio: int
    cantidad: int
    imagen: str

# ➕ Agregar producto al carrito
@router.post("/")
async def agregar_item(item: ItemCarrito):
    result = await db.carrito.insert_one(item.dict())
    return {"_id": str(result.inserted_id), **item.dict()}

# 📦 Obtener todos los productos del carrito
@router.get("/")
async def obtener_carrito():
    items = []
    async for item in db.carrito.find():
        item["_id"] = str(item["_id"])
        items.append(item)
    return items

# 🗑️ Eliminar producto del carrito
@router.delete("/{item_id}")
async def eliminar_item(item_id: str):
    result = await db.carrito.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"mensaje": "Item eliminado correctamente"}
