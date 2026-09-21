import sys
import os
from pathlib import Path
from collections import Counter

# Agrega backend/ a la ruta de Python para que "from src..." funcione
# (este archivo está en backend/src/services/, así que backend es parents[2])
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests
from src.config import config

# Si config.py aún no tiene TRUCKNET_TRANS_URL, la toma del .env directo
TRANS_URL = getattr(config, "TRUCKNET_TRANS_URL", None) or os.getenv("TRUCKNET_TRANS_URL")


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
            TRANS_URL,
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


if __name__ == "__main__":
    sesion = login()
    if sesion:
        print(f"Token vence: {sesion.get('expiresAt')}")

        rows = get_transactions(sesion["token"])
        if rows is not None:
            print(f"Total filas: {len(rows)}")
            print(f"transactionId únicos: {len({r['transactionId'] for r in rows})}")

            llaves = Counter((r["transactionId"], r["productCode"]) for r in rows)
            repetidas = {k: v for k, v in llaves.items() if v > 1}
            print(f"Llaves (transactionId, productCode) únicas: {len(llaves)}")
            print(f"Llaves repetidas: {len(repetidas)}")

            # Detalle de las filas repetidas para compararlas lado a lado
            for (tid, pcode), veces in repetidas.items():
                print(f"\n--- transactionId={tid}, productCode={pcode} ({veces} filas) ---")
                print("fecha | tarjeta | vehículo | galones | monto | odómetro")
                for r in rows:
                    if r["transactionId"] == tid and r["productCode"] == pcode:
                        print(
                            r["transactionDate"], "|",
                            r["cardNumber"], "|",
                            r["vehicleNumber"], "|",
                            r["gallons"], "|",
                            r["totalAmount"], "|",
                            r["odometer"],
                        )