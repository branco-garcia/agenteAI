# Registro de Decisiones Técnicas

## ADR-001: Selección de Framework Web
**Fecha:** Octubre 2024
**Estado:** Aprobado

### Contexto
Necesidad de servidor web ligero para interfaz conversacional.

### Decisión
Utilizar Flask sobre alternativas como Django o FastAPI.

### Consecuencias
- ✅ Menor complejidad y overhead
- ✅ Rápido desarrollo de prototipo
- ✅ Fácil integración con APIs existentes
- ⚠️ Limitaciones en escalabilidad avanzada

## ADR-002: Integración de IA Conversacional
**Fecha:** Octubre 2024
**Estado:** Aprobado

### Contexto
Requerimiento de procesamiento de lenguaje natural para comandos.

### Decisión
Usar Gemini AI sobre OpenAI GPT o modelos locales.

### Consecuencias
- ✅ Buen balance costo/rendimiento
- ✅ API fácil de integrar
- ✅ Soporte para español nativo
- ⚠️ Dependencia de servicio externo

## ADR-003: Sistema de Notificaciones
**Fecha:** Octubre 2024
**Estado:** Aprobado

### Contexto
Necesidad de notificaciones inmediatas para cambios de estado.

### Decisión
Implementar Telegram Bot sobre email o Slack.

### Consecuencias
- ✅ Notificaciones en tiempo real
- ✅ Bajo costo de implementación
- ✅ Amplia adopción entre usuarios
- ⚠️ Dependencia de aplicación externa