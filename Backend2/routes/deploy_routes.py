from flask import jsonify, request
import asyncio
from services.maas_client import listar_maquinas_para_deploy, ejecutar_deploy

def setup_deploy_routes(app):
    """Configura las rutas para deploy"""

    @app.route("/deploy/maquinas", methods=["GET"])
    def listar_maquinas_deploy():
        """Endpoint para listar máquinas disponibles para deploy"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            maquinas = loop.run_until_complete(listar_maquinas_para_deploy())
            return jsonify({
                'maquinas': maquinas,
                'total': len(maquinas)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/deploy/ejecutar", methods=["POST"])
    def ejecutar_deploy_endpoint():
        """Endpoint para ejecutar deploy en una máquina"""
        try:
            data = request.get_json()
            if not data or 'system_id' not in data:
                return jsonify({'error': 'Se requiere system_id'}), 400

            system_id = data['system_id']
            opciones = data.get('opciones', {})
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            resultado = loop.run_until_complete(ejecutar_deploy(system_id, opciones))

            return jsonify(resultado)

        except Exception as e:
            return jsonify({'error': str(e)}), 500