#!/usr/bin/env python3
"""
Mini servidor HTTP estándar para storage-report.
Regenera el reporte en cada petición a / o /storage_report.html
y sirve el HTML recién generado. Sin dependencias externas.
"""
import http.server
import pathlib
from urllib.parse import unquote
import sys

# Añadir el directorio del paquete al path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from storage_report.generator import generate_html

REPORT_PATH = pathlib.Path("/tmp/storage_report.html")
BASE_DIR = pathlib.Path("/tmp")
PORT = 8888

def regenerate_report():
    try:
        html = generate_html()
        REPORT_PATH.write_text(html)
    except Exception:
        # Si falla, seguimos sirviendo lo que haya
        pass

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciar logs para no saturar journal
        return

    def do_GET(self):
        url_path = unquote(self.path.split('?',1)[0])
        # Normalizar
        if url_path in ('/', '/index.html', '/storage_report.html'):
            regenerate_report()
            if REPORT_PATH.is_file():
                try:
                    data = REPORT_PATH.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception:
                    pass
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error generating report")
            return

        # Servir archivos estáticos desde /tmp para rutas relativas
        rel_path = url_path.lstrip('/')
        file_path = (BASE_DIR / rel_path).resolve()
        # Seguridad: no salir de BASE_DIR
        try:
            if str(file_path).startswith(str(BASE_DIR.resolve())) and file_path.is_file():
                data = file_path.read_bytes()
                self.send_response(200)
                # Tipo simple
                if file_path.suffix == '.html':
                    ctype = 'text/html; charset=utf-8'
                elif file_path.suffix in ('.css',):
                    ctype = 'text/css'
                elif file_path.suffix in ('.js',):
                    ctype = 'application/javascript'
                else:
                    ctype = 'application/octet-stream'
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        except Exception:
            pass
        self.send_response(404)
        self.end_headers()

def run():
    server_address = ('', PORT)
    httpd = http.server.HTTPServer(server_address, Handler)
    httpd.serve_forever()

if __name__ == "__main__":
    run()
