import os

MAAS_URL = os.getenv("MAAS_URL", "http://172.16.25.2:5240/MAAS")
MAAS_API_KEY = os.getenv("MAAS_API_KEY", "E9nebNWw3WhSejrkAL:Av2xxeCgHq2jeGL2rG:skcKZQp85vMdya2WubtERYXhMxf7pTty")

# Configuración de tiempo de espera para conexiones MaaS (en segundos)
MAAS_TIMEOUT = int(os.getenv("MAAS_TIMEOUT", 30))