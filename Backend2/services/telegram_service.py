import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def enviar_notificacion_telegram(mensaje):
    """Envía notificación a Telegram (para el servicio de monitoreo)"""
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("Configuración de Telegram no completada")
            return False
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando notificación a Telegram: {e}")
        return False

def enviar_mensaje_telegram(chat_id, mensaje, parse_mode='HTML'):
    """Envía mensaje a un chat específico de Telegram"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("Token de Telegram no configurado")
            return False
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": parse_mode
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")
        return False