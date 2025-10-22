from flask import jsonify, request
import asyncio
from services.chat_service import responder_pregunta

def setup_chat_routes(app):
    @app.route("/preguntar", methods=["POST"])
    def preguntar():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"respuesta": "❌ No se recibieron datos JSON"}), 400
                
            pregunta = data.get("pregunta", "")
            if not pregunta.strip():
                return jsonify({"respuesta": "Por favor, ingresa una pregunta."}), 400
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            respuesta = loop.run_until_complete(responder_pregunta(pregunta))
            return jsonify({"respuesta": respuesta})
        except Exception as e:
            return jsonify({"respuesta": f"❌ Error procesando la pregunta: {e}"}), 500