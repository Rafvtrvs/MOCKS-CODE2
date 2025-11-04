from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import Body

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Conexión a MongoDB ---
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["tienda"]
productos_col = db["productos"]
carrito_col = db["carrito"]

# --- Helper para convertir ObjectId ---
def serializar_producto(prod):
    return {
        "_id": str(prod["_id"]),  # necesario para usar en el frontend
        "nombre": prod["nombre"],
        "precio": prod["precio"],
        "categoria": prod["categoria"],
        "imagen": prod.get("imagen", ""),
        "estado": prod.get("estado", "Disponible")  # valor por defecto
    }


def serializar_carrito(item):
    return {
        "_id": str(item["_id"]),
        "nombre": item["nombre"],
        "precio": item["precio"],
        "imagen": item.get("imagen", "")
    }

# --- PRODUCTOS ---
@app.get("/productos")
async def obtener_productos():
    productos = []
    async for p in productos_col.find():
        productos.append(serializar_producto(p))
    return productos

@app.post("/productos")
async def agregar_producto(producto: dict = Body(...)):
    result = await productos_col.insert_one(producto)
    return {"_id": str(result.inserted_id)}

@app.put("/productos/{id_producto}")
async def actualizar_producto(id_producto: str, producto: dict = Body(...)):
    result = await productos_col.update_one({"_id": ObjectId(id_producto)}, {"$set": producto})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "ok"}

@app.delete("/productos/{id_producto}")
async def eliminar_producto(id_producto: str):
    result = await productos_col.delete_one({"_id": ObjectId(id_producto)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "ok"}


# --- CARRITO ---
@app.get("/carrito")
async def obtener_carrito():
    carrito = []
    async for c in carrito_col.find():
        carrito.append(serializar_carrito(c))
    return carrito

@app.post("/carrito")
async def agregar_al_carrito(item: dict):
    """Agrega un producto al carrito"""
    result = await carrito_col.insert_one(item)
    return {"_id": str(result.inserted_id)}

@app.delete("/carrito/{id_item}")
async def eliminar_item_carrito(id_item: str):
    """Elimina un producto del carrito"""
    result = await carrito_col.delete_one({"_id": ObjectId(id_item)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado en carrito")
    return {"status": "ok"}

@app.delete("/carrito")
async def vaciar_carrito():
    """Vacía el carrito completo"""
    await carrito_col.delete_many({})
    return {"status": "Carrito vacío"}
