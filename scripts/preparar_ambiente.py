"""Cria o ambiente local e instala as dependências sem substituir o .env."""
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 10):
        raise SystemExit('Use Python 3.10 ou superior; o ambiente validado está documentado no guia.')
    environment = ROOT / '.venv'
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        venv.EnvBuilder(with_pip=True).create(environment)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')],
                   cwd=ROOT, check=True)
    if not (ROOT / '.env').exists():
        shutil.copyfile(ROOT / '.env.example', ROOT / '.env')
    print('Ambiente preparado. O arquivo .env existente foi preservado.')
    print('Inicie API e dashboard com o Python da .venv e run.py.')


if __name__ == '__main__':
    main()
