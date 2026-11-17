import os
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch

import pandas as pd

from analytics import filtered, income, metrics
import requests
from werkzeug.serving import make_server

from data_source import load_data
from dataset import COLUMNS, normalize


class WeightedIndicators(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame([
            [2, 2, 9, 2, 1, 1000], [1, 2, 8, 1, 2, 3000],
            [1, 1, 9, 1, 1, 4000], [6, 2, 2, 4, None, 500],
            [1, 2, 9, 4, None, None],
        ], columns=['v1028', 'v2007', 'vd4009', 'v2010', 'v4019', 'vd4016'])

    def test_weighted_denominators_and_missing(self):
        result = metrics(self.frame)
        self.assertEqual(result['women_total'], 4)
        self.assertEqual(result['women_share'], 80)
        self.assertEqual(result['black_share'], 75)
        self.assertAlmostEqual(result['formal_rate'], 200 / 3)
        self.assertAlmostEqual(result['women_income'], 5000 / 3)
        self.assertAlmostEqual(result['income_gap'], 100 * (1 - (5000 / 3) / 4000))
        self.assertEqual(result['income_n'], 2)

    def test_zero_income_is_valid(self):
        self.assertEqual(income(pd.DataFrame({'v1028': [1, 1], 'vd4016': [0, 100]})), 50)

    def test_no_comparator_or_no_sample(self):
        self.assertIsNone(metrics(self.frame.loc[self.frame.v2007.eq(2)])['income_gap'])
        self.assertIsNone(metrics(self.frame.iloc[:0])['women_share'])

    def test_null_capital_belongs_to_rest_of_state(self):
        geo = pd.DataFrame({'capital': [29, None, None], 'v2009': [25, 35, 60]})
        self.assertEqual(len(filtered(geo, geography='interior')), 2)
        self.assertEqual(len(filtered(geo, geography='salvador')), 1)

    def test_invalid_weights_are_rejected(self):
        sample = pd.DataFrame([{c: 1 for c in COLUMNS}])
        sample['v1028'] = -1
        with self.assertRaises(ValueError):
            normalize(sample)


class AppIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from api import create_app
        cls.service = make_server('127.0.0.1', 0, create_app(), threaded=True)
        cls.base_url = f'http://127.0.0.1:{cls.service.server_port}'
        cls.environment = patch.dict(os.environ, {'API_BASE_URL': cls.base_url, 'DATA_FILE': ''})
        cls.environment.start()
        cls.thread = Thread(target=cls.service.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.service.shutdown()
        cls.service.server_close()
        cls.thread.join(timeout=5)
        cls.environment.stop()

    def test_real_archive_and_geographic_partition(self):
        frame, source = load_data()
        self.assertIn('API própria', source)
        self.assertEqual(len(frame), 20706)
        self.assertEqual(frame.groupby('trimestre').size().to_dict(), {1: 10062, 2: 10644})
        self.assertEqual(len(filtered(frame, 'salvador')), 3382)
        self.assertEqual(len(filtered(frame, 'salvador')) + len(filtered(frame, 'interior')), len(frame))

    def test_layout_callbacks_filters_and_download(self):
        from app import app, render_dashboard, export_table
        with patch.dict(os.environ, {'API_BASE_URL': self.base_url}):
            client = app.server.test_client()
            for url in ['/', '/_dash-layout', '/_dash-dependencies', '/assets/style.css']:
                with client.get(url) as response:
                    self.assertEqual(response.status_code, 200)
            rendered = render_dashboard(0, 0, None, 'bahia', [], [], [14, 130], [])
            self.assertEqual(len(rendered[0]), 6)
            self.assertEqual(rendered[-1], '2026 · T2')
            self.assertIn('10.644', rendered[7])
            empty = render_dashboard(0, 0, None, 'bahia', [5], [], [129, 130], [])
            self.assertEqual(empty[5], [])
            download, message = export_table(1, rendered[-1], 'salvador', [2, 4], [], [14, 130], [])
            self.assertIn('Trimestre', download['content'])
            self.assertIn('2026 · T2', download['content'])
            self.assertIn('exportada', message)

    def test_browser_callback_protocol(self):
        from app import app
        key, meta = next((key, meta) for key, meta in app.callback_map.items() if 'indicadores.children' in key)
        values = [0, 0, None, 'salvador', [2, 4], [], [14, 130], []]
        inputs = [dict(spec, value=value) for spec, value in zip(meta['inputs'], values)]
        outputs = [{'id': item.component_id, 'property': item.component_property} for item in meta['output']]
        with patch.dict(os.environ, {'API_BASE_URL': self.base_url}):
            response = app.server.test_client().post('/_dash-update-component', json={
                'output': key, 'outputs': outputs, 'inputs': inputs, 'state': [],
                'changedPropIds': ['geography.value'],
            })
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()['response']
        self.assertEqual(len(payload['indicadores']['children']), 6)
        self.assertIn('API própria', payload['connection']['children'])
        self.assertEqual(payload['period']['value'], '2026 · T2')

    def test_api_failure_and_recovery(self):
        from app import render_dashboard
        with patch.dict(os.environ, {'DATA_FILE': 'arquivo_que_nao_existe.csv'}):
            response = requests.get(self.base_url + '/api/v1/observacoes', timeout=5)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()['error']['code'], 'SOURCE_UNAVAILABLE')
            result = render_dashboard(0, 0, None, 'bahia', [], [], [14, 130], [])
        self.assertEqual(result[0], [])
        self.assertNotIn('arquivo_que_nao_existe', result[6])
        self.assertIn('Falha', result[6])
        recovered = render_dashboard(0, 0, None, 'bahia', [], [], [14, 130], [])
        self.assertEqual(len(recovered[0]), 6)

    def test_csv_changes_are_visible_on_next_request(self):
        frame, _ = load_data()
        sample = frame.iloc[:2][COLUMNS].copy()
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'dados.csv'
            sample.to_csv(path, index=False)
            with patch.dict(os.environ, {'DATA_FILE': str(path)}):
                first = requests.get(self.base_url + '/api/v1/observacoes', timeout=5).json()
                sample.loc[sample.index[0], 'vd4016'] = 9876
                sample.to_csv(path, index=False)
                second = requests.get(self.base_url + '/api/v1/observacoes', timeout=5).json()
                updated, _ = load_data()
        self.assertEqual(first['meta']['total'], 2)
        self.assertNotEqual(first['meta']['versao'], second['meta']['versao'])
        self.assertEqual(second['data'][0]['vd4016'], 9876)
        self.assertEqual(updated.iloc[0].vd4016, 9876)

    def test_contract_nulls_and_methods(self):
        response = requests.get(self.base_url + '/api/v1/observacoes', timeout=10)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        payload = response.json()
        self.assertEqual(payload['meta']['total'], len(payload['data']))
        self.assertEqual(set(payload['data'][0]), set(COLUMNS))
        self.assertTrue(any(row['vd4016'] is None for row in payload['data']))
        self.assertNotIn('NaN', response.text)
        self.assertEqual(requests.post(self.base_url + '/api/v1/observacoes', timeout=5).status_code, 405)
        self.assertEqual(requests.get(self.base_url + '/inexistente', timeout=5).status_code, 404)
        self.assertEqual(requests.get(self.base_url + '/health', timeout=5).json()['status'], 'ok')
        contract = requests.get(self.base_url + '/openapi.json', timeout=5).json()
        self.assertEqual(contract['openapi'], '3.1.0')
        expected = json.loads((Path(__file__).resolve().parents[1] / 'api/openapi.json').read_text(encoding='utf-8'))
        self.assertEqual(contract, expected)

    def test_client_rejects_broken_contract(self):
        # Exercita o cliente HTTP com um servidor real de contrato inválido.
        from flask import Flask, jsonify
        broken = Flask('broken-contract')
        broken.add_url_rule('/api/v1/observacoes', view_func=lambda: jsonify(data=[], meta={'total': 1}))
        service = make_server('127.0.0.1', 0, broken, threaded=True)
        thread = Thread(target=service.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {'API_BASE_URL': f'http://127.0.0.1:{service.server_port}'}):
                with self.assertRaises(ValueError):
                    load_data()
        finally:
            service.shutdown()
            service.server_close()
            thread.join(timeout=5)

    def test_empty_source_and_invalid_source(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'dados.csv'
            pd.DataFrame(columns=COLUMNS).to_csv(path, index=False)
            with patch.dict(os.environ, {'DATA_FILE': str(path)}):
                frame, _ = load_data()
                self.assertTrue(frame.empty)
                from app import render_dashboard
                rendered = render_dashboard(0, 0, None, 'bahia', [], [], [14, 130], [])
                self.assertEqual(len(rendered[0]), 6)
                self.assertEqual(rendered[5], [])
                pd.DataFrame({'ano': [2026]}).to_csv(path, index=False)
                response = requests.get(self.base_url + '/api/v1/observacoes', timeout=5)
                self.assertEqual(response.status_code, 503)


if __name__ == '__main__':
    unittest.main()
