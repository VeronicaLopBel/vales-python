import requests
from datetime import datetime, timedelta
from src.config import config
from src.database import db

# Filtramos por productName -- ajustaremos esta lista en cuanto veamos datos reales,
# ya que "Diesel #2" no es exactamente igual a los textos viejos "DIESEL"/"CNG"/etc.
PRODUCTOS_VALIDOS = ["DIESEL", "CNG", "ULSD-DUTY FREE", "B20 DSL", "DEF"]

REMAPEO_TRUCKID = {
    "4": "307", "12": "303", "17": "221", "18": "235",
    "19": "217", "20": "306", "22": "310", "23": "220",
}


def login():
    """Login con Basic Auth. La respuesta trae 'token' directo, según la doc."""
    response = requests.post(
        config.TRUCKNET_LOGIN_URL,
        auth=(config.TRUCKNET_USER, config.TRUCKNET_PASSWORD),
    )
    response.raise_for_status()
    data = response.json()
    return data["token"]


def descargar_transacciones(token, fecha_desde, fecha_hasta):
    """GET /transactions con query params, según la doc (antes se armaba distinto)."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "fromDate": fecha_desde,   # formato YYYY-MM-DD
        "toDate": fecha_hasta,
        "onlyNew": "true",
    }
    response = requests.get(config.TRUCKNET_TRANS_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def procesar(fecha_desde, fecha_hasta):
    token = login()
    transacciones = descargar_transacciones(token, fecha_desde, fecha_hasta)

    descargados = len(transacciones)
    no_validos = 0
    repetidos = 0
    anadidos = 0

    conn = db.get_connection()

    for t in transacciones:
        producto = t.get("productName", "")
        if not any(p in producto.upper() for p in PRODUCTOS_VALIDOS):
            no_validos += 1
            continue

        truckid_original = str(t["vehicleNumber"])
        notes = ""
        if truckid_original in REMAPEO_TRUCKID:
            notes = f"Original truck number {truckid_original}"
            truckid = REMAPEO_TRUCKID[truckid_original]
        else:
            truckid = truckid_original

        fecha = t["transactionDate"]  # ej. "2026-03-10T14:23:00"
        vale_id = f"{truckid_original}_{fecha}"

        if db.vale_existe(conn, vale_id):
            repetidos += 1
            continue

        fecha_solo = fecha[:10]
        hora = fecha[11:16]
        pudate = datetime.now().strftime("%Y-%m-%d %H:%M")

        vale = {
            "id": vale_id,
            "sitestate": t["state"],
            "truckid": truckid,
            "fecha": fecha_solo,
            "hora": hora,
            "galons": t["gallons"],
            "odometro": t["odometer"],
            "grate": t["pricePerUnit"],
            "cardno": str(t["cardNumber"]),
            "sitecode": str(t["siteId"]),
            "status": "0",
            "company": "TRUCK NET",
            "notes": notes,
            "pudate": pudate,
        }
        db.insertar_vale(conn, vale)
        anadidos += 1

    conn.close()
    return {"descargados": descargados, "no_validos": no_validos, "repetidos": repetidos, "anadidos": anadidos}


if __name__ == "__main__":
    hoy = datetime.now()
    fecha_hasta = hoy.strftime("%Y-%m-%d")
    fecha_desde = (hoy - timedelta(days=6)).strftime("%Y-%m-%d")
    resultado = procesar(fecha_desde, fecha_hasta)
    print(f"Rango: {fecha_desde} a {fecha_hasta}")
    print("Resultado TruckNet:", resultado)