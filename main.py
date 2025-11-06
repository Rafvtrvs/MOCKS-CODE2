from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import Body
import hashlib

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
favoritos_col = db["favoritos"]  # Nueva colección para favoritos
usuarios_col = db["usuarios"]  # Colección para usuarios
empleados_col = db["empleados"]  # Colección para portal de empleados
cupones_col = db["cupones"]  # Colección opcional para cupones (no usada en básico)

# --- Helper para convertir ObjectId ---
def serializar_producto(prod):
    return {
        "_id": str(prod["_id"]),
        "nombre": prod["nombre"],
        "precio": prod["precio"],
        "categoria": prod["categoria"],
        "imagen": prod.get("imagen", ""),
        "estado": prod.get("estado", "N/A")
    }

def serializar_carrito(item):
    return {
        "_id": str(item["_id"]),
        "nombre": item["nombre"],
        "precio": item["precio"],
        "imagen": item.get("imagen", "")
    }

def serializar_favorito(fav):
    return {
        "_id": str(fav["_id"]),
        "nombre": fav["nombre"],
        "precio": fav["precio"],
        "categoria": fav["categoria"],
        "imagen": fav.get("imagen", ""),
        "estado": fav.get("estado", "N/A")
    }

def serializar_usuario(usuario):
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
        "es_super_usuario": es_super_usuario(correo)
    }

def hash_password(password: str) -> str:
    """Hashea la contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def es_super_usuario(correo: str) -> bool:
    if not correo:
        return False
    correo_normalizado = correo.lower()
    super_correos = {
        "rafaarodriguezjr@gmail.com",
        "alguien@example.com",
    }
    return correo_normalizado in super_correos

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
async def obtener_carrito(usuario_email: str = None):
    """Obtiene el carrito de un usuario específico"""
    query = {}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    carrito = []
    async for c in carrito_col.find(query):
        carrito.append(serializar_carrito(c))
    return carrito

@app.post("/carrito")
async def agregar_al_carrito(item: dict):
    """Agrega un producto al carrito de un usuario"""
    # Verificar que se proporcione el email del usuario
    if "usuario_email" not in item:
        raise HTTPException(status_code=400, detail="usuario_email es requerido")
    
    # Verificar si el producto ya está en el carrito del usuario
    existente = await carrito_col.find_one({
        "usuario_email": item["usuario_email"],
        "nombre": item.get("nombre")
    })
    
    if existente:
        raise HTTPException(status_code=400, detail="El producto ya está en el carrito")
    
    result = await carrito_col.insert_one(item)
    return {"_id": str(result.inserted_id)}

@app.delete("/carrito/{id_item}")
async def eliminar_item_carrito(id_item: str, usuario_email: str = None):
    """Elimina un producto del carrito de un usuario"""
    query = {"_id": ObjectId(id_item)}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    result = await carrito_col.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado en carrito")
    return {"status": "ok"}

@app.delete("/carrito")
async def vaciar_carrito(usuario_email: str = None):
    """Vacía el carrito de un usuario"""
    query = {}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    await carrito_col.delete_many(query)
    return {"status": "Carrito vacío"}


# --- FAVORITOS ---
@app.get("/favoritos")
async def obtener_favoritos(usuario_email: str = None):
    """Obtiene los favoritos de un usuario específico"""
    query = {}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    favoritos = []
    async for f in favoritos_col.find(query):
        favoritos.append(serializar_favorito(f))
    return favoritos

@app.post("/favoritos")
async def agregar_a_favoritos(producto: dict = Body(...)):
    """Agrega un producto a favoritos de un usuario"""
    # Verificar que se proporcione el email del usuario
    if "usuario_email" not in producto:
        raise HTTPException(status_code=400, detail="usuario_email es requerido")
    
    # Verificar si ya existe en favoritos del usuario (por nombre)
    existente = await favoritos_col.find_one({
        "usuario_email": producto["usuario_email"],
        "nombre": producto["nombre"]
    })
    if existente:
        raise HTTPException(status_code=400, detail="El producto ya está en favoritos")
    
    result = await favoritos_col.insert_one(producto)
    return {"_id": str(result.inserted_id), "message": "Producto agregado a favoritos"}

@app.delete("/favoritos/{id_favorito}")
async def eliminar_de_favoritos(id_favorito: str, usuario_email: str = None):
    """Elimina un producto de favoritos de un usuario"""
    query = {"_id": ObjectId(id_favorito)}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    result = await favoritos_col.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")
    return {"status": "ok"}

@app.delete("/favoritos")
async def vaciar_favoritos(usuario_email: str = None):
    """Vacía los favoritos de un usuario"""
    query = {}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    await favoritos_col.delete_many(query)
    return {"status": "Favoritos vaciados"}


# --- USUARIOS ---
@app.post("/usuarios/registro")
async def registrar_usuario(usuario: dict = Body(...)):
    """Registra un nuevo usuario"""
    # Verificar si el correo ya existe
    existente = await usuarios_col.find_one({"correo": usuario["correo"]})
    if existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    # Verificar si el RUT ya existe
    if "rut" in usuario:
        existente_rut = await usuarios_col.find_one({"rut": usuario["rut"]})
        if existente_rut:
            raise HTTPException(status_code=400, detail="El RUT ya está registrado")
    
    # Crear nombre de usuario único si no se proporciona
    if "usuario" not in usuario or not usuario["usuario"]:
        import time
        nombres = usuario.get("nombres", "").lower().replace(" ", "")
        apellidos = usuario.get("apellidos", "").lower().replace(" ", "")
        timestamp = int(time.time())
        usuario["usuario"] = f"{nombres}_{apellidos}_{timestamp}"
    
    # Hashear la contraseña antes de guardarla
    password_original = usuario.pop("password", "")
    usuario["password_hash"] = hash_password(password_original)
    
    # Insertar usuario
    result = await usuarios_col.insert_one(usuario)
    usuario_creado = await usuarios_col.find_one({"_id": result.inserted_id})
    
    return {
        "_id": str(result.inserted_id),
        "message": "Usuario registrado exitosamente",
        "usuario": serializar_usuario(usuario_creado)
    }

@app.post("/usuarios/login")
async def login_usuario(credenciales: dict = Body(...)):
    """Inicia sesión de un usuario"""
    correo = credenciales.get("correo", "")
    password = credenciales.get("password", "")
    
    if not correo or not password:
        raise HTTPException(status_code=400, detail="Correo y contraseña son requeridos")
    
    # Buscar usuario por correo
    usuario = await usuarios_col.find_one({"correo": correo})
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    
    # Verificar contraseña
    password_hash = hash_password(password)
    if usuario.get("password_hash") != password_hash:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    
    return {
        "message": "Inicio de sesión exitoso",
        "usuario": serializar_usuario(usuario)
    }

@app.get("/usuarios/perfil/{correo}")
async def obtener_perfil(correo: str):
    """Obtiene el perfil de un usuario por correo"""
    usuario = await usuarios_col.find_one({"correo": correo})
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return serializar_usuario(usuario)

@app.put("/usuarios/perfil/{correo}")
async def actualizar_perfil(correo: str, datos: dict = Body(...)):
    """Actualiza el perfil de un usuario"""
    # No permitir cambiar correo ni contraseña directamente
    datos.pop("correo", None)
    datos.pop("password", None)
    datos.pop("password_hash", None)
    
    result = await usuarios_col.update_one(
        {"correo": correo},
        {"$set": datos}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario_actualizado = await usuarios_col.find_one({"correo": correo})
    return {
        "message": "Perfil actualizado exitosamente",
        "usuario": serializar_usuario(usuario_actualizado)
    }

# --- EMPLEADOS ---
@app.post("/empleados")
async def crear_empleado(empleado: dict = Body(...)):
    """Crea un empleado para el portal de empleados."""
    requerido = ["nombre", "email", "rut", "rol"]
    for campo in requerido:
        if not empleado.get(campo):
            raise HTTPException(status_code=400, detail=f"Campo requerido: {campo}")

    # Validaciones básicas
    # RUT chileno simple formato 12345678-9
    import re
    if not re.match(r"^\d{7,8}-[0-9kK]$", empleado.get("rut", "")):
        raise HTTPException(status_code=400, detail="RUT inválido (formato 12345678-9)")

    # Evitar duplicados por email o rut
    existente = await empleados_col.find_one({"$or": [{"email": empleado["email"]}, {"rut": empleado["rut"]}]})
    if existente:
        raise HTTPException(status_code=400, detail="Empleado ya existe (correo o RUT)")

    # Estado por defecto
    if "estado" not in empleado:
        empleado["estado"] = "activo"

    result = await empleados_col.insert_one(empleado)
    return {"_id": str(result.inserted_id)}

# Cambiar contraseña de usuario
@app.put("/usuarios/perfil/{correo}/password")
async def cambiar_password(correo: str, datos: dict = Body(...)):
    """Cambia la contraseña del usuario validando la actual."""
    password_actual = datos.get("password_actual", "")
    password_nueva = datos.get("password_nueva", "")

    if not password_actual or not password_nueva:
        raise HTTPException(status_code=400, detail="password_actual y password_nueva son requeridos")

    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar contraseña actual
    if usuario.get("password_hash") != hash_password(password_actual):
        raise HTTPException(status_code=401, detail="La contraseña actual es incorrecta")

    # Actualizar por nueva contraseña
    nuevo_hash = hash_password(password_nueva)
    await usuarios_col.update_one({"correo": correo}, {"$set": {"password_hash": nuevo_hash}})

    return {"message": "Contraseña actualizada exitosamente"}

# --- CUPONES ---
@app.get("/cupones/{codigo}")
async def validar_cupon(codigo: str):
    """Valida un cupón y retorna su efecto. Implementación básica con lista blanca.
    tipos soportados: free_shipping, percent (value=0-100), fixed (value en CLP)
    """
    codigo_norm = (codigo or "").strip().upper()
    cupones = {
        "LIBREENVIO": {"type": "free_shipping", "label": "Envío gratis"},
        "ENVIOGRATIS": {"type": "free_shipping", "label": "Envío gratis"},
        "DESCUENTO10": {"type": "percent", "value": 10, "label": "10% de descuento"},
        "MENOS2000": {"type": "fixed", "value": 2000, "label": "$2.000 de descuento"},
    }
    data = cupones.get(codigo_norm)
    if not data:
        raise HTTPException(status_code=404, detail="Cupón inválido o expirado")
    return {"code": codigo_norm, **data}

# --- MEDIOS DE PAGO POR USUARIO ---
@app.get("/usuarios/{correo}/medios_pago")
async def listar_medios_pago(correo: str):
    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    medios = usuario.get("medios_pago", [])
    # Normalizar _id a string si existen
    for m in medios:
        if isinstance(m.get("_id"), ObjectId):
            m["_id"] = str(m["_id"])
    return medios

@app.post("/usuarios/{correo}/medios_pago")
async def agregar_medio_pago(correo: str, medio: dict = Body(...)):
    """Agrega un medio de pago al usuario. No almacena el número completo, solo últimos 4 y máscara."""
    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    tipo = (medio.get("tipo") or "tarjeta").lower()
    titular = medio.get("titular", "")
    numero = (medio.get("numero") or "").replace(" ", "")
    vencimiento = medio.get("vencimiento", "")  # formato MM/AA
    marca = medio.get("marca", "")

    if tipo == "tarjeta":
        if not numero or len(numero) < 12:
            raise HTTPException(status_code=400, detail="Número de tarjeta inválido")
        last4 = numero[-4:]
        numero_enmascarado = "**** **** **** " + last4
    else:
        last4 = ""
        numero_enmascarado = ""

    nuevo_medio = {
        "_id": ObjectId(),
        "tipo": tipo,
        "titular": titular,
        "marca": marca,
        "vencimiento": vencimiento,
        "numero_enmascarado": numero_enmascarado,
        "last4": last4
    }

    await usuarios_col.update_one(
        {"correo": correo},
        {"$push": {"medios_pago": nuevo_medio}}
    )

    nuevo_medio["_id"] = str(nuevo_medio["_id"])  # serializar
    return {"message": "Medio de pago agregado", "medio": nuevo_medio}

@app.put("/usuarios/{correo}/medios_pago/{medio_id}")
async def actualizar_medio_pago(correo: str, medio_id: str, cambios: dict = Body(...)):
    """Actualiza campos editables del medio de pago (titular, marca, vencimiento)."""
    campos_permitidos = {"titular", "marca", "vencimiento"}
    set_data = {k: v for k, v in cambios.items() if k in campos_permitidos}
    if not set_data:
        raise HTTPException(status_code=400, detail="No hay campos válidos para actualizar")

    result = await usuarios_col.update_one(
        {"correo": correo, "medios_pago._id": ObjectId(medio_id)},
        {"$set": {**{f"medios_pago.$.{k}": v for k, v in set_data.items()}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Medio de pago no encontrado")
    return {"message": "Medio de pago actualizado"}

@app.delete("/usuarios/{correo}/medios_pago/{medio_id}")
async def eliminar_medio_pago(correo: str, medio_id: str):
    result = await usuarios_col.update_one(
        {"correo": correo},
        {"$pull": {"medios_pago": {"_id": ObjectId(medio_id)}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Medio de pago no encontrado")
    return {"message": "Medio de pago eliminado"}