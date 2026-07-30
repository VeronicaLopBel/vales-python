import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta

from src.services import trucknet, xiga
from src.scheduler import iniciar_scheduler, ultimo_estado 

class APIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        if self.path == '/api/health':
            self._respond_json({'ok': True, 'message': 'backend alive'})
        elif self.path == '/api/status':
            self._respond_json({'ok': True, 'estado': ultimo_estado})
        else:
            self._respond_json({'ok': False, 'message': 'Not found'}, status=404)
            
    def do_POST(self):
        if self.path == '/api/trucknet':
            self._handle_trucknet()
        elif self.path == '/api/xiga':
            self._handle_xiga_full()
        elif self.path == '/api/xiga-prog':
            self._handle_xiga(account=2)
        else:
            self._respond_json({'ok': False, 'message': 'Not found'}, status=404)

    def _read_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        body = self.rfile.read(length).decode('utf-8')
        if not body.strip():
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _respond_json(self, payload, status=200):
        self._set_headers(status)
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def _default_dates(self):
        today = datetime.now()
        return (
            (today - timedelta(days=15)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d'),
        )

    def _handle_trucknet(self):
        body = self._read_json_body()
        fecha_desde, fecha_hasta = self._default_dates()
        fecha_desde = body.get('fromDate', fecha_desde)
        fecha_hasta = body.get('toDate', fecha_hasta)

        try:
            result = trucknet.procesar(fecha_desde, fecha_hasta)
            self._respond_json({'ok': True, **result})
        except Exception as exc:
            self._respond_json({'ok': False, 'message': str(exc)}, status=500)

    def _handle_xiga(self, account: int):
        body = self._read_json_body()
        fecha_desde, fecha_hasta = self._default_dates()
        fecha_desde = body.get('fromDate', fecha_desde)
        fecha_hasta = body.get('toDate', fecha_hasta)

        try:
            if account == 1:
                result = xiga.procesar(
                    usuario=xiga.config.XIGA1_USER,
                    password=xiga.config.XIGA1_PASSWORD,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    vehiculos_excluidos=["0125", "0106", "00157"],
                    remapeo_truckid=xiga.REMAPEO_TRUCKID_CUENTA1,
                )
            else:
                result = xiga.procesar(
                    usuario=xiga.config.XIGA2_USER,
                    password=xiga.config.XIGA2_PASSWORD,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    vehiculos_excluidos=["0012", "0026"],
                    remapeo_truckid=None,
                )
            self._respond_json({'ok': True, **result})
        except Exception as exc:
            self._respond_json({'ok': False, 'message': str(exc)}, status=500)

    def _handle_xiga_full(self):
        body = self._read_json_body()
        fecha_desde, fecha_hasta = self._default_dates()
        fecha_desde = body.get('fromDate', fecha_desde)
        fecha_hasta = body.get('toDate', fecha_hasta)

        try:
            result1 = xiga.procesar(
                usuario=xiga.config.XIGA1_USER,
                password=xiga.config.XIGA1_PASSWORD,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                vehiculos_excluidos=["0125", "0106", "00157"],
                remapeo_truckid=xiga.REMAPEO_TRUCKID_CUENTA1,
            )
            result2 = xiga.procesar(
                usuario=xiga.config.XIGA2_USER,
                password=xiga.config.XIGA2_PASSWORD,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                vehiculos_excluidos=["0012", "0026"],
                remapeo_truckid=None,
            )
            self._respond_json({'ok': True, 'xiga1': result1, 'xiga2': result2})
        except Exception as exc:
            self._respond_json({'ok': False, 'message': str(exc)}, status=500)


def run(server_class=HTTPServer, handler_class=APIHandler, port=8000):
    iniciar_scheduler() 
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving backend API on http://127.0.0.1:{port}')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
