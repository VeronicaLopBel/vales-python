import requests
from datetime import datetime, timedelta
from src.config import config
from src.database import db


def login(usuario, password):
    """Hace login en XIGA y regresa el token."""
    response = requests.post(
        config.XIGA_LOGIN_URL,
        json={"user": usuario, "password": password}
    )
    response.raise_for_status()
    data = response.json()
    return data["token"]


def descargar_consumos(token, fecha_desde, fecha_hasta):
    """Descarga los consumos de combustible entre dos fechas."""
    headers = {
        "accept": "text/plain",
        "Authorization": f"Bearer {token}",
    }
    body = {"fromDate": fecha_desde, "toDate": fecha_hasta}
    response = requests.post(config.XIGA_CONSUMPTIONS_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()


# Remapeo de camiones — solo aplica a la cuenta 1 (Helper2 en tu Java)
# La cuenta 2 (Helper3) no tenía ningún remapeo
REMAPEO_TRUCKID_CUENTA1 = {
    "202 MEX": "202", "200 BIN": "200", "197 BIN": "197", "252 BIN": "252",
    "267 BIN": "267", "278 TJ LOC": "278", "258 MEX": "258", "R015 BIN": "R015",
    "240 BIN": "240", "198 BIN": "198", "285 BIN": "285", "289 BIN": "289",
    "294 BIN": "294", "205 MEX": "205", "203 BIN": "203", "R018 BIN": "R018",
    "290BIN": "290", "318 BIN": "318", "243 BIN": "242", "R014 BIN": "R014",
    "248 BIN": "248", "239 BIN": "239", "286 BIN": "286", "284 BIN": "284",
    "296 BIN": "296", "292 BIN": "292", "264 BIN": "264", "256 BIN": "256",
    "293 BIN": "293", "283 BIN": "283", "291 BIN": "291", "76178D3": "R021",
    "R016 BIN": "R016", "269 BIN": "269", "161 TJ LOC": "161", "204 BIN": "204",
    "316 TJ LOC": "316",
}


def convertir_litros_a_galones(litros):
    galones = litros / 3.78541
    return round(galones, 3)


def calcular_tarifa_por_galon(monto, galones):
    return round(monto / galones, 3)


def procesar(usuario, password, fecha_desde, fecha_hasta, vehiculos_excluidos,
             remapeo_truckid=None, sitestate="BC"):
    """Procesa una cuenta XIGA: descarga consumos y guarda en DB."""
    remapeo_truckid = remapeo_truckid or {}

    token = login(usuario, password)
    consumos = descargar_consumos(token, fecha_desde, fecha_hasta)

    descargados = len(consumos)
    no_validos = 0
    repetidos = 0
    anadidos = 0

    conn = db.get_connection()

    for c in consumos:
        if "Diesel" not in c.get("product", ""):
            no_validos += 1
            continue

        vehicle = c.get("vehicle", "")
        if vehicle in vehiculos_excluidos:
            no_validos += 1
            continue

        vale_id = str(c.get("id", ""))
        if db.vale_existe(conn, vale_id):
            repetidos += 1
            continue

        truckid_original = c.get("economicNum", "")
        notes = ""
        if truckid_original in remapeo_truckid:
            notes = f"Original truck number {truckid_original}"
            truckid = remapeo_truckid[truckid_original]
        elif vehicle == "0157":
            notes = f"Tibor {vehicle}"
            truckid = "TIB"
        else:
            truckid = truckid_original

        galones = convertir_litros_a_galones(float(c.get("liters", 0)))
        tarifa = calcular_tarifa_por_galon(float(c.get("amount", 0)), galones)

        fecha = c.get("date", "")
        fecha_solo = fecha[:10]
        hora = fecha[11:16]
        pudate = datetime.now().strftime("%Y-%m-%d %H:%M")

        vale = {
            "id": vale_id,
            "sitestate": sitestate,
            "truckid": truckid,
            "fecha": fecha_solo,
            "hora": hora,
            "galons": galones,
            "odometro": c.get("kms", ""),
            "grate": tarifa,
            "cardno": c.get("secuence", ""),
            "sitecode": c.get("stationNumber", ""),
            "status": "0",
            "company": "XIGA",
            "notes": notes,
            "pudate": pudate,
        }
        db.insertar_vale(conn, vale)
        anadidos += 1

    conn.close()

    return {
        "descargados": descargados,
        "no_validos": no_validos,
        "repetidos": repetidos,
        "anadidos": anadidos,
    }


if __name__ == "__main__":
    hoy = datetime.now()
    fecha_desde = (hoy - timedelta(days=15)).strftime("%Y-%m-%d")
    fecha_hasta = hoy.strftime("%Y-%m-%d")

    resultado = procesar(
        usuario=config.XIGA1_USER,
        password=config.XIGA1_PASSWORD,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0125", "0106", "00157"],
        remapeo_truckid=REMAPEO_TRUCKID_CUENTA1,
    )
    print(f"Rango: {fecha_desde} a {fecha_hasta}")
    print("Resultado cuenta 1:", resultado)

    resultado2 = procesar(
        usuario=config.XIGA2_USER,
        password=config.XIGA2_PASSWORD,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0012", "0026"],
        remapeo_truckid=None,
    )
    print("Resultado cuenta 2:", resultado2)
