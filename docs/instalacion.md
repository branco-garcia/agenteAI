# Instalación y Configuración

## Requisitos Previos

- Python 3.8 o superior
- Acceso a una instancia de MaaS
- API Key de Gemini AI
- Token de bot de Telegram

## Pasos de Instalación

1. Clonar o descargar el proyecto.

2. Instalar dependencias:

```bash
pip install -r requirements.txt

MAAS_URL=http://tu_servidor_maas:5240/MAAS
MAAS_API_KEY=tu_api_key_maas
GEMINI_API_KEY=tu_api_key_gemini
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id

python backend.py