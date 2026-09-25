import time
import threading
from datetime import datetime, timedelta
from src.config import config
from src.services import trucknet, xiga

# estado compartido que el front va a poder consultar via /api/status
ultimo_estado = {
    "trucknet": None,
    "xiga": None,
    "xiga-prog": None,
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def correr_paso(clave, nombre, funcion, **kwargs):
    """Ejecuta un paso aislado: si falla, lo registra y el ciclo continúa."""
    log(f"Ejecutando {nombre}...")
    try:
        resultado = funcion(**kwargs)
        # Añadir marca de tiempo de cuándo se completó este paso
        if isinstance(resultado, dict):
            resultado["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ultimo_estado[clave] = resultado
    except Exception as e:
        log(f"Error en {nombre}: {e}")
        ultimo_estado[clave] = {"error": str(e), "origen": "automatico", "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


def ejecutar_ciclo():
    hoy = datetime.now()
    fecha_desde = (hoy - timedelta(days=15)).strftime('%Y-%m-%d')
    fecha_hasta = hoy.strftime('%Y-%m-%d')

    correr_paso("trucknet", "TruckNet", trucknet.procesar,
                origen="automatico", dry_run=False)
    time.sleep(60)

    correr_paso(
        "xiga", "XIGA cuenta 1", xiga.procesar,
        usuario=config.XIGA1_USER,
        password=config.XIGA1_PASSWORD,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0125", "0106", "00157"],
        remapeo_truckid=xiga.REMAPEO_TRUCKID_CUENTA1,
        origen="automatico",
    )

    time.sleep(60)

    correr_paso(
        "xiga-prog", "XIGA cuenta 2", xiga.procesar,
        usuario=config.XIGA2_USER,
        password=config.XIGA2_PASSWORD,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        vehiculos_excluidos=["0012", "0026"],
        remapeo_truckid=None,
        origen="automatico",
    )


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
    
    
if __name__ == "__main__":
    log("Prueba manual: un solo ciclo")
    ejecutar_ciclo()
    log(f"Estado final: {ultimo_estado}")