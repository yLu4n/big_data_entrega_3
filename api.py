"""API REST própria para a base tratada da PNAD Contínua."""
import json
import os
from pathlib import Path

from flask import Flask, jsonify, send_file

from dataset import COLUMNS, read_snapshot


def create_app():
    api = Flask(__name__)
    api.json.ensure_ascii = False

    @api.after_request
    def prevent_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    @api.get('/health')
    def health():
        return jsonify(status='ok', service='empreendedorismo-feminino-bahia-api', version='1.0.0')

    @api.get('/openapi.json')
    def contract():
        return send_file(Path(__file__).resolve().parent / 'api' / 'openapi.json', mimetype='application/json')

    @api.get('/api/v1/observacoes')
    def observations():
        try:
            frame, meta = read_snapshot()
            data = json.loads(frame[COLUMNS].to_json(orient='records', double_precision=15))
            return jsonify(data=data, meta=meta)
        except Exception:
            api.logger.warning('Fonte de dados indisponível ou inválida.')
            return jsonify(error={'code': 'SOURCE_UNAVAILABLE',
                                  'message': 'Não foi possível ler a base tratada. Verifique DATA_FILE ou o pacote original.'}), 503

    @api.errorhandler(404)
    def not_found(_error):
        return jsonify(error={'code': 'NOT_FOUND', 'message': 'Endpoint não encontrado.'}), 404

    @api.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error={'code': 'METHOD_NOT_ALLOWED', 'message': 'Use GET para consultar os dados.'}), 405

    return api


api = create_app()

if __name__ == '__main__':
    api.run(host='127.0.0.1', port=int(os.getenv('API_PORT', '8000')), debug=False)
