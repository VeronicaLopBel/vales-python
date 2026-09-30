import csv
import re
from datetime import datetime
from src.database import db
from src.services import samsara


MARCAS_CONOCIDAS = {
    "LOV": "Love's",
    "TRU": "TRUCKNET LLC",
}


def nombre_marca(nombre_geocerca):
    """Traduce el nombre de geocerca (ej. 'LOV643') a la marca real (ej. 'Love's')."""
    if not nombre_geocerca:
        return ""
    for prefijo, marca in MARCAS_CONOCIDAS.items():
        if nombre_geocerca.upper().startswith(prefijo):
            return marca
    return nombre_geocerca  # prefijo desconocido: se deja igual, para revisar después


def separar_direccion(full_address):
    """Separa 'Calle, Ciudad, ESTADO CP, PAIS' en sus 4 partes.
    Regresa (calle, ciudad, estado, codigo_postal).
    Por ahora funciona bien con direcciones de EE.UU.; las de México quedan
    pendientes de ajustar (formato distinto).
    """
    if not full_address:
        return "", "", "", ""

    partes = [p.strip() for p in full_address.split(",")]

    # Quita el país si viene al final
    paises = ("EE. UU.", "USA", "US")
    if partes and partes[-1].upper() in [p.upper() for p in paises]:
        partes = partes[:-1]

    if len(partes) < 3:
        return full_address, "", "", ""

    calle = partes[0]
    ciudad = partes[1]
    ultima = partes[-1]  # ej. "TX 75790"

    match = re.match(r"^([A-Za-z\.]+)\s*(\d{4,5})?$", ultima)
    if match:
        estado = match.group(1).strip()
        cp = match.group(2) or ""
    else:
        estado = ultima
        cp = ""

    return calle, ciudad, estado, cp
    
def generar_reporte(desde, hasta, ruta_salida="reporte_ifta.csv"):
    """Genera el CSV para Samsara con los vales entre 'desde' y 'hasta' (AAAA-MM-DD)."""

    print("Descargando vales de la base de datos...")
    vales = db.obtener_vales(desde, hasta)
    print(f"  {len(vales)} vales encontrados")

    print("Descargando catálogos de Samsara (esto puede tardar un poco)...")
    vin_por_truckid = samsara.mapa_truckid_vin()
    id_por_truckid = samsara.mapa_truckid_id()
    direcciones = samsara.listar_direcciones()

    filas_csv = []
    sin_vin = 0
    sin_ubicacion = 0

    for i, vale in enumerate(vales, start=1):
        truckid = vale["TRUCKID"]

        # --- Fecha y hora combinadas ---
        fecha = vale["FECHA"].strftime("%Y-%m-%d")   # FECHA viene como datetime
        hora = vale["HORA"]                          # HORA ya viene como texto "HH:MM"
        fecha_hora_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        fecha_hora_iso = f"{fecha}T{hora}:00-05:00"    # hora Central (EE.UU.), no UTC

        fecha_texto = fecha_hora_dt.strftime("%-m/%-d/%Y")
        hora_texto = fecha_hora_dt.strftime("%-H:%M:00")
        fecha_hora_texto = f"{fecha_texto} {fecha_hora_dt.strftime('%-H:%M')}"

        # --- VIN ---
        vin = vin_por_truckid.get(truckid, "")
        if not vin:
            sin_vin += 1

        # --- Dirección (geocerca más cercana en esa fecha/hora) ---
        site_name = ""
        direccion = ""
        vehiculo_id = id_por_truckid.get(truckid)
        if vehiculo_id:
            ubicacion = samsara.ubicacion_en_fecha(vehiculo_id, fecha_hora_iso)
            if ubicacion:
                lat, lon = ubicacion
                geocerca, _distancia = samsara.geocerca_mas_cercana(lat, lon, direcciones)
                if geocerca:
                    site_name = geocerca.get("name", "")
                    direccion = geocerca.get("formattedAddress", "")
                    
                    calle, ciudad, estado, cp = separar_direccion(direccion)
            else:
                sin_ubicacion += 1
        else:
            sin_ubicacion += 1

        # --- Precio total ---
        galones = float(vale["GALONS"])
        tarifa = float(vale["GRATE"])
        precio_total = round(galones * tarifa, 2)

        filas_csv.append({
            "Transaction Number": vale["ID"],
            "Date & Time": fecha_hora_texto,
            "Date": fecha_texto,
            "Time": hora_texto,
            "Fuel Type": "Diesel",
            "Full Address": direccion,
            "Site Name": nombre_marca(site_name),
            "Street Name": calle,
            "City": ciudad,
            "Jurisdiction": estado,
            "Postal Code": cp,
            "Vehicle": truckid,
            "VIN": vin,
            "Quantity": galones,
            "Fuel unit": "Gallons",
            "Gross Price": precio_total,
            "Currency": "USD",
            "Driver Id": "",
            "Merchant Name": vale["COMPANY"],
            "Discount": "",
            "Fuel Grade": "",
        })

        if i % 25 == 0:
            print(f"  Procesados {i}/{len(vales)}...")

    # --- Escribir el CSV ---
    columnas = list(filas_csv[0].keys()) if filas_csv else []
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas_csv)

    print(f"\nListo. Archivo generado: {ruta_salida}")
    print(f"Vales sin VIN encontrado: {sin_vin}")
    print(f"Vales sin ubicación/geocerca encontrada: {sin_ubicacion}")

    return ruta_salida


if __name__ == "__main__":
    generar_reporte("2026-09-24", "2026-09-24")