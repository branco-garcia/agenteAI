from flask import jsonify
import asyncio
from services.maas_client import obtener_metricas_dashboard

def setup_dashboard_routes(app):
    """Configura las rutas del dashboard"""
    
    @app.route("/dashboard/metricas", methods=["GET"])
    def obtener_metricas_dashboard_endpoint():
        """Endpoint para obtener todas las métricas del dashboard"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            metricas = loop.run_until_complete(obtener_metricas_dashboard())
            return jsonify(metricas)
        except Exception as e:
            print(f"Error en endpoint /dashboard/metricas: {e}")
            return jsonify({
                "resumen": {},
                "maquinas": [],
                "red": {},
                "alertas": [],
                "rendimiento": {},
                "error": str(e)
            }), 500

    @app.route("/dashboard/maquinas", methods=["GET"])
    def obtener_maquinas_dashboard_endpoint():
        """Endpoint para obtener detalle de máquinas"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            metricas = loop.run_until_complete(obtener_metricas_dashboard())
            return jsonify(metricas.get("maquinas", []))
        except Exception as e:
            print(f"Error en endpoint /dashboard/maquinas: {e}")
            return jsonify({"error": str(e), "maquinas": []}), 500

    @app.route("/dashboard/alertas", methods=["GET"])
    def obtener_alertas_endpoint():
        """Endpoint para obtener alertas activas"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            metricas = loop.run_until_complete(obtener_metricas_dashboard())
            return jsonify(metricas.get("alertas", []))
        except Exception as e:
            print(f"Error en endpoint /dashboard/alertas: {e}")
            return jsonify({"error": str(e), "alertas": []}), 500