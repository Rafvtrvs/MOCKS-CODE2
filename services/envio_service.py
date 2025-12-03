"""
Servicio de Envío
Capa de lógica de negocio: cálculo de costos de envío
"""
import math
import httpx

# Configuración de envío
RESTAURANT_LAT = -33.4417
RESTAURANT_LON = -70.6400
DISTANCIA_LIMITE_KM = 5.0  # 5 km
COSTO_ENVIO_LEJOS = 3000  # $3000 si está a más de 5km
COSTO_ENVIO_CERCA = 0  # Gratis si está a 5km o menos

def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine.
    Retorna la distancia en kilómetros.
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencia de coordenadas
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distancia = R * c
    return distancia

async def geocodificar_direccion(direccion: str) -> tuple:
    """
    Convierte una dirección en coordenadas (latitud, longitud).
    Usa Nominatim (OpenStreetMap) que es gratuito.
    Retorna (lat, lon) o None si falla.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            "q": direccion,
            "format": "json",
            "limit": 1,
            "countrycodes": "cl"  # Solo Chile
        }
        headers = {
            "User-Agent": "LibreYRico/1.0"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return (lat, lon)
        return None
    except Exception as e:
        print(f"Error en geocodificación: {e}")
        return None

async def calcular_costo_envio(direccion_cliente: str = None, lat_cliente: float = None, lon_cliente: float = None) -> dict:
    """
    Calcula el costo de envío basado en la distancia desde el restaurante.
    Puede usar coordenadas directamente (más rápido) o geocodificar una dirección.
    Retorna: {
        "costo": int,
        "distancia_km": float,
        "dentro_radio": bool
    }
    """
    # Si se proporcionan coordenadas directamente, usarlas (más rápido y preciso)
    if lat_cliente is not None and lon_cliente is not None:
        distancia_km = calcular_distancia_haversine(
            RESTAURANT_LAT, RESTAURANT_LON,
            lat_cliente, lon_cliente
        )
        dentro_radio = distancia_km <= DISTANCIA_LIMITE_KM
        costo = COSTO_ENVIO_CERCA if dentro_radio else COSTO_ENVIO_LEJOS
        
        return {
            "costo": costo,
            "distancia_km": round(distancia_km, 2),
            "dentro_radio": dentro_radio,
            "mensaje": f"Envío {'gratis' if dentro_radio else f'${costo}'} (distancia: {round(distancia_km, 2)} km)"
        }
    
    # Si no hay coordenadas, intentar geocodificar la dirección
    if not direccion_cliente:
        return {
            "costo": COSTO_ENVIO_LEJOS,
            "distancia_km": None,
            "dentro_radio": False,
            "mensaje": "Dirección no proporcionada, se aplica costo de envío estándar"
        }
    
    # Geocodificar dirección del cliente
    coordenadas = await geocodificar_direccion(direccion_cliente)
    
    if not coordenadas:
        return {
            "costo": COSTO_ENVIO_LEJOS,
            "distancia_km": None,
            "dentro_radio": False,
            "mensaje": "No se pudo calcular la distancia, se aplica costo de envío estándar"
        }
    
    lat_cliente, lon_cliente = coordenadas
    distancia_km = calcular_distancia_haversine(
        RESTAURANT_LAT, RESTAURANT_LON,
        lat_cliente, lon_cliente
    )
    dentro_radio = distancia_km <= DISTANCIA_LIMITE_KM
    costo = COSTO_ENVIO_CERCA if dentro_radio else COSTO_ENVIO_LEJOS
    
    return {
        "costo": costo,
        "distancia_km": round(distancia_km, 2),
        "dentro_radio": dentro_radio,
        "mensaje": f"Envío {'gratis' if dentro_radio else f'${costo}'} (distancia: {round(distancia_km, 2)} km)"
    }



