"""Teste integrado de implantação local em portas temporárias, via HTTP real."""
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def verify():
    api_port, dashboard_port = free_port(), free_port()
    while api_port == dashboard_port:
        dashboard_port = free_port()
    environment = os.environ.copy()
    environment.update(API_PORT=str(api_port), PORT=str(dashboard_port))
    process = subprocess.Popen([sys.executable, str(ROOT / 'run.py')], cwd=ROOT,
                               env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base_api = f'http://127.0.0.1:{api_port}'
    base_dashboard = f'http://127.0.0.1:{dashboard_port}'
    checks = []
    try:
        deadline = time.monotonic() + 30
        while True:
            if process.poll() is not None:
                raise RuntimeError('O iniciador encerrou antes de disponibilizar os serviços.')
            try:
                health = requests.get(base_api + '/health', timeout=1)
                dashboard = requests.get(base_dashboard + '/', timeout=1)
                if health.status_code == dashboard.status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError('Os serviços não ficaram disponíveis em 30 segundos.')
            time.sleep(0.2)
        checks.extend(['API /health: HTTP 200', 'Dashboard /: HTTP 200'])
        response = requests.get(base_api + '/api/v1/observacoes', timeout=20)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload.get('data'), list) or payload['meta']['total'] != len(payload['data']):
            raise RuntimeError('Snapshot da API inconsistente.')
        checks.append('Snapshot da API: quantidade consistente')
        contract = requests.get(base_api + '/openapi.json', timeout=5)
        contract.raise_for_status()
        if contract.json().get('openapi') != '3.1.0':
            raise RuntimeError('Contrato OpenAPI indisponível.')
        checks.append('Contrato OpenAPI: HTTP 200')

        from app import app
        key, meta = next((key, meta) for key, meta in app.callback_map.items()
                         if 'indicadores.children' in key)
        values = [0, 0, None, 'bahia', [], [], [14, 130], []]
        body = {'output': key,
                'outputs': [{'id': item.component_id, 'property': item.component_property}
                            for item in meta['output']],
                'inputs': [dict(spec, value=value) for spec, value in zip(meta['inputs'], values)],
                'state': [], 'changedPropIds': ['clock.n_intervals']}
        rendered = requests.post(base_dashboard + '/_dash-update-component', json=body, timeout=30)
        rendered.raise_for_status()
        output = rendered.json()['response']
        if len(output['indicadores']['children']) != 6 or 'HTTP' not in output['connection']['children']:
            raise RuntimeError('Dashboard não recebeu os seis indicadores pela API.')
        checks.append('Dashboard → API: seis indicadores recebidos por HTTP')
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    checks.append('Processo de teste encerrado; instâncias do usuário preservadas')
    git = subprocess.run(['git', '-c', f'safe.directory={ROOT}', 'rev-parse', '--show-toplevel'], cwd=ROOT,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return {'validado_em_utc': datetime.now(timezone.utc).isoformat(),
            'python': sys.version.split()[0], 'resultado': 'aprovado_localmente',
            'observacoes_fonte': payload['meta']['total'], 'verificacoes': checks,
            'repositorio_git_detectado': git.returncode == 0}


if __name__ == '__main__':
    try:
        result = verify()
    except Exception as error:
        print(f'Validação de implantação falhou ({type(error).__name__}). Verifique a fonte, dependências e portas locais.')
        raise SystemExit(1)
    destination = ROOT / 'docs' / 'validacao_implantacao.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Implantação local validada. Evidência: docs/validacao_implantacao.json')
