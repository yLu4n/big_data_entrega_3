"""Inspeção estática para arquivos publicáveis. Relata local, nunca o valor encontrado."""
import argparse,json,re
from pathlib import Path

IGNORED={'.git','.venv','venv','__pycache__','.terraform','work'}
PATTERNS={
    'token Aiven':re.compile(r'\bAVNS_[A-Za-z0-9_-]{12,}\b'),
    'token GitHub':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
    'chave AWS':re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'chave privada':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'URI com senha':re.compile(r'postgres(?:ql)?://[^\s:/@]+:[^\s/@]+@'),
    'senha/token literal':re.compile(r'''(?ix)\b(?:password|passwd|api_token|access_token)\b["']?\s*[:=]\s*["']([^"'\r\n]+)["']''')
}
TEXT_SUFFIXES={'.py','.ps1','.tf','.hcl','.json','.md','.sql','.txt','.yaml','.yml','.tfvars','.example','.csv'}

def scan(root):
    found=[];checked=0
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(root)
        if any(part in IGNORED for part in rel.parts):continue
        name=path.name.lower()
        forbidden=(name in {'.env','terraform.tfvars','.pgpass','pgpass.conf','plan.json'}
                   or name.startswith('.env.') and name!='.env.example'
                   or '.tfstate' in name or name.endswith(('.tfplan','.key','.pem','.auto.tfvars','.log'))
                   or 'segredos' in rel.parts)
        if forbidden:found.append(dict(arquivo=rel.as_posix(),tipo='arquivo privado no conjunto publicável'));continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {'.gitignore','.gitattributes'}:continue
        try:text=path.read_text(encoding='utf-8-sig')
        except UnicodeError:continue
        checked+=1
        for lineno,line in enumerate(text.splitlines(),1):
            for kind,pattern in PATTERNS.items():
                match=pattern.search(line)
                if not match:continue
                if kind=='senha/token literal':
                    value=match.group(1)
                    if value.startswith(('PREENCHA','EXEMPLO','<','${')):continue
                    # O próprio código contém expressões regulares e exemplos de validação.
                    if path.resolve()==Path(__file__).resolve():continue
                found.append(dict(arquivo=rel.as_posix(),linha=lineno,tipo=kind))
    return dict(arquivos_texto_inspecionados=checked,ocorrencias=found,resultado='OK' if not found else 'REVISAR',limite='Inspeção estática de texto; não audita binários nem histórico remoto.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--saida',type=Path);args=p.parse_args();result=scan(args.raiz)
    if args.saida:args.saida.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['resultado']=='OK' else 1)
