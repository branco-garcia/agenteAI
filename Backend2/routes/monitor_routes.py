from flask import jsonify
import asyncio
import threading

def setup_monitor_routes(app, monitor):
    """Configura las rutas del monitor"""
    
    @app.route("/monitor/start", methods=["POST"])
    def iniciar_monitor():
        """Endpoint para iniciar el monitoreo"""
        try:
            if not monitor.monitoreo_activo:
                threading.Thread(target=lambda: asyncio.run(monitor.iniciar_monitoreo()), daemon=True).start()
                return jsonify({
                    "estado": "Monitoreo iniciado",
                    "mensaje": "🔍 Monitoreo de máquinas MAAS iniciado correctamente"
                })
            else:
                return jsonify({
                    "estado": "El monitoreo ya está activo",
                    "mensaje": "El monitoreo ya se encuentra en ejecución"
                })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/monitor/stop", methods=["POST"])
    def detener_monitor():
        """Endpoint para detener el monitoreo"""
        try:
            monitor.detener_monitoreo()
            return jsonify({
                "estado": "Monitoreo detenido", 
                "mensaje": "⏹️ Monitoreo de máquinas detenido correctamente"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/monitor/status", methods=["GET"])
    def estado_monitor():
        """Endpoint para ver el estado del monitoreo"""
        return jsonify({
            "monitoreo_activo": monitor.monitoreo_activo,
            "maquinas_monitoreadas": len(monitor.estados_anteriores),
            "intervalo_segundos": monitor.intervalo,
            "estado": "Activo" if monitor.monitoreo_activo else "Inactivo"
        })