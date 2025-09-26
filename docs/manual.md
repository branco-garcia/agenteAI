
## **5. docs/manual.md**
```markdown
# Manual de Usuario

## Interfaz Principal

### Acceso a la Aplicación
1. Ejecutar el backend: `python agentemensaje.py`
2. Abrir navegador en: `http://localhost:5000`
3. Interfaz de chat cargará automáticamente

### Elementos de la Interfaz
- **Área de Chat:** Muestra conversación con el agente
- **Campo de Texto:** Para escribir comandos
- **Botón Enviar:** Envía el comando al agente
- **Cabecera:** Información del sistema y modelos disponibles

## Comandos Disponibles

### Gestión de Máquinas
| Comando | Ejemplo | Descripción |
|---------|---------|-------------|
| Listar máquinas | "lista las máquinas" | Muestra todas las máquinas disponibles |
| Encender máquina | "enciende servidor1" | Enciende una máquina específica |
| Apagar máquina | "apaga 172.16.25.201" | Apaga una máquina por nombre o IP |
| Consultar estado | "estado de web-server" | Muestra estado específico de máquina |

### Consultas de Hardware
| Comando | Ejemplo | Respuesta |
|---------|---------|-----------|
| Consultar RAM | "RAM de servidor1" | Memoria disponible en GB |
| Consultar almacenamiento | "disco de database" | Almacenamiento en GB |
| Consultar CPUs | "procesadores de app-server" | Número de núcleos |

### Consultas de Red
| Comando | Ejemplo | Propósito |
|---------|---------|-----------|
| Listar subredes | "muestra las subredes" | Lista configuración de red |
| Consultar IPs | "IP de las máquinas" | Direcciones IP asignadas |

## Ejemplos de Conversación

### Consulta Básica


## Consejos de Uso

### Mejores Prácticas
- Usar nombres exactos de máquinas para comandos específicos
- Verificar estado antes de ejecutar acciones
- Utilizar el monitoreo automático para seguimiento

### Solución de Problemas
- **Comando no reconocido:** Reformular la pregunta
- **Error de conexión:** Verificar estado de MaaS
- **Sin respuesta:** Revisar logs del backend

## Notificaciones

El sistema envía notificaciones automáticas via Telegram cuando:
- Una máquina cambia de estado
- Se ejecutan comandos críticos
- Ocurren errores en el sistema

## Seguridad
- Todas las comunicaciones son locales
- No se almacenan credenciales en el frontend
- Validación de comandos antes de ejecución