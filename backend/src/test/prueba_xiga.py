from src.services import xiga
from src.config import config
import json

token = xiga.login(config.XIGA1_USER, config.XIGA1_PASSWORD)
print("Token obtenido:", token[:20], "...")  # solo mostramos un pedazo por seguridad visual

consumos = xiga.descargar_consumos(token, "2026-01-15", "2026-01-30")
print("Cantidad de consumos:", len(consumos))
if consumos:
    print("Primer registro de ejemplo:")
    print(json.dumps(consumos[0], indent=2))