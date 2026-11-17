"""Reproduz os resultados descritivos do README a partir do pacote original."""
import hashlib
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics import SECTORS, filtered, income, metrics, ratio, weight
from dataset import ARCHIVE, normalize


def build_report():
    with ZipFile(ARCHIVE) as archive:
        raw = archive.read('entrega_fase2_bahia/dados/pnadc_ocupados_2026.csv')
    frame = normalize(pd.read_csv(io.BytesIO(raw)))
    result = {'fonte': str(ARCHIVE.relative_to(ROOT)),
              'csv_sha256': hashlib.sha256(raw).hexdigest(),
              'metodo': 'Estimativas pontuais ponderadas por V1028; renda nominal VD4016; um trimestre por vez.',
              'recortes': []}
    for quarter in [1, 2]:
        for geography in ['bahia', 'salvador', 'interior']:
            selected = filtered(frame.loc[frame.trimestre.eq(quarter)], geography)
            entrepreneurs = selected.loc[selected.vd4009.isin([8, 9])]
            women = entrepreneurs.loc[entrepreneurs.v2007.eq(2)]
            men = entrepreneurs.loc[entrepreneurs.v2007.eq(1)]
            groups = {}
            for label, sex, races in [('mulheres_negras', 2, [2, 4]),
                                      ('mulheres_brancas', 2, [1]),
                                      ('homens_negros', 1, [2, 4]),
                                      ('homens_brancos', 1, [1])]:
                group = entrepreneurs.loc[entrepreneurs.v2007.eq(sex) & entrepreneurs.v2010.isin(races)]
                known = group.loc[group.v4019.isin([1, 2])]
                groups[label] = {'renda_media': income(group), 'n': len(group),
                                 'n_renda': int(group.vd4016.notna().sum()),
                                 'formalizacao_pct': ratio(weight(known.loc[known.v4019.eq(1)]), weight(known)),
                                 'n_cnpj': len(known)}
            sectors = [{'setor': SECTORS.get(code, str(code)),
                        'participacao_pct': ratio(weight(group), weight(women))}
                       for code, group in women.groupby('vd4010')]
            result['recortes'].append({'ano': 2026, 'trimestre': quarter, 'territorio': geography,
                                       'n_ocupados': len(selected), 'indicadores': metrics(selected),
                                       'renda_media_homens': income(men), 'grupos': groups,
                                       'setores_empreendedoras': sorted(sectors, key=lambda row: row['participacao_pct'], reverse=True)})
    return result


if __name__ == '__main__':
    destination = ROOT / 'docs' / 'resultados_pnad.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(build_report(), ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('Resultados gravados em docs/resultados_pnad.json')
