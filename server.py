"""Servidor local do protótipo. Execute: python server.py."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from filas import analyze, inspect_data

ROOT = Path(__file__).resolve().parent
PORT = 7002
FILES = {
    '/': ('static/index.html', 'text/html; charset=utf-8'),
    '/app.js': ('static/app.js', 'text/javascript; charset=utf-8'),
    '/replay.js': ('static/replay.js', 'text/javascript; charset=utf-8'),
    '/replay.css': ('static/replay.css', 'text/css; charset=utf-8'),
    '/style.css': ('static/style.css', 'text/css; charset=utf-8'),
    '/dados/mercado_pico_FICTICIO.csv': ('dados/mercado_pico_FICTICIO.csv', 'text/csv; charset=utf-8'),
    '/dados/Angelone_pico_FICTICIO.csv': ('dados/Angelone_pico_FICTICIO.csv', 'text/csv; charset=utf-8'),
    '/dados/Angeloni_pico.csv': ('dados/Angeloni_pico.csv', 'text/csv; charset=utf-8'),
    '/dados/modelo_coleta.csv': ('dados/modelo_coleta.csv', 'text/csv; charset=utf-8'),
    '/dados/modelo_coleta_por_tipo.csv': ('dados/modelo_coleta_por_tipo.csv', 'text/csv; charset=utf-8'),
    '/dados/Angeloni_pico_por_tipo.csv': ('dados/Angeloni_pico_por_tipo.csv', 'text/csv; charset=utf-8'),
    '/guia-coleta': ('GUIA_COLETA.md', 'text/plain; charset=utf-8'),
}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def json(self, status, obj):
        self.reply(status, json.dumps(obj, ensure_ascii=False, allow_nan=False).encode('utf-8'))

    def do_GET(self):
        path = urlsplit(self.path).path
        if path not in FILES:
            return self.json(404, {'error': 'Recurso não encontrado.'})
        filename, content_type = FILES[path]
        try:
            self.reply(200, (ROOT / filename).read_bytes(), content_type)
        except FileNotFoundError:
            self.json(404, {'error': 'Arquivo indisponível.'})

    def do_POST(self):
        if self.path not in ('/api/analisar', '/api/inspecionar'):
            return self.json(404, {'error': 'Rota não encontrada.'})
        if self.headers.get('Host') not in (f'127.0.0.1:{PORT}', f'localhost:{PORT}'):
            return self.json(403, {'error': 'Use o endereço local da aplicação.'})
        origin = self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}'):
            return self.json(403, {'error': 'Origem não permitida.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2_000_000:
                return self.json(413, {'error': 'Envie até 2 MB por requisição.'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.json(415, {'error': 'Envie os dados em JSON.'})
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            self.json(200, inspect_data(payload) if self.path == '/api/inspecionar' else analyze(payload))
        except (ValueError, UnicodeError) as exc:
            self.json(400, {'error': str(exc)})
        except Exception:
            self.log_error('Falha interna no cálculo')
            self.json(500, {'error': 'Falha interna. Confira o terminal do servidor.'})


if __name__ == '__main__':
    print(f'Mercado em fluxo: http://127.0.0.1:{PORT}', flush=True)
    print('Servidor local. Ctrl+C encerra. Dados recebidos não são gravados no servidor.', flush=True)
    try:
        ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nServidor encerrado.')
