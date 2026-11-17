"""Adaptador de arquivos da API: relê a fonte em cada requisição."""
import hashlib
import io
import os
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env', override=False)
ARCHIVE = ROOT / 'Dados_tratados' / 'Entrega_Tecnica_Fase_2_Bahia.zip'
COLUMNS = ['ano', 'trimestre', 'uf', 'capital', 'v1028', 'v2007', 'v2009',
           'v2010', 'vd3004', 'vd4002', 'vd4009', 'v4019', 'vd4010', 'vd4016']
NULLABLE = {'capital', 'v4019', 'vd4016'}


def normalize(frame):
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError('Colunas obrigatórias ausentes na fonte.')
    frame = frame[COLUMNS].copy()
    for column in COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors='raise')
    if not frame.empty:
        if not np.isfinite(frame.drop(columns=list(NULLABLE)).to_numpy(dtype=float)).all():
            raise ValueError('Valores obrigatórios ausentes ou não finitos.')
        if np.isinf(frame.to_numpy(dtype=float)).any():
            raise ValueError('Valores infinitos na fonte.')
        if (frame['v1028'] <= 0).any():
            raise ValueError('Os pesos devem ser positivos.')
        if not frame.trimestre.isin([1, 2, 3, 4]).all():
            raise ValueError('Trimestre inválido.')
        if ((frame.vd4016 < 0) & frame.vd4016.notna()).any():
            raise ValueError('Rendimento negativo inválido.')
        for column in set(COLUMNS) - {'v1028', 'vd4016'}:
            valid = frame[column].dropna()
            if not valid.eq(valid.round()).all():
                raise ValueError('Códigos e contagens devem ser inteiros.')
    frame = frame.loc[frame.uf.eq(29) & frame.vd4002.eq(1)].copy()
    frame['periodo'] = frame.ano.astype(int).astype(str) + ' · T' + frame.trimestre.astype(int).astype(str)
    return frame


def read_snapshot():
    configured = os.getenv('DATA_FILE', '').strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = ROOT / path
        raw = path.read_bytes()
    else:
        with ZipFile(ARCHIVE) as archive:
            raw = archive.read('entrega_fase2_bahia/dados/pnadc_ocupados_2026.csv')
    frame = normalize(pd.read_csv(io.BytesIO(raw), usecols=COLUMNS))
    meta = {'total': len(frame), 'consultado_em': datetime.now(timezone.utc).isoformat(),
            'versao': hashlib.sha256(raw).hexdigest(),
            'fonte': 'PNAD Contínua / IBGE · ocupados da Bahia'}
    return frame, meta
