from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from fastapi import Body

# --- Importaciones de capas ---
# Repositorios (acceso a datos)
from repositories.database import (
    productos_col, carrito_col, favoritos_col, usuarios_col,
    empleados_col, cupones_col, ordenes_col, tokens_recuperacion_col
)

# Servicios (lógica de negocio)
from services.productos_service import ProductosService
from services.carrito_service import CarritoService
from services.envio_service import calcular_costo_envio

# Modelos (serializadores y utilidades)
from models.serializers import (
    serializar_producto, serializar_carrito, serializar_favorito,
    serializar_usuario
)
from models.auth import hash_password, es_super_usuario

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Inicializar servicios ---
productos_service = ProductosService()
carrito_service = CarritoService()

# --- NOTA: Funciones movidas a capas ---
# Serializadores → models/serializers.py
# Autenticación → models/auth.py
# Cálculo de envío → services/envio_service.py
# Acceso a datos → repositories/database.py

# --- PRODUCTOS ---
# Controladores: Reciben peticiones HTTP y delegan a servicios
@app.get("/productos")
async def obtener_productos():
    """Controlador: Obtiene todos los productos"""
    return await productos_service.obtener_todos()

@app.post("/productos")
async def agregar_producto(producto: dict = Body(...)):
    """Controlador: Crea un nuevo producto"""
    result_id = await productos_service.crear(producto)
    return {"_id": str(result_id)}

@app.put("/productos/{id_producto}")
async def actualizar_producto(id_producto: str, producto: dict = Body(...)):
    """Controlador: Actualiza un producto"""
    actualizado = await productos_service.actualizar(id_producto, producto)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "ok"}

@app.delete("/productos/{id_producto}")
async def eliminar_producto(id_producto: str):
    """Controlador: Elimina un producto"""
    eliminado = await productos_service.eliminar(id_producto)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "ok"}


# --- CARRITO ---
# Controladores: Reciben peticiones HTTP y delegan a servicios
@app.get("/carrito")
async def obtener_carrito(usuario_email: str = None):
    """Controlador: Obtiene el carrito de un usuario"""
    return await carrito_service.obtener_por_usuario(usuario_email)

@app.post("/carrito")
async def agregar_al_carrito(item: dict):
    """Controlador: Agrega un producto al carrito"""
    try:
        result_id = await carrito_service.agregar_item(item)
        return {"_id": str(result_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        "usuario": serializar_usuario_helper(usuario_creado)
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
        "usuario": serializar_usuario_helper(usuario)
    }

@app.get("/usuarios/perfil/{correo}")
async def obtener_perfil(correo: str):
    """Obtiene el perfil de un usuario por correo"""
    usuario = await usuarios_col.find_one({"correo": correo})
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return serializar_usuario_helper(usuario)

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

# --- VALIDACIÓN DE CORREO ---
@app.post("/usuarios/validar-correo")
async def validar_correo(datos: dict = Body(...)):
    """
    Valida si un correo electrónico existe y está registrado en el sistema.
    Simula validación de correo (en producción usaría servicio de email real).
    """
    correo = datos.get("correo", "").strip().lower()
    
    if not correo:
        raise HTTPException(status_code=400, detail="Correo es requerido")
    
    # Validar formato básico de email
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
        return {
            "valido": False,
            "existe": False,
            "mensaje": "Formato de correo inválido"
        }
    
    # Verificar si el correo existe en la base de datos
    usuario = await usuarios_col.find_one({"correo": correo})
    
    if usuario:
        return {
            "valido": True,
            "existe": True,
            "mensaje": "Correo válido y registrado"
        }
    else:
        return {
            "valido": True,
            "existe": False,
            "mensaje": "Correo válido pero no registrado"
        }

# --- SOLICITUD DE CAMBIO DE CONTRASEÑA (Olvidé mi contraseña) ---
@app.post("/usuarios/solicitar-cambio-password")
async def solicitar_cambio_password(datos: dict = Body(...)):
    """
    Genera un token de recuperación y simula el envío de email con link.
    En producción, enviaría un email real con el link.
    """
    correo = datos.get("correo", "").strip().lower()
    
    if not correo:
        raise HTTPException(status_code=400, detail="Correo es requerido")
    
    # Verificar que el usuario existe
    usuario = await usuarios_col.find_one({"correo": correo})
    if not usuario:
        # Por seguridad, no revelamos si el correo existe o no
        return {
            "mensaje": "Si el correo existe, se enviará un link de recuperación",
            "token_simulado": None  # En producción no se retorna
        }
    
    # Generar token único
    import secrets
    import datetime
    token = secrets.token_urlsafe(32)
    
    # Guardar token en base de datos (válido por 1 hora)
    expiracion = datetime.datetime.now() + datetime.timedelta(hours=1)
    await tokens_recuperacion_col.insert_one({
        "correo": correo,
        "token": token,
        "expiracion": expiracion,
        "usado": False,
        "fecha_creacion": datetime.datetime.now()
    })
    
    # SIMULAR envío de email (en producción usarías un servicio real)
    # Aquí solo retornamos el link para desarrollo/pruebas
    link_recuperacion = f"http://127.0.0.1:8000/reset-password.html?token={token}"
    
    print(f"[SIMULACIÓN EMAIL] Para: {correo}")
    print(f"[SIMULACIÓN EMAIL] Asunto: Recuperación de contraseña - Libre & Rico")
    print(f"[SIMULACIÓN EMAIL] Link: {link_recuperacion}")
    print(f"[SIMULACIÓN EMAIL] En producción, este link se enviaría por email real")
    
    # En producción, retornarías solo un mensaje genérico
    return {
        "mensaje": "Si el correo existe, se enviará un link de recuperación",
        "token_simulado": token,  # Solo para desarrollo, eliminar en producción
        "link_simulado": link_recuperacion  # Solo para desarrollo
    }

# --- CAMBIAR CONTRASEÑA CON TOKEN ---
@app.post("/usuarios/cambiar-password-token")
async def cambiar_password_con_token(datos: dict = Body(...)):
    """
    Cambia la contraseña usando un token de recuperación.
    Se usa cuando el usuario hace clic en el link del email.
    """
    token = datos.get("token", "")
    password_nueva = datos.get("password_nueva", "")
    
    if not token or not password_nueva:
        raise HTTPException(status_code=400, detail="Token y password_nueva son requeridos")
    
    # Buscar token válido
    import datetime
    token_doc = await tokens_recuperacion_col.find_one({
        "token": token,
        "usado": False,
        "expiracion": {"$gt": datetime.datetime.now()}
    })
    
    if not token_doc:
        raise HTTPException(
            status_code=400, 
            detail="Token inválido o expirado. Solicita un nuevo link de recuperación."
        )
    
    correo = token_doc["correo"]
    
    # Validar formato de contraseña (mínimo 8 caracteres, 1 mayúscula, 1 dígito)
    import re
    if not re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password_nueva):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener mínimo 8 caracteres, 1 mayúscula y 1 dígito"
        )
    
    # Actualizar contraseña
    nuevo_hash = hash_password(password_nueva)
    await usuarios_col.update_one(
        {"correo": correo},
        {"$set": {"password_hash": nuevo_hash}}
    )
    
    # Marcar token como usado
    await tokens_recuperacion_col.update_one(
        {"token": token},
        {"$set": {"usado": True}}
    )
    
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

# --- ÓRDENES Y PAGOS ---
def serializar_orden(orden):
    """Serializa una orden para respuesta JSON"""
    return {
        "_id": str(orden["_id"]),
        "usuario_email": orden.get("usuario_email", ""),
        "productos": orden.get("productos", []),
        "subtotal": orden.get("subtotal", 0),
        "descuento": orden.get("descuento", 0),
        "envio": orden.get("envio", 0),
        "total": orden.get("total", 0),
        "estado": orden.get("estado", "pendiente"),
        "medio_pago_id": str(orden.get("medio_pago_id", "")) if orden.get("medio_pago_id") else None,
        "metodo_pago_usado": orden.get("metodo_pago_usado", "tarjeta_guardada"),
        "fecha_creacion": orden.get("fecha_creacion", ""),
        "fecha_pago": orden.get("fecha_pago", ""),
        "fecha_cancelacion": orden.get("fecha_cancelacion", ""),
        "cupon_codigo": orden.get("cupon_codigo", ""),
        "direccion_envio": orden.get("direccion_envio", ""),
        "distancia_km": orden.get("distancia_km"),
        "dentro_radio_envio": orden.get("dentro_radio_envio")
    }

@app.get("/ordenes/calcular-envio")
async def calcular_envio_orden(usuario_email: str):
    """
    Calcula el costo de envío para un usuario basado en su dirección o coordenadas.
    Retorna el costo de envío, distancia y si está dentro del radio.
    """
    if not usuario_email:
        raise HTTPException(status_code=400, detail="usuario_email es requerido")
    
    # Obtener usuario y su dirección/coordenadas
    usuario = await usuarios_col.find_one({"correo": usuario_email})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Priorizar coordenadas guardadas (más rápido y preciso)
    lat = usuario.get("latitud")
    lon = usuario.get("longitud")
    direccion = usuario.get("domicilio", "")
    
    # Si tiene coordenadas, usarlas directamente (más rápido)
    if lat is not None and lon is not None:
        resultado_envio = await calcular_costo_envio(lat_cliente=lat, lon_cliente=lon)
    else:
        # Si no tiene coordenadas, geocodificar la dirección
        resultado_envio = await calcular_costo_envio(direccion_cliente=direccion)
    
    return resultado_envio

@app.post("/ordenes")
async def crear_orden(orden_data: dict = Body(...)):
    """Crea una nueva orden a partir del carrito del usuario"""
    usuario_email = orden_data.get("usuario_email")
    if not usuario_email:
        raise HTTPException(status_code=400, detail="usuario_email es requerido")
    
    # Obtener carrito del usuario
    carrito_items = []
    async for item in carrito_col.find({"usuario_email": usuario_email}):
        carrito_items.append({
            "nombre": item.get("nombre", ""),
            "precio": item.get("precio", 0),
            "cantidad": item.get("cantidad", 1),
            "imagen": item.get("imagen", "")
        })
    
    if not carrito_items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")
    
    # Calcular costo de envío según distancia
    usuario = await usuarios_col.find_one({"correo": usuario_email})
    direccion = usuario.get("domicilio", "") if usuario else ""
    lat_usuario = usuario.get("latitud") if usuario else None
    lon_usuario = usuario.get("longitud") if usuario else None
    
    # Si se proporciona envío explícitamente (y no es None), usarlo (para cupones de envío gratis)
    envio_proporcionado = orden_data.get("envio")
    if envio_proporcionado is not None and envio_proporcionado != "":
        try:
            envio = int(envio_proporcionado)
            distancia_info = None
        except (ValueError, TypeError):
            # Si no es un número válido, calcular según distancia
            # Priorizar coordenadas si están disponibles
            if lat_usuario is not None and lon_usuario is not None:
                resultado_envio = await calcular_costo_envio(lat_cliente=lat_usuario, lon_cliente=lon_usuario)
            else:
                resultado_envio = await calcular_costo_envio(direccion_cliente=direccion)
            envio = resultado_envio["costo"]
            distancia_info = {
                "distancia_km": resultado_envio.get("distancia_km"),
                "dentro_radio": resultado_envio.get("dentro_radio")
            }
    else:
        # Calcular envío según distancia
        # Priorizar coordenadas si están disponibles (más rápido y preciso)
        if lat_usuario is not None and lon_usuario is not None:
            resultado_envio = await calcular_costo_envio(lat_cliente=lat_usuario, lon_cliente=lon_usuario)
        else:
            resultado_envio = await calcular_costo_envio(direccion_cliente=direccion)
        envio = resultado_envio["costo"]
        distancia_info = {
            "distancia_km": resultado_envio.get("distancia_km"),
            "dentro_radio": resultado_envio.get("dentro_radio")
        }
    
    # Calcular totales
    subtotal = sum(item["precio"] * item.get("cantidad", 1) for item in carrito_items)
    descuento = orden_data.get("descuento", 0)
    total = max(0, subtotal - descuento) + envio
    
    # Crear orden
    from datetime import datetime
    nueva_orden = {
        "usuario_email": usuario_email,
        "productos": carrito_items,
        "subtotal": subtotal,
        "descuento": descuento,
        "envio": envio,
        "total": total,
        "estado": "pendiente",
        "medio_pago_id": orden_data.get("medio_pago_id"),
        "fecha_creacion": datetime.now().isoformat(),
        "cupon_codigo": orden_data.get("cupon_codigo", ""),
        "direccion_envio": direccion,
        "distancia_km": distancia_info.get("distancia_km") if distancia_info else None,
        "dentro_radio_envio": distancia_info.get("dentro_radio") if distancia_info else None
    }
    
    result = await ordenes_col.insert_one(nueva_orden)
    orden_creada = await ordenes_col.find_one({"_id": result.inserted_id})
    
    return {
        "message": "Orden creada exitosamente",
        "orden": serializar_orden(orden_creada)
    }

@app.post("/ordenes/{orden_id}/pagar")
async def procesar_pago(orden_id: str, pago_data: dict = Body(...)):
    """Procesa el pago de una orden"""
    orden = await ordenes_col.find_one({"_id": ObjectId(orden_id)})
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if orden.get("estado") != "pendiente":
        raise HTTPException(status_code=400, detail=f"La orden ya está {orden.get('estado')}")
    
    usuario_email = orden.get("usuario_email")
    medio_pago_id = pago_data.get("medio_pago_id")
    
    # Verificar que el medio de pago pertenece al usuario
    if medio_pago_id:
        usuario = await usuarios_col.find_one({"correo": usuario_email})
        if usuario:
            medios_pago = usuario.get("medios_pago", [])
            medio_encontrado = any(str(m.get("_id")) == medio_pago_id for m in medios_pago)
            if not medio_encontrado:
                raise HTTPException(status_code=400, detail="Medio de pago no válido")
    
    # Simular procesamiento de pago (aquí integrarías con pasarela real)
    # Por ahora, marcamos como pagado directamente
    from datetime import datetime
    metodo_pago_usado = pago_data.get("metodo_pago", "tarjeta_guardada")  # mercadopago, applepay, tarjeta_guardada
    
    update_data = {
        "estado": "pagado",
        "fecha_pago": datetime.now().isoformat(),
        "metodo_pago_usado": metodo_pago_usado
    }
    
    if medio_pago_id:
        update_data["medio_pago_id"] = ObjectId(medio_pago_id)
    else:
        update_data["medio_pago_id"] = None
    
    await ordenes_col.update_one(
        {"_id": ObjectId(orden_id)},
        {"$set": update_data}
    )
    
    # Vaciar carrito del usuario después del pago exitoso
    await carrito_col.delete_many({"usuario_email": usuario_email})
    
    orden_actualizada = await ordenes_col.find_one({"_id": ObjectId(orden_id)})
    
    return {
        "message": "Pago procesado exitosamente",
        "orden": serializar_orden(orden_actualizada)
    }

@app.get("/ordenes")
async def obtener_ordenes(usuario_email: str = None):
    """Obtiene las órdenes de un usuario o todas si es super usuario"""
    query = {}
    if usuario_email:
        query["usuario_email"] = usuario_email
    
    ordenes = []
    async for orden in ordenes_col.find(query).sort("fecha_creacion", -1):
        ordenes.append(serializar_orden(orden))
    
    return ordenes

@app.get("/ordenes/{orden_id}")
async def obtener_orden(orden_id: str):
    """Obtiene una orden específica"""
    orden = await ordenes_col.find_one({"_id": ObjectId(orden_id)})
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    return serializar_orden(orden)

@app.put("/ordenes/{orden_id}/cancelar")
async def cancelar_orden(orden_id: str):
    """Cancela una orden pendiente"""
    orden = await ordenes_col.find_one({"_id": ObjectId(orden_id)})
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if orden.get("estado") != "pendiente":
        raise HTTPException(status_code=400, detail=f"No se puede cancelar una orden que está {orden.get('estado')}. Solo se pueden cancelar órdenes pendientes.")
    
    from datetime import datetime
    await ordenes_col.update_one(
        {"_id": ObjectId(orden_id)},
        {
            "$set": {
                "estado": "cancelado",
                "fecha_cancelacion": datetime.now().isoformat()
            }
        }
    )
    
    orden_actualizada = await ordenes_col.find_one({"_id": ObjectId(orden_id)})
    
    return {
        "message": "Orden cancelada exitosamente",
        "orden": serializar_orden(orden_actualizada)
    }