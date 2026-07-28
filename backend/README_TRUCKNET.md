# Pruebas y configuración de TruckNet (UAT)

Pasos rápidos para configurar y probar el login de TruckNet en el entorno UAT.

1. Copia el ejemplo de variables de entorno al archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

2. Edita `.env` y reemplaza `TRUCKNET_TENANT`, `TRUCKNET_USER` y `TRUCKNET_PASSWORD`.

Ejemplo mínimo:

```
TRUCKNET_TENANT=mi-tenant
TRUCKNET_ENV=UAT
TRUCKNET_USER=jsmith
TRUCKNET_PASSWORD=s3cr3t
```

3. Comprobar con `curl` (UAT):

```bash
curl -i -X POST "https://webuat.triniumtech.com/fpas/MI-TENANT/web/api/login" -u "jsmith:s3cr3t"
```

Respuesta esperada: `200` y un JSON con `token` y `expiresAt`.

4. Probar desde el backend (venv activo):

```bash
cd backend
source ../venv/bin/activate
python -m src.services.trucknet
```

Notas de depuración:
- Si ves HTML con "WebSpeed error", el `TENANT` o la URL están mal (servicio no existe).
- Si el login devuelve 405, asegúrate de usar `POST`.
- Si tu entorno requiere proxy, configura variables `HTTP_PROXY`/`HTTPS_PROXY`.
