"""Cliente HTTP do dashboard. O acesso à base pertence exclusivamente à API."""
import os
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env', override=False)


def load_data():
    base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
    if urlparse(base_url).scheme not in {'http', 'https'}:
        raise ValueError('API_BASE_URL deve usar http ou https.')
    timeout = float(os.getenv('API_TIMEOUT_SECONDS', '15'))
    response = requests.get(base_url + '/api/v1/observacoes', timeout=(3, timeout),
                            headers={'Accept': 'application/json'}, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200:
        raise ValueError('A API deve responder com HTTP 200, sem redirecionamento.')
    payload = response.json()
    from dataset import COLUMNS, normalize
    if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
        raise ValueError('Resposta da API fora do contrato.')
    metadata = payload.get('meta', {})
    if metadata.get('total') != len(payload['data']):
        raise ValueError('A API devolveu uma quantidade de registros inconsistente.')
    frame = pd.DataFrame(payload['data']) if payload['data'] else pd.DataFrame(columns=COLUMNS)
    frame = normalize(frame)
    if len(frame) != metadata['total']:
        raise ValueError('A API devolveu registros fora do universo Bahia / ocupados.')
    return frame, 'API própria • consulta HTTP em tempo real'
