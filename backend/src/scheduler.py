import time
import threading
from datetime import datetime, timedelta
from src.services import trucknet, xiga

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def ejecutar_ciclo():
    hoy = datetime.now()
    fecha_desde = (hoy - timedelta(days=15)).strftime('%Y-%m-%d')
    fecha_hasta = hoy.strftime('%Y-%m-%d')

    print("[scheduler] Ejecutando TruckNet...")
    trucknet.procesar(fecha_desde, fecha_hasta)

    time.sleep(60)

    print("[scheduler] Ejecutando XIGA cuenta 1...")
    xiga.procesar(
        usuario=xiga.config.XIGA1_USER,
        password=xiga.config.XIGA1_PASSWORD,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0125", "0106", "00157"],
        remapeo_truckid=xiga.REMAPEO_TRUCKID_CUENTA1,
    )

    time.sleep(60)

    print("[scheduler] Ejecutando XIGA cuenta 2...")
    xiga.procesar(
        usuario=xiga.config.XIGA2_USER,
        password=xiga.config.XIGA2_PASSWORD,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0012", "0026"],
        remapeo_truckid=None,
    )

def loop_cada_hora():
    while True:
        try:
            ejecutar_ciclo()
        except Exception as e:
            print(f"[scheduler] Error en ciclo: {e}")
        time.sleep(3600)

def iniciar_scheduler():
    hilo = threading.Thread(target=loop_cada_hora, daemon=True)
    hilo.start()