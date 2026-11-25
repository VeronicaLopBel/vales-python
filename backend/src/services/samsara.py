import requests
from math import radians, sin, cos, sqrt, atan2
from src.config import config

BASE_URL = "https://api.samsara.com"


def _headers():
    return {"Authorization": f"Bearer {config.SAMSARA_TOKEN}"}


def listar_direcciones():
    """Trae TODAS las direcciones (geocercas) de Samsara, página por página."""
    direcciones = []
    after = None
    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after
        resp = requests.get(
            f"{BASE_URL}/addresses",
            headers=_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        cuerpo = resp.json()
        direcciones.extend(cuerpo.get("data", []))
        paginacion = cuerpo.get("pagination", {})
        if not paginacion.get("hasNextPage"):
            break
        after = paginacion.get("endCursor")
    return direcciones

def listar_vehiculos():
    """Trae todos los camiones de Samsara (id, nombre, VIN)."""
    vehiculos = []
    after = None
    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after
        resp = requests.get(
            f"{BASE_URL}/fleet/vehicles",
            headers=_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        cuerpo = resp.json()
        vehiculos.extend(cuerpo.get("data", []))
        paginacion = cuerpo.get("pagination", {})
        if not paginacion.get("hasNextPage"):
            break
        after = paginacion.get("endCursor")
    return vehiculos

def mapa_truckid_vin():
    """Regresa un diccionario { truckid: vin } usando el 'name' de Samsara como truckid."""
    vehiculos = listar_vehiculos()
    mapa = {}
    for v in vehiculos:
        nombre = v.get("name", "").strip()
        vin = v.get("vin", "")
        if nombre and vin:
            mapa[nombre] = vin
    return mapa

def mapa_truckid_id():
    """Regresa un diccionario { truckid: id_interno_samsara }."""
    vehiculos = listar_vehiculos()
    mapa = {}
    for v in vehiculos:
        nombre = v.get("name", "").strip()
        id_samsara = v.get("id", "")
        if nombre and id_samsara:
            mapa[nombre] = id_samsara
    return mapa

def ubicacion_en_fecha(vehiculo_id, fecha_hora_iso):
    """Consulta la ubicación GPS de un camión en un momento específico.
    fecha_hora_iso debe ir en formato: '2026-08-26T11:27:00Z'
    """
    resp = requests.get(
        f"{BASE_URL}/fleet/vehicles/stats",
        headers=_headers(),
        params={"vehicleIds": vehiculo_id, "types": "gps", "time": fecha_hora_iso},
        timeout=30,
    )
    resp.raise_for_status()
    cuerpo = resp.json()
    datos = cuerpo.get("data", [])
    if not datos:
        return None
    gps = datos[0].get("gps")
    if not gps:
        return None
    return gps.get("latitude"), gps.get("longitude")

def buscar_geocerca_real(vehiculo_id, inicio_utc, fin_utc):
    """Busca, en un rango de tiempo UTC, el primer punto donde el camión
    estuvo REALMENTE dentro de una geocerca de Samsara.
    inicio_utc y fin_utc deben ser strings tipo '2026-09-24T07:03:00Z'.
    Regresa el 'id' de la geocerca, o None si no encontró ninguna.
    """
    resp = requests.get(
        f"{BASE_URL}/assets/location-and-speed/stream",
        headers=_headers(),
        params={
            "ids": vehiculo_id,
            "startTime": inicio_utc,
            "endTime": fin_utc,
            "includeReverseGeo": "true",
            "includeGeofenceLookup": "true",
        },
        timeout=30,
    )
    resp.raise_for_status()
    puntos = resp.json().get("data", [])

    for punto in puntos:
        geofence = punto.get("location", {}).get("geofence")
        if geofence and geofence.get("id"):
            return geofence.get("id")
    return None

def _distancia_km(lat1, lon1, lat2, lon2):
    """Distancia en línea recta entre 2 puntos GPS (fórmula de Haversine)."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def geocerca_mas_cercana(lat, lon, direcciones):
    """De la lista de direcciones de Samsara, regresa la más cercana a (lat, lon)."""
    mejor = None
    mejor_distancia = None
    for d in direcciones:
        dlat = d.get("latitude")
        dlon = d.get("longitude")
        if dlat is None or dlon is None:
            continue
        distancia = _distancia_km(lat, lon, dlat, dlon)
        if mejor_distancia is None or distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor = d
    return mejor, mejor_distancia

def geocerca_dentro_de_radio(lat, lon, direcciones, radio_default_metros=150):
    """Busca, entre las direcciones de Samsara, la geocerca cuyo círculo
    REALMENTE contiene el punto (lat, lon) -- no solo la más cercana.
    Regresa (geocerca, distancia_km) o (None, None) si ninguna lo contiene.
    """
    mejor = None
    mejor_distancia = None
    for d in direcciones:
        dlat = d.get("latitude")
        dlon = d.get("longitude")
        if dlat is None or dlon is None:
            continue
        radio = (
            d.get("geofence", {}).get("circle", {}).get("radiusMeters")
            or radio_default_metros
        )
        distancia_km = _distancia_km(lat, lon, dlat, dlon)
        if distancia_km * 1000 <= radio:
            if mejor_distancia is None or distancia_km < mejor_distancia:
                mejor_distancia = distancia_km
                mejor = d
    return mejor, mejor_distancia

if __name__ == "__main__":
    ids = mapa_truckid_id()
    direcciones = listar_direcciones()

    truckid_prueba = "356"
    fecha_prueba = "2026-08-26T11:27:00Z"   # usa una fecha real de un vale de ese camión

    vehiculo_id = ids.get(truckid_prueba)
    print("ID Samsara del camión:", vehiculo_id)

    ubicacion = ubicacion_en_fecha(vehiculo_id, fecha_prueba)
    print("Ubicación en esa fecha:", ubicacion)

    if ubicacion:
        lat, lon = ubicacion
        geocerca, distancia = geocerca_mas_cercana(lat, lon, direcciones)
        print("Geocerca más cercana:", geocerca.get("name") if geocerca else None)
        print("Dirección:", geocerca.get("formattedAddress") if geocerca else None)
        print("Distancia (km):", round(distancia, 2) if distancia else None)