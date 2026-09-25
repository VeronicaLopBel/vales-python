import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

# Agrega backend/ a la ruta de Python (este archivo está en backend/src/services/)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests
from src.config import config
from src.database import db


def _normalizar(texto):
    """Quita espacios repetidos y pasa a mayúsculas
    (la API devuelve 'ULTRA  LOW SULFUR DIESEL' con doble espacio)."""
    return " ".join(str(texto).split()).upper()


# Mismas reglas que el Java: el producto es válido si su descripción
# CONTIENE alguna de estas palabras
PALABRAS_VALIDAS = ("DIESEL", "CNG", "ULSD-DUTY FREE", "B20 DSL")

# Remapeo de camiones de TruckNet (Helper del Java): original -> el que se guarda
REMAPEO_TRUCKID_TRUCKNET = {
    "4": "307", "12": "303", "17": "221", "18": "235",
    "19": "217", "20": "306", "22": "310", "23": "220",
}

# El Java pedía los últimos 6 días
DIAS_VENTANA = 6


def login():
    try:
        response = requests.post(
            config.TRUCKNET_LOGIN_URL,
            auth=(config.TRUCKNET_USER, config.TRUCKNET_PASSWORD),
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] No se pudo conectar al servidor: {e}")
        return None

    print(f"Login - status: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        return None

    try:
        return response.json()
    except ValueError:
        print("[AVISO] No es JSON:")
        print(response.text)
        return None


def get_transactions(token):
    try:
        response = requests.get(
            config.TRUCKNET_TRANS_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] No se pudo conectar al servidor: {e}")
        return None

    print(f"Transacciones - status: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()


def procesar(origen="manual", dry_run=True, desde=None, hasta=None, dias=DIAS_VENTANA):
    """Descarga las transacciones de TruckNet y las guarda en vales.

    dry_run=True (por defecto): NO inserta nada, solo simula y reporta.
    dry_run=False: inserta de verdad.
    desde: fecha mínima "AAAA-MM-DD". Si no se da, se usan los últimos `dias`.
    """
    if desde is None:
        desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    if hasta is None:
        hasta = datetime.now().strftime("%Y-%m-%d")

    sesion = login()
    if not sesion:
        raise RuntimeError("No se pudo hacer login en TruckNet")

    todas = get_transactions(sesion["token"])
    if todas is None:
        raise RuntimeError("No se pudieron descargar las transacciones de TruckNet")

    rows = [r for r in todas if desde <= r.get("transactionDate", "")[:10] <= hasta]

    no_validos = 0
    repetidos = 0
    anadidos = 0
    remapeados = 0
    vistos = set()                     # IDs ya vistos en esta misma corrida
    por_producto = defaultdict(list)   # producto -> lista de precios
    fechas = []
    muestra = []

    conn = db.get_connection()
    try:
        for r in rows:
            producto = _normalizar(r.get("productName", ""))
            if not any(p in producto for p in PALABRAS_VALIDAS):
                no_validos += 1
                continue

            fecha = r.get("transactionDate", "")
            fecha_solo = fecha[:10]
            hora = fecha[11:16]

            # El ID usa el camión ORIGINAL, como el Java (se arma antes del remapeo)
            truckid_original = str(r.get("vehicleNumber", ""))
            vale_id = f"{truckid_original}_{fecha_solo} {hora}"

            if vale_id in vistos or db.vale_existe(conn, vale_id):
                repetidos += 1
                continue
            vistos.add(vale_id)

            notes = ""
            truckid = truckid_original
            if truckid_original in REMAPEO_TRUCKID_TRUCKNET:
                notes = f"Original truck number {truckid_original}"
                truckid = REMAPEO_TRUCKID_TRUCKNET[truckid_original]
                remapeados += 1

            vale = {
                "id": vale_id,
                "sitestate": r.get("state", ""),
                "truckid": truckid,
                "fecha": fecha_solo,
                "hora": hora,
                "galons": round(float(r.get("gallons") or 0), 3),
                "odometro": int(float(r.get("odometer") or 0)),
                "grate": float(r.get("pricePerUnit") or 0),
                "cardno": str(r.get("cardNumber", "")),
                "sitecode": str(r.get("siteId", "")),
                "status": "0",
                "company": "TRUCK NET",
                "notes": notes,
                "pudate": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

            por_producto[producto].append(vale["grate"])
            fechas.append(fecha_solo)
            if len(muestra) < 5:
                muestra.append(vale)

            if not dry_run:
                db.insertar_vale(conn, vale)
            anadidos += 1
    finally:
        conn.close()

    if dry_run:
        print("\n=== SIMULACIÓN (no se insertó nada) ===")
        print(f"Ventana: desde {desde} "
              f"(la API devolvió {len(todas)} filas, {len(rows)} dentro de la ventana)")
        print(f"Se insertarían {anadidos} vales ({repetidos} ya existen)")
        print(f"Camiones remapeados: {remapeados}")
        if fechas:
            print(f"Rango de fechas: {min(fechas)} -> {max(fechas)}")
        print("\nPor producto (cantidad | precio mín - máx):")
        for producto, precios in por_producto.items():
            print(f"  {producto}: {len(precios)} | {min(precios)} - {max(precios)}")
        print("\nEjemplos de lo que se insertaría:")
        for v in muestra:
            print(" ", v)

    return {
        "descargados": len(rows),
        "no_validos": no_validos,
        "repetidos": repetidos,
        "anadidos": anadidos,
        "origen": origen,
        "dry_run": dry_run,
        "desde": desde,
    }


if __name__ == "__main__":
    real = "--real" in sys.argv
    desde = None
    if "--desde" in sys.argv:
        desde = sys.argv[sys.argv.index("--desde") + 1]

    resultado = procesar(origen="manual", dry_run=not real, desde=desde)
    print("\nResultado:", resultado)