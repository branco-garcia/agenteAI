import os

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "una_clave_secreta_muy_segura")