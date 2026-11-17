"""Inicia a API e o dashboard juntos: python run.py."""
import os
import socket
from threading import Thread

from werkzeug.serving import make_server

from api import api


def main():
    port = int(os.getenv('API_PORT', '8000'))
    dashboard_port = int(os.getenv('PORT', '8050'))
    if port == dashboard_port:
        raise SystemExit('API_PORT e PORT precisam ser diferentes.')
    for candidate in [port, dashboard_port]:
        with socket.socket() as probe:
            probe.settimeout(0.5)
            if probe.connect_ex(('127.0.0.1', candidate)) == 0:
                raise SystemExit(f'A porta {candidate} já está em uso. Encerre a instância antiga com Ctrl+C ou altere a porta no .env.')
    os.environ['API_BASE_URL'] = f'http://127.0.0.1:{port}'
    service = make_server('127.0.0.1', port, api, threaded=True)
    thread = Thread(target=service.serve_forever, daemon=True)
    thread.start()
    try:
        from app import app
        print(f'API: http://127.0.0.1:{port}/api/v1/observacoes')
        app.run(host='127.0.0.1', port=dashboard_port, debug=False)
    finally:
        service.shutdown()
        service.server_close()
        thread.join(timeout=5)


if __name__ == '__main__':
    main()
