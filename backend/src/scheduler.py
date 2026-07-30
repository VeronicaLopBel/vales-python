import time
import threading
from datetime import datetime, timedelta
from src.services import trucknet, xiga

# estado compartido que el front va a poder consultar via /api/status
ultimo_estado = {
    "trucknet": None,
    "xiga": None,
    "xiga-prog": None,
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def ejecutar_ciclo():
    global ultimo_estado
    hoy = datetime.now()
    fecha_desde = (hoy - timedelta(days=15)).strftime('%Y-%m-%d')
    fecha_hasta = hoy.strftime('%Y-%m-%d')

    # log("Ejecutando TruckNet...")
    # resultado_trucknet = trucknet.procesar(fecha_desde, fecha_hasta)
    # ultimo_estado["trucknet"] = resultado_trucknet
    # time.sleep(60)

    log("Ejecutando XIGA cuenta 1...")
    resultado1 = xiga.procesar(
        usuario=xiga.config.XIGA1_USER,
        password=xiga.config.XIGA1_PASSWORD,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0125", "0106", "00157"],
        remapeo_truckid=xiga.REMAPEO_TRUCKID_CUENTA1,
        origen="automatico"
    )
    ultimo_estado["xiga"] = resultado1

    time.sleep(60)

    log("Ejecutando XIGA cuenta 2...")
    resultado2 = xiga.procesar(
        usuario=xiga.config.XIGA2_USER,
        password=xiga.config.XIGA2_PASSWORD,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0012", "0026"],
        remapeo_truckid=None,
        origen="automatico"
    )
    ultimo_estado["xiga-prog"] = resultado2

def loop_cada_hora():
    while True:
        try:
            ejecutar_ciclo()
        except Exception as e:
            log(f"Error en ciclo: {e}")
        log("Ciclo completado")
        ahora = datetime.now()
        siguiente_hora = (ahora.replace(minute=0, second=0, microsecond=0) 
                          + timedelta(hours=1))
        espera = (siguiente_hora - ahora).total_seconds()
        log(f"Próxima ejecución a las {siguiente_hora.strftime('%H:%M:%S')}")
        time.sleep(espera)

def iniciar_scheduler():
    log("Iniciando hilo del scheduler...")
    hilo = threading.Thread(target=loop_cada_hora, daemon=True)
    hilo.start()