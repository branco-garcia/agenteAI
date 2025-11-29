from flask import jsonify
import asyncio
import threading
from datetime import datetime
from services.maas_client import obtener_maquinas_nuevas
from services.telegram_service import enviar_notificacion_telegram

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
                    "mensaje": "El Monitoreo de máquinas MAAS iniciado correctamente"
                })
            else:
                return jsonify({
                    "estado": "El monitoreo ya está activo",
                    "mensaje": "El monitoreo ya se encuentra en ejecución"
                })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/monitor/stop", methods=["POST"])
    def detener_monitor():
        """Endpoint para detener el monitoreo"""
        try:
            monitor.detener_monitoreo()
            return jsonify({
                "estado": "Monitoreo detenido",
                "mensaje": "El Monitoreo de máquinas detenido correctamente"
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/monitor/status", methods=["GET"])
    def estado_monitor():
        """Endpoint para ver el estado del monitoreo"""
        return jsonify({
            "monitoreo_activo": monitor.monitoreo_activo,
            "maquinas_monitoreadas": len(monitor.estados_anteriores),
            "intervalo_segundos": monitor.intervalo,
            "estado": "Activo" if monitor.monitoreo_activo else "Inactivo"
        })

    @app.route("/monitor/check-new", methods=["POST"])
    @app.route("/debug/power/<system_id>", methods=["GET"])
    def debug_power_route(system_id):
        """Endpoint para debug de power parameters"""
        try:
            from services.maas_client import debug_power_parameters
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            resultado = loop.run_until_complete(debug_power_parameters(system_id))
            return jsonify({"debug_power": resultado})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    def verificar_maquinas_nuevas():
        """Endpoint para verificar máquinas nuevas manualmente"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            maquinas_nuevas = loop.run_until_complete(obtener_maquinas_nuevas())
            
            # Notificar por Telegram si hay máquinas nuevas
            if maquinas_nuevas:
                for maquina in maquinas_nuevas:
                    mensaje = (
                        f"🆕 <b>NUEVA MÁQUINA DETECTADA (Manual)</b>\n\n"
                        f"🔧 <b>Nombre:</b> {maquina['hostname']}\n"
                        f"🌐 <b>IP:</b> {maquina['ip']}\n"
                        f"🆔 <b>ID:</b> {maquina['system_id']}\n"
                        f"📊 <b>Estado:</b> {maquina['status']}\n\n"
                        f"💡 <i>Esta máquina necesita commissioning y deploy</i>"
                    )
                    threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje)).start()
            
            return jsonify({
                "maquinas_nuevas": maquinas_nuevas,
                "total": len(maquinas_nuevas),
                "mensaje": f"Se encontraron {len(maquinas_nuevas)} máquinas nuevas",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500