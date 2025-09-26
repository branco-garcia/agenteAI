# Documentación de la API

## Endpoints Disponibles

### GET /
**Descripción:** Sirve la interfaz web principal
**Respuesta:** HTML de la interfaz de chat
**Ejemplo:**
```bash
curl http://localhost:5000/

POST /preguntar

Descripción: Procesa preguntas/comandos del usuario
Body:

{
    "pregunta": "string - comando en lenguaje natural"
}

{
    "respuesta": "string - respuesta del agente IA"
}

curl -X POST http://localhost:5000/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Lista las máquinas disponibles"}'

POST /monitor/start

Descripción: Inicia el sistema de monitoreo automático
Respuesta

{
    "estado": "Monitoreo iniciado"
}

POST /monitor/stop

{
    "estado": "Monitoreo detenido"
}

GET /monitor/status

Descripción: Obtiene estado actual del monitoreo
Respuesta:

{
    "monitoreo_activo": true,
    "maquinas_monitoreadas": 5,
    "intervalo_segundos": 30
}


