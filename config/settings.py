import os

# Configuración general del proyecto
PROJECT_NAME = "Agente Conversacional MaaS"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"