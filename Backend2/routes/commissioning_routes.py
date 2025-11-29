from flask import jsonify, request
import asyncio
from services.maas_client import listar_maquinas_para_commissioning, ejecutar_commissioning, obtener_estado_commissioning

def setup_commissioning_routes(app):
    """Configura las rutas para commissioning"""
    
    @app.route("/commissioning/maquinas", methods=["GET"])
    def listar_maquinas_commissioning():
        """Endpoint para listar máquinas disponibles para commissioning"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            maquinas = loop.run_until_complete(listar_maquinas_para_commissioning())
            return jsonify({
                'maquinas': maquinas,
                'total': len(maquinas)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route("/commissioning/ejecutar", methods=["POST"])
    def ejecutar_commissioning_endpoint():
        """Endpoint para ejecutar commissioning en una máquina"""
        try:
            data = request.get_json()
            if not data or 'system_id' not in data:
                return jsonify({'error': 'Se requiere system_id'}), 400
            
            system_id = data['system_id']
            opciones = data.get('opciones', {})
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            resultado = loop.run_until_complete(ejecutar_commissioning(system_id, opciones))
            
            return jsonify(resultado)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route("/commissioning/estado/<system_id>", methods=["GET"])
    def estado_commissioning(system_id):
        """Endpoint para obtener estado del commissioning"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            estado = loop.run_until_complete(obtener_estado_commissioning(system_id))
            return jsonify(estado)
        except Exception as e:
            return jsonify({'error': str(e)}), 500