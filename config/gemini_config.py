import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCVmwiNmBqMaYQrvGDMBzPY_GJwrDNynt4")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Configuración de generación de respuestas
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", 1000))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", 0.7))