# Arquitectura del Sistema

## Componentes Principales

### Backend (agentemensaje.py)
**Tecnologías:** Python 3.8+, Flask, asyncio
**Responsabilidades:**
- Servidor web con endpoints REST
- Integración con API MaaS
- Procesamiento de lenguaje natural via Gemini AI
- Sistema de monitoreo automático
- Gestión de notificaciones Telegram

### Frontend (index.html)
**Tecnologías:** HTML5, CSS3, JavaScript vanilla
**Responsabilidades:**
- Interfaz de usuario conversacional
- Comunicación asíncrona con backend
- Experiencia de usuario responsive

### Servicios Externos
- **MaaS API:** Gestión de infraestructura física
- **Gemini AI:** Procesamiento de lenguaje natural
- **Telegram API:** Sistema de notificaciones

## Flujos de Datos

### Flujo de Comando de Usuario
1. Usuario envía comando por interfaz web
2. Frontend hace petición HTTP POST a /preguntar
3. Backend procesa comando con Gemini AI
4. Backend ejecuta acción en MaaS API
5. Backend envía respuesta al frontend
6. Sistema de monitoreo detecta cambios y notifica

### Flujo de Monitoreo
1. Monitor verifica estado cada 30 segundos
2. Detecta cambios en máquinas MaaS
3. Envía notificaciones via Telegram
4. Registra eventos en log del sistema


