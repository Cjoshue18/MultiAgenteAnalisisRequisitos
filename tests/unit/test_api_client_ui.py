"""Verifica contrato del cliente visual sin Streamlit ni llamadas de red externas."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import json
import pytest
from src.services.api_client import ClienteAPI, ErrorAPI


class ServidorPrueba(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/analisis/ANA-1/exportar'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return
        self._responder({"status": "ok", "ruta": self.path})

    def do_POST(self):
        n = int(self.headers.get('Content-Length', '0'))
        self.server.peticion = self.rfile.read(n)
        self.server.tipo = self.headers.get('Content-Type')
        if self.path == '/api/analisis/ANA-1/aprobar':
            self._responder({"detail": "Ya está aprobado"}, 409)
            return
        self._responder({"ok": True}, 201)

    def _responder(self, payload, estado=200):
        contenido = json.dumps(payload).encode()
        self.send_response(estado)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def log_message(self, *args):
        pass


@contextmanager
def servidor_local():
    servidor = ThreadingHTTPServer(('127.0.0.1', 0), ServidorPrueba)
    hilo = Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield servidor, ClienteAPI(f'http://127.0.0.1:{servidor.server_port}')
    finally:
        servidor.shutdown()
        hilo.join(timeout=3)
        servidor.server_close()


def test_estado_y_consulta_con_filtro():
    with servidor_local() as (_, api):
        assert api.estado()['status'] == 'ok'
        assert 'proyecto_id=PRY-1' in api.analisis('PRY-1')['ruta']


def test_crear_y_analizar_en_utf8():
    with servidor_local() as (servidor, api):
        assert api.crear_proyecto('Biblioteca')['ok']
        assert api.iniciar_texto('PRY-1', 'CUS', 'préstamos y devolución')['ok']
        assert json.loads(servidor.peticion)['modalidad_modelado'] == 'CUS'


def test_carga_multipart_y_formato():
    with servidor_local() as (servidor, api):
        assert api.iniciar_archivo('PRY-1', 'HU', 'req.txt', b'necesito libros')['ok']
        assert 'multipart/form-data' in servidor.tipo
        assert b'name="archivo"' in servidor.peticion
        assert b'necesito libros' in servidor.peticion
        with pytest.raises(ErrorAPI, match='Solo se admiten'):
            api.iniciar_archivo('PRY-1', 'HU', 'ejecutable.exe', b'no')
        with pytest.raises(ErrorAPI, match='10 MB'):
            api.iniciar_archivo('PRY-1', 'HU', 'muy_grande.txt', b'x' * (10 * 1024 * 1024 + 1))


def test_error_http_muestra_detalle():
    with servidor_local() as (_, api):
        with pytest.raises(ErrorAPI, match='409: Ya está aprobado'):
            api.revisar('ANA-1', {'accion': 'aprobar'})


def test_descarga_y_formato_invalido():
    with servidor_local() as (_, api):
        assert api.exportar('ANA-1', 'json') == b'{"ok": true}'
        with pytest.raises(ValueError, match='Formato'):
            api.exportar('ANA-1', 'exe')
