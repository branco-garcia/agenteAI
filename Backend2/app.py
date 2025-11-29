from flask import Flask, jsonify
from flask_cors import CORS
import threading
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from models.monitor import MonitorMaquinas
from services.telegram_service import enviar_notificacion_telegram
# Importar rutas
from routes.chat_routes import setup_chat_routes
from routes.monitor_routes import setup_monitor_routes
from routes.dashboard_routes import setup_dashboard_routes
from routes.commissioning_routes import setup_commissioning_routes
from routes.deploy_routes import setup_deploy_routes
app = Flask(__name__)
CORS(app)

# Instancia global del monitor
monitor = MonitorMaquinas()

# Configurar rutas
setup_chat_routes(app)
setup_monitor_routes(app, monitor)
setup_dashboard_routes(app)
setup_commissioning_routes(app)
setup_deploy_routes(app)

@app.route('/')
def index(): 
    return jsonify({
        "mensaje": "MAAS Bot API está funcionando correctamente",
        "version": "2.0",
        "endpoints": {
            "/preguntar": "POST - Enviar preguntas al asistente",
            "/monitor/start": "POST - Iniciar monitoreo", 
            "/monitor/stop": "POST - Detener monitoreo",
            "/monitor/status": "GET - Estado del monitoreo",
            "/dashboard/metricas": "GET - Métricas del dashboard",
            "/health": "GET - Health check"
        }
    })

@app.route('/health', methods=["GET"])
def health_check(): 
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "MAAS Bot API"
    })

def iniciar_aplicacion(): 
    print("Iniciando aplicación MAAS Bot...")
    
    # Notificación de inicio
    mensaje_inicio = f"<b>MAAS Bot Iniciado</b>\nSistema de monitorización listo\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_inicio)).start()

if __name__ == "__main__":
    iniciar_aplicacion()
    print("Servidor Flask iniciado en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)