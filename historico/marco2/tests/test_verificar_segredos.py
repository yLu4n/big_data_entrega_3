import importlib.util,json,uuid,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('secret_scan',ROOT/'scripts/verificar_segredos.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class SecurityScanTests(unittest.TestCase):
    def setUp(self):
        self.root=(ROOT/'work/testes'/uuid.uuid4().hex).resolve()
        self.root.mkdir(parents=True,exist_ok=True)
    def tearDown(self):
        assert self.root.is_relative_to((ROOT/'work/testes').resolve())
        for p in sorted(self.root.rglob('*'),key=lambda p:len(p.parts),reverse=True):
            if p.is_file():p.unlink()
            else:p.rmdir()
        self.root.rmdir()
    def write(self,name,content):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')
    def test_detects_token_without_printing_value(self):
        fake='AVNS_'+'X'*24
        self.write('config.txt',fake)
        result=module.scan(self.root)
        self.assertEqual(result['resultado'],'REVISAR')
        self.assertNotIn(fake,json.dumps(result))
    def test_blocks_state_in_publishable_path(self):
        self.write('infra/aiven.tfstate','{}')
        self.assertEqual(module.scan(self.root)['resultado'],'REVISAR')
    def test_ignores_private_runtime_directory(self):
        self.write('work/terraform-state/aiven.tfstate','{}')
        self.assertEqual(module.scan(self.root)['resultado'],'OK')
    def test_allows_lock_and_public_connection(self):
        self.write('infra/.terraform.lock.hcl','# provider checksums')
        self.write('config.json',json.dumps(dict(host='example.aivencloud.com',sslmode='require')))
        self.assertEqual(module.scan(self.root)['resultado'],'OK')
    def test_rejects_literal_credential_field(self):
        field='pass'+'word'
        self.write('config.json',json.dumps({field:'fixture-value-for-unit-test'}))
        self.assertEqual(module.scan(self.root)['resultado'],'REVISAR')
    def test_rejects_secret_file_even_without_token_pattern(self):
        self.write('.env','QUALQUER=valor')
        self.assertEqual(module.scan(self.root)['resultado'],'REVISAR')

if __name__=='__main__':unittest.main()
