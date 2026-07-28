# Vales - Backend/Frontend Connection

## 1. Arrancar el backend

Desde la carpeta raíz del proyecto:

```bash
cd /home/vero/Documentos/vales-python/backend
source ../venv/bin/activate
python -m src.server
```

El backend quedará escuchando en:

- http://127.0.0.1:8000

Puedes verificar que está vivo con:

```bash
curl http://127.0.0.1:8000/api/health
```

## 2. Arrancar el frontend

En otra terminal, desde la carpeta `frontend`:

```bash
cd /home/vero/Documentos/vales-python/frontend
npm run dev
```

El frontend Vite se abrirá en:

- http://127.0.0.1:5173

## 3. Cómo se conecta

- El frontend ahora usa rutas relativas: `/api/trucknet`, `/api/xiga`, `/api/xiga-prog`.
- Vite proxy redirige `/api` al backend en `http://127.0.0.1:8000`.
- El backend expone CORS con `Access-Control-Allow-Origin: *` para permitir la conexión.

## 4. Notas

- Asegúrate de tener el backend corriendo antes de usar la UI.
- Si la UI muestra `Error: Failed to fetch`, revisa si el backend está activo y si la terminal del backend muestra peticiones.
- Si usas otro puerto backend, ajusta `frontend/vite.config.js` en la sección `proxy.target`.
