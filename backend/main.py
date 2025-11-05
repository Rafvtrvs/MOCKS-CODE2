from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import hashlib
import re

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mongo
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["tienda"]
productos_col = db["productos"]
carrito_col = db["carrito"]
favoritos_col = db["favoritos"]
usuarios_col = db["usuarios"]
empleados_col = db["empleados"]


# Helpers
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def es_super_usuario(correo: str) -> bool:
    return bool(correo) and correo.lower() == "rafaarodriguezjr@gmail.com".lower()


def serializar_producto(prod: dict) -> dict:
    return {
        "_id": str(prod.get("_id")),
        "nombre": prod.get("nombre"),
        "precio": prod.get("precio"),
        "categoria": prod.get("categoria"),
        "imagen": prod.get("imagen", ""),
        "estado": prod.get("estado", "N/A"),
    }


def serializar_carrito(item: dict) -> dict:
    return {
        "_id": str(item.get("_id")),
        "nombre": item.get("nombre"),
        "precio": item.get("precio"),
        "imagen": item.get("imagen", ""),
        "usuario_email": item.get("usuario_email", ""),
    }


def serializar_favorito(fav: dict) -> dict:
    return {
        "_id": str(fav.get("_id")),
        "nombre": fav.get("nombre"),
        "precio": fav.get("precio"),
        "categoria": fav.get("categoria"),
        "imagen": fav.get("imagen", ""),
        "estado": fav.get("estado", "N/A"),
        "usuario_email": fav.get("usuario_email", ""),
    }


def serializar_usuario(usuario: dict) -> dict:
    correo = usuario.get("correo", "")
    return {
        "_id": str(usuario.get("_id")),
        "nombres": usuario.get("nombres", ""),
        "apellidos": usuario.get("apellidos", ""),
        "rut": usuario.get("rut", ""),
        "domicilio": usuario.get("domicilio", ""),
        "correo": correo,
        "telefono": usuario.get("telefono", ""),
        "usuario": usuario.get("usuario", ""),
        "imagen_perfil": usuario.get("imagen_perfil", ""),
        "es_super_usuario": es_super_usuario(correo),
    }


# Productos
@app.get("/productos")
async def obtener_productos():
    productos = []
    async for p in productos_col.find():
        productos.append(serializar_producto(p))
    return productos


@app.post("/productos")
async def agregar_producto(producto: dict = Body(...)):
    res = await productos_col.insert_one(producto)
    return {"_id": str(res.inserted_id)}


@app.put("/productos/{id_producto}")
async def actualizar_producto(id_producto: str, producto: dict = Body(...)):
    res = await productos_col.update_one({"_id": ObjectId(id_producto)}, {"$set": producto})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "ok"}


@app.delete("/productos/{id_producto}")
async def eliminar_producto(id_producto: str):
    res = await productos_col.delete_one({"_id": ObjectId(id_producto)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "ok"}


# Carrito
@app.get("/carrito")
async def obtener_carrito(usuario_email: str | None = None):
    query = {"usuario_email": usuario_email} if usuario_email else {}
    items = []
    async for c in carrito_col.find(query):
        items.append(serializar_carrito(c))
    return items


@app.post("/carrito")
async def agregar_al_carrito(item: dict = Body(...)):
    if "usuario_email" not in item:
        raise HTTPException(status_code=400, detail="usuario_email es requerido")
    existente = await carrito_col.find_one({
        "usuario_email": item["usuario_email"],
        "nombre": item.get("nombre"),
    })
    if existente:
        raise HTTPException(status_code=400, detail="El producto ya está en el carrito")
    res = await carrito_col.insert_one(item)
    return {"_id": str(res.inserted_id)}


@app.delete("/carrito/{id_item}")
async def eliminar_item_carrito(id_item: str, usuario_email: str | None = None):
    query = {"_id": ObjectId(id_item)}
    if usuario_email:
        query["usuario_email"] = usuario_email
    res = await carrito_col.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado en carrito")
    return {"status": "ok"}


@app.delete("/carrito")
async def vaciar_carrito(usuario_email: str | None = None):
    query = {"usuario_email": usuario_email} if usuario_email else {}
    await carrito_col.delete_many(query)
    return {"status": "Carrito vacío"}


# Favoritos
@app.get("/favoritos")
async def obtener_favoritos(usuario_email: str | None = None):
    query = {"usuario_email": usuario_email} if usuario_email else {}
    favs = []
    async for f in favoritos_col.find(query):
        favs.append(serializar_favorito(f))
    return favs


@app.post("/favoritos")
async def agregar_a_favoritos(producto: dict = Body(...)):
    if "usuario_email" not in producto:
        raise HTTPException(status_code=400, detail="usuario_email es requerido")
    existente = await favoritos_col.find_one({
        "usuario_email": producto["usuario_email"],
        "nombre": producto.get("nombre"),
    })
    if existente:
        raise HTTPException(status_code=400, detail="El producto ya está en favoritos")
    res = await favoritos_col.insert_one(producto)
    return {"_id": str(res.inserted_id), "message": "Producto agregado a favoritos"}


@app.delete("/favoritos/{id_favorito}")
async def eliminar_de_favoritos(id_favorito: str, usuario_email: str | None = None):
    query = {"_id": ObjectId(id_favorito)}
    if usuario_email:
        query["usuario_email"] = usuario_email
    res = await favoritos_col.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")
    return {"status": "ok"}


@app.delete("/favoritos")
async def vaciar_favoritos(usuario_email: str | None = None):
    query = {"usuario_email": usuario_email} if usuario_email else {}
    await favoritos_col.delete_many(query)
    return {"status": "Favoritos vaciados"}


# Usuarios
@app.post("/usuarios/registro")
async def registrar_usuario(usuario: dict = Body(...)):
    existente = await usuarios_col.find_one({"correo": usuario.get("correo")})
    if existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if usuario.get("rut"):
        existe_rut = await usuarios_col.find_one({"rut": usuario.get("rut")})
        if existe_rut:
            raise HTTPException(status_code=400, detail="El RUT ya está registrado")
    # usuario
    if not usuario.get("usuario"):
        nombres = (usuario.get("nombres", "").lower().replace(" ", ""))
        apellidos = (usuario.get("apellidos", "").lower().replace(" ", ""))
        usuario["usuario"] = f"{nombres}_{apellidos}" if (nombres or apellidos) else usuario.get("correo", "").split("@")[0]
    # password
    pw = usuario.pop("password", "")
    usuario["password_hash"] = hash_password(pw)
    res = await usuarios_col.insert_one(usuario)
    creado = await usuarios_col.find_one({"_id": res.inserted_id})
    return {"_id": str(res.inserted_id), "message": "Usuario registrado exitosamente", "usuario": serializar_usuario(creado)}


@app.post("/usuarios/login")
async def login_usuario(credenciales: dict = Body(...)):
    correo = credenciales.get("correo", "")
    password = credenciales.get("password", "")
    if not correo or not password:
        raise HTTPException(status_code=400, detail="Correo y contraseña son requeridos")
    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    if usuario.get("password_hash") != hash_password(password):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return {"message": "Inicio de sesión exitoso", "usuario": serializar_usuario(usuario)}


@app.get("/usuarios/perfil/{correo}")
async def obtener_perfil(correo: str):
    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serializar_usuario(usuario)


@app.put("/usuarios/perfil/{correo}")
async def actualizar_perfil(correo: str, datos: dict = Body(...)):
    datos.pop("correo", None)
    datos.pop("password", None)
    datos.pop("password_hash", None)
    res = await usuarios_col.update_one({"correo": correo}, {"$set": datos})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario = await usuarios_col.find_one({"correo": correo})
    return {"message": "Perfil actualizado exitosamente", "usuario": serializar_usuario(usuario)}


@app.put("/usuarios/perfil/{correo}/password")
async def cambiar_password(correo: str, datos: dict = Body(...)):
    actual = datos.get("password_actual", "")
    nueva = datos.get("password_nueva", "")
    if not actual or not nueva:
        raise HTTPException(status_code=400, detail="password_actual y password_nueva son requeridos")
    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.get("password_hash") != hash_password(actual):
        raise HTTPException(status_code=401, detail="La contraseña actual es incorrecta")
    await usuarios_col.update_one({"correo": correo}, {"$set": {"password_hash": hash_password(nueva)}})
    return {"message": "Contraseña actualizada exitosamente"}


# Empleados (portal)
@app.post("/empleados")
async def crear_empleado(empleado: dict = Body(...)):
    for campo in ["nombre", "email", "rut", "rol"]:
        if not empleado.get(campo):
            raise HTTPException(status_code=400, detail=f"Campo requerido: {campo}")
    if not re.match(r"^\d{7,8}-[0-9kK]$", empleado.get("rut", "")):
        raise HTTPException(status_code=400, detail="RUT inválido (formato 12345678-9)")
    existente = await empleados_col.find_one({"$or": [{"email": empleado["email"]}, {"rut": empleado["rut"]}]})
    if existente:
        raise HTTPException(status_code=400, detail="Empleado ya existe (correo o RUT)")
    if "estado" not in empleado:
        empleado["estado"] = "activo"
    res = await empleados_col.insert_one(empleado)
    return {"_id": str(res.inserted_id)}

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
