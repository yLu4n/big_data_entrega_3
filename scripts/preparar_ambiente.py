"""Cria o ambiente local e instala as dependências sem substituir o .env."""
import argparse
import os
import shutil
import subprocess
import sys
import venv
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recriar', action='store_true',
                        help='Preserva a .venv antiga em tmp/ambientes e cria um ambiente limpo.')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        raise SystemExit('Use Python 3.10 ou superior; o ambiente validado está documentado no guia.')
    environment = ROOT / '.venv'
    if args.recriar and environment.exists():
        resolved = environment.resolve()
        backup = (ROOT / 'tmp' / 'ambientes' /
                  ('venv-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:8])).resolve()
        if resolved.parent != ROOT or not backup.is_relative_to(ROOT / 'tmp' / 'ambientes'):
            raise SystemExit('Caminho do ambiente ou backup fora da pasta esperada.')
        if Path(sys.prefix).resolve() == resolved:
            raise SystemExit('Use o Python externo à .venv: python scripts/preparar_ambiente.py --recriar')
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(resolved), str(backup))
        print(f'Ambiente anterior preservado em {backup.relative_to(ROOT)}', flush=True)
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        venv.EnvBuilder(with_pip=True).create(environment)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')],
                   cwd=ROOT, check=True)
    # pip pode considerar um pacote instalado mesmo que seus binários pertençam
    # a outra versão do Python. Importar confirma o carregamento das extensões.
    verification = subprocess.run(
        [str(python), '-c', 'import numpy, pandas, dash, plotly, flask, requests'],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if verification.returncode != 0:
        raise SystemExit('As dependências não carregaram corretamente. Use o Python externo e execute: '
                         'python scripts/preparar_ambiente.py --recriar')
    if not (ROOT / '.env').exists():
        shutil.copyfile(ROOT / '.env.example', ROOT / '.env')
    print('Ambiente preparado. O arquivo .env existente foi preservado.')
    print('Importação de NumPy, Pandas, Dash, Plotly, Flask e Requests validada.')
    print('Inicie API e dashboard com o Python da .venv e run.py.')


if __name__ == '__main__':
    main()
