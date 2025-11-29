import asyncio
import re
from config import CORTESIAS
from services.maas_client import listar_maquinas, listar_subredes, encender_maquina, apagar_maquina, buscar_maquina_por_ip
from services.gemini_service import generar_respuesta_gemini
from services.maas_client import obtener_maquinas_nuevas, configurar_power_virsh
from services.maas_client import listar_maquinas_para_commissioning, ejecutar_commissioning
from services.maas_client import listar_maquinas_para_deploy, ejecutar_deploy

# Estados de conversación para configuración interactiva:
estados_conversacion = {}

class EstadoConfiguracion:
    def __init__(self, system_id, hostname_maas, ip_maquina):
        self.system_id = system_id
        self.hostname_maas = hostname_maas
        self.ip_maquina = ip_maquina
        self.paso_actual = "esperando_nombre"
        self.vm_id_asignado = None

async def responder_pregunta(pregunta):
    try:
        pregunta_lower = pregunta.lower()

        # Filtrar cortesias
        if any(c in pregunta_lower for c in CORTESIAS):
            return "[De nada] 😊"

        # ====== COMANDOS DE COMMISSIONING - DEBEN IR PRIMERO ========

        # Comando para ejecutar commissioning CON NÚMERO (más específico primero)
        if any(palabra in pregunta_lower for palabra in ['commissioning', 'comisionar']) and any(c.isdigit() for c in pregunta):
            try:
                # Extraer número de la pregunta
                numeros = [int(s) for s in pregunta.split() if s.isdigit()]
                if not numeros:
                    return "❌ Por favor, especifica el número de la máquina. Ejemplo: 'commissioning 1'"

                numero_maquina = numeros[0]
                maquinas = await listar_maquinas_para_commissioning()

                if numero_maquina < 1 or numero_maquina > len(maquinas):
                    return f"❌ Número inválido. Por favor elige un número entre 1 y {len(maquinas)}"

                maquina_seleccionada = maquinas[numero_maquina - 1]
                resultado = await ejecutar_commissioning(maquina_seleccionada['system_id'])

                if resultado['success']:
                    respuesta = f"✅ **COMMISSIONING INICIADO**\n\n"
                    respuesta += f"**Máquina:** {maquina_seleccionada['hostname']}\n"
                    respuesta += f"**IP:** {maquina_seleccionada['ip']}\n"
                    respuesta += f"**ID:** {maquina_seleccionada['system_id']}\n\n"
                    respuesta += "⏳ El proceso de commissioning ha comenzado. Esto puede tomar varios minutos.\n"
                    respuesta += "💻 Puedes monitorear el progreso en el dashboard de MAAS."

                else:
                    respuesta = f"❌ **ERROR EN COMMISSIONING**\n\n{resultado['message']}"

                return respuesta

            except Exception as e:
                return f"❌ Error al ejecutar commissioning: {str(e)}"

        # Comando para listar máquinas para commissioning (sin número)
        elif any(palabra in pregunta_lower for palabra in ['commissioning', 'comisionar', 'maquinas para commissioning', 'máquinas para commissioning']):
            try:
                maquinas = await listar_maquinas_para_commissioning()

                if not maquinas:
                    return "❌ No hay máquinas disponibles para commissioning. Todas las máquinas están en estado 'Deployed'."

                respuesta = "🔄 **MÁQUINAS DISPONIBLES PARA COMMISSIONING**\n\n"
                for i, maquina in enumerate(maquinas, 1):
                    respuesta += f"{i}. **{maquina['hostname']}**\n"
                    respuesta += f"   IP: {maquina['ip']}\n"
                    respuesta += f"   Estado: {maquina['status']}\n"
                    respuesta += f"   ID: {maquina['system_id']}\n\n"

                respuesta += "💡 **Para ejecutar commissioning:**\n"
                respuesta += "Escribe: 'commissioning [número]' o 'comisionar [número]'\n"
                respuesta += "Ejemplo: 'commissioning 1' para ejecutar en la primera máquina"

                return respuesta

            except Exception as e:
                return f"❌ Error al listar máquinas para commissioning: {str(e)}"

        # ====== COMANDOS DE DEPLOY ========

        # Comando para ejecutar deploy CON NÚMERO (y posiblemente opciones)
        elif any(palabra in pregunta_lower for palabra in ['deploy', 'desplegar']) and any(c.isdigit() for c in pregunta):
            try:
                # Extraer número y opciones
                partes = pregunta.split()
                numeros = [int(s) for s in partes if s.isdigit()]
                if not numeros:
                    return "❌ Por favor, especifica el número de la máquina. Ejemplo: 'deploy 1'"

                numero_maquina = numeros[0]
                maquinas = await listar_maquinas_para_deploy()

                if numero_maquina < 1 or numero_maquina > len(maquinas):
                    return f"❌ Número inválido. Por favor elige un número entre 1 y {len(maquinas)}"

                # Procesar opciones si las hay
                opciones = {}
                for parte in partes:
                    if ':' in parte:
                        key, value = parte.split(':', 1)
                        opciones[key.strip().lower()] = value.strip()

                maquina_seleccionada = maquinas[numero_maquina - 1]
                resultado = await ejecutar_deploy(maquina_seleccionada['system_id'], opciones)

                if resultado['success']:
                    respuesta = f"✅ **DEPLOY INICIADO**\n\n"
                    respuesta += f"**Máquina:** {maquina_seleccionada['hostname']}\n"
                    respuesta += f"**IP:** {maquina_seleccionada['ip']}\n"
                    respuesta += f"**ID:** {maquina_seleccionada['system_id']}\n"
                    
                    if opciones:
                        respuesta += f"**Opciones:** {opciones}\n\n"
                    else:
                        respuesta += "\n"
                    
                    respuesta += "⏳ El proceso de deploy ha comenzado. Esto puede tomar varios minutos.\n"
                    respuesta += "💻 Puedes monitorear el progreso en el dashboard de MAAS."

                else:
                    respuesta = f"❌ **ERROR EN DEPLOY**\n\n{resultado['message']}"

                return respuesta

            except Exception as e:
                return f"❌ Error al ejecutar deploy: {str(e)}"

        # Comando para listar máquinas para deploy (sin número)
        elif any(palabra in pregunta_lower for palabra in ['deploy', 'desplegar', 'maquinas para deploy', 'máquinas para deploy']):
            try:
                maquinas = await listar_maquinas_para_deploy()

                if not maquinas:
                    return "❌ No hay máquinas disponibles para deploy. Las máquinas deben estar en estado 'Ready'."

                respuesta = "🚀 **MÁQUINAS DISPONIBLES PARA DEPLOY**\n\n"
                for i, maquina in enumerate(maquinas, 1):
                    respuesta += f"{i}. **{maquina['hostname']}**\n"
                    respuesta += f"   IP: {maquina['ip']}\n"
                    respuesta += f"   Estado: {maquina['status']}\n"
                    respuesta += f"   SO: {maquina['osystem']} | Arquitectura: {maquina['architecture']}\n"
                    respuesta += f"   RAM: {maquina['memory_gb']} GB | CPUs: {maquina['cpu_count']}\n"
                    respuesta += f"   ID: {maquina['system_id']}\n\n"

                respuesta += "💡 **Para ejecutar deploy:**\n"
                respuesta += "Escribe: 'deploy [número]' o 'desplegar [número]'\n"
                respuesta += "Ejemplo: 'deploy 1' para desplegar la primera máquina\n\n"
                respuesta += "🔧 **Opciones de deploy personalizado:**\n"
                respuesta += "Puedes añadir opciones después del número:\n"
                respuesta += "- distro:[nombre] (ej: distro:jammy)\n"
                respuesta += "- kernel:[nombre] (ej: kernel:hwe-22.04)\n"
                respuesta += "Ejemplo: 'deploy 1 distro:focal kernel:hwe-20.04'"

                return respuesta

            except Exception as e:
                return f"❌ Error al listar máquinas para deploy: {str(e)}"

        # Comando para deploy con opciones específicas
        elif any(palabra in pregunta_lower for palabra in ['deploy personalizado', 'deploy con opciones']):
            try:
                maquinas = await listar_maquinas_para_deploy()
                
                if not maquinas:
                    return "❌ No hay máquinas disponibles para deploy."

                respuesta = "🔧 **DEPLOY PERSONALIZADO**\n\n"
                respuesta += "**Máquinas disponibles:**\n"
                for i, maquina in enumerate(maquinas, 1):
                    respuesta += f"{i}. {maquina['hostname']} ({maquina['ip']})\n"

                respuesta += "\n💡 **Para deploy personalizado:**\n"
                respuesta += "Escribe: 'deploy [número] [opciones]'\n"
                respuesta += "Opciones disponibles:\n"
                respuesta += "- distro:[nombre] (ej: distro:jammy)\n"
                respuesta += "- kernel:[nombre] (ej: kernel:hwe-22.04)\n"
                respuesta += "Ejemplo: 'deploy 1 distro:focal kernel:hwe-20.04'"

                return respuesta

            except Exception as e:
                return f"❌ Error: {str(e)}"

        # =========== FIN COMANDOS DE DEPLOY ==========

        # DETECTAR COMANDOS DE CONTROL DE MÁQUINAS:
        # Comando para encender máquinas:
        elif any(palabra in pregunta_lower for palabra in ['enciendo', 'encienda', 'prende', 'prenda', 'power on', 'encender']):
            # Extraer el identificador de la máquina:
            identificador = None
            # Buscar por nombre de máquina:
            maquinas_texto = await listar_maquinas()

            for linea in maquinas_texto.split('\n'):
                if 'MÁQUINA:' in linea:
                    partes = linea.split('(')
                    if len(partes) > 1:
                        # Extraer nombre limpio sin emojis:
                        nombre_completo = partes[0].replace('MÁQUINA:', '').strip()
                        nombre_maquina = re.sub(r'[^a-zA-Z0-9]', '', nombre_completo).strip()
                        system_id = partes[1].replace(')', '').strip()

                        # Coincidencia más flexible:
                        if nombre_maquina.lower() in pregunta_lower:
                            identificador = nombre_maquina
                            break
                        elif system_id.lower() in pregunta_lower:
                            identificador = system_id
                            break

            # Buscar por ip:
            if not identificador:
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                ips = re.findall(ip_pattern, pregunta)
                if ips:
                    maquina_por_ip = await buscar_maquina_por_ip(ips[0])
                    if maquina_por_ip:
                        identificador = maquina_por_ip.hostname

            if not identificador:
                # Si no se encontró identificador, mostrar máquinas disponibles:
                maquinas_disponibles = []
                for linea in maquinas_texto.split('\n'):
                    if 'MÁQUINA:' in linea:
                        nombre_completo = linea.split('MÁQUINA:')[1].split('(')[0].strip()
                        nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '', nombre_completo).strip()
                        maquinas_disponibles.append(nombre_limpio)

                if maquinas_disponibles:
                    return f"❓ ¿Qué máquina quieres encender?\n\n Máquinas disponibles:\n" + "\n".join([f"• {maquina}" for maquina in maquinas_disponibles])
                else:
                    return "❌ No se encontraron máquinas disponibles."

            # Ejecutar comando de encender:
            resultado = await encender_maquina(identificador)
            return resultado

        # Comando para apagar maquina:
        elif any(palabra in pregunta_lower for palabra in ['apaga', 'apague', 'apagar', 'power off', 'apagado']):
            # Extraer el identificador de la máquina:
            identificador = None
            # Buscar por nombre de máquina:
            maquinas_texto = await listar_maquinas()

            for linea in maquinas_texto.split('\n'):
                if 'MÁQUINA:' in linea:
                    partes = linea.split('(')
                    if len(partes) > 1:
                        # Extraer nombre limpio sin emojis:
                        nombre_completo = partes[0].replace('MÁQUINA:', '').strip()
                        nombre_maquina = re.sub(r'[^a-zA-Z0-9]', '', nombre_completo).strip()
                        system_id = partes[1].replace(')', '').strip()

                        # Coincidencia más flexible:
                        if nombre_maquina.lower() in pregunta_lower:
                            identificador = nombre_maquina
                            break
                        elif system_id.lower() in pregunta_lower:
                            identificador = system_id
                            break

            # Buscar por ip:
            if not identificador:
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                ips = re.findall(ip_pattern, pregunta)
                if ips:
                    maquina_por_ip = await buscar_maquina_por_ip(ips[0])
                    if maquina_por_ip:
                        identificador = maquina_por_ip.hostname

            if not identificador:
                # Si no se encontró identificador, mostrar máquinas disponibles:
                maquinas_disponibles = []
                for linea in maquinas_texto.split('\n'):
                    if 'MÁQUINA:' in linea:
                        nombre_completo = linea.split('MÁQUINA:')[1].split('(')[0].strip()
                        nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '', nombre_completo).strip()
                        maquinas_disponibles.append(nombre_limpio)

                if maquinas_disponibles:
                    return f"❓ ¿Qué máquina quieres apagar?\n\n Máquinas disponibles:\n" + "\n".join([f"• {maquina}" for maquina in maquinas_disponibles])
                else:
                    return "❌ No se encontraron máquinas disponibles."

            # Ejecutar comando de apagar:
            resultado = await apagar_maquina(identificador)
            return resultado

        # Comando para verificar maquinas nuevas:
        elif any(palabra in pregunta_lower for palabra in ['maquinas nuevas', 'máquinas nuevas', 'nuevas detectadas']):
            try:
                maquinas_nuevas = await obtener_maquinas_nuevas()
                if not maquinas_nuevas:
                    return "✅ No hay máquinas nuevas detectadas. Todas las máquinas están configuradas."

                respuesta = "🆕 **MÁQUINAS NUEVAS DETECTADAS**\n\n"
                for maquina in maquinas_nuevas:
                    respuesta += (
                        f"**Nombre:** {maquina['hostname']}\n"
                        f"**IP:** {maquina['ip']}\n"
                        f"**Estado:** {maquina['status']}\n"
                        f"**ID:** {maquina['system_id']}\n\n"
                    )

                respuesta += "⚠️ *Estas máquinas necesitan proceso de commissioning y deploy*"
                return respuesta
            except Exception as e:
                return f"❌ Error al verificar máquinas nuevas: {str(e)}"

        # Comando para iniciar configuración interactiva:
        elif any(palabra in pregunta_lower for palabra in ['configurar maquina', 'configurar máquina', 'asignar nombre']):
            # Primero, obtener máquinas nuevas
            maquinas_nuevas = await obtener_maquinas_nuevas()

            if not maquinas_nuevas:
                return "✅ No hay máquinas nuevas para configurar."

            if len(maquinas_nuevas) == 1:
                # Si hay solo una máquina nueva, empezar configuración directa:
                maquina = maquinas_nuevas[0]
                estados_conversacion['usuario_actual'] = EstadoConfiguracion(
                    maquina['system_id'],
                    maquina['hostname'],
                    maquina['ip']
                )

                return (
                    f"⚙️ **CONFIGURAR MÁQUINA NUEVA**\n\n"
                    f"**Información de la máquina:**\n"
                    f"**Hostname MAAS:** {maquina['hostname']}\n"
                    f"**IP:** {maquina['ip']}\n"
                    f"**ID:** {maquina['system_id']}\n\n"
                    f"**¿Cómo se llama esta máquina en Virsh?**\n"
                    f"**Responde con el VM ID exacto (ej: maq2, servidor-web, etc.)**"
                )

            else:
                # Si hay múltiples máquinas, listarlas
                respuesta = "🆕 **MÚLTIPLES MÁQUINAS NUEVAS DETECTADAS**\n\n"
                for i, maquina in enumerate(maquinas_nuevas, 1):
                    respuesta += (
                        f"{i}. **{maquina['hostname']}** (IP: {maquina['ip']})\n"
                    )

                respuesta += (
                    f"\n**Responde con el número de la máquina que quieres configurar**\n"
                    f"**Ejemplo: '1' para {maquinas_nuevas[0]['hostname']}**"
                )

                # Guardar estado temporal
                estados_conversacion['maquinas_lista'] = maquinas_nuevas
                estados_conversacion['paso'] = 'seleccionar_maquina'

                return respuesta

        # Manejar respuestas de configuración (cuando hay estado activo)
        elif 'usuario_actual' in estados_conversacion:
            estado = estados_conversacion['usuario_actual']
            if estado.paso_actual == "esperando_nombre":
                # El usuario está respondiendo con el nombre de la máquina
                vm_id = pregunta.strip()

                # Configurar el power Virsh con el nombre proporcionado
                resultado_power = await configurar_power_virsh(estado.system_id, vm_id)

                # Limpiar estado
                del estados_conversacion['usuario_actual']
                return (
                    f"✅ **CONFIGURACIÓN COMPLETADA**\n\n"
                    f"**Máquina:** {estado.hostname_maas}\n"
                    f"**IP:** {estado.ip_maquina}\n"
                    f"**VM ID asignado:** {vm_id}\n\n"
                    f"{resultado_power}\n\n"
                    f"💡 *Ahora puedes realizar el commissioning manual cuando lo necesites*"
                )

        # Manejar selección de maquina de la lista
        elif 'maquinas_lista' in estados_conversacion and estados_conversacion.get('paso') == 'seleccionar_maquina':
            try:
                numero = int(pregunta.strip())
                maquinas_lista = estados_conversacion['maquinas_lista']

                if 1 <= numero <= len(maquinas_lista):
                    maquina = maquinas_lista[numero - 1]

                    # Iniciar configuración para esta máquina
                    estados_conversacion['usuario_actual'] = EstadoConfiguracion(
                        maquina['system_id'],
                        maquina['hostname'],
                        maquina['ip']
                    )

                    # Limpiar estado temporal
                    del estados_conversacion['maquinas_lista']
                    del estados_conversacion['paso']

                    return (
                        f"⚙️ **CONFIGURAR MÁQUINA NUEVA**\n\n"
                        f"**Información de la máquina:**\n"
                        f"**Hostname MAAS:** {maquina['hostname']}\n"
                        f"**IP:** {maquina['ip']}\n"
                        f"**ID:** {maquina['system_id']}\n\n"
                        f"**¿Cómo se llama esta máquina en Virsh?**\n"
                        f"**Responde con el VM ID exacto (ej: maq2, servidor-web, etc.)**"
                    )

                else:
                    return f"❌ Número inválido. Por favor, elige un número entre 1 y {len(maquinas_lista)}."

            except ValueError:
                return "❌ Por favor, responde con un número válido."

        # Consulta de subredes:
        elif 'subred' in pregunta_lower or "subredes" in pregunta_lower:
            subredes_texto = await listar_subredes()
            prompt = f"""
INFORMACIÓN DE SUBREDES EN MAAS:
{subredes_texto}

PREGUNTA DEL USUARIO: {pregunta}

INSTRUCCIONES:
- Responde en español de forma clara y organizada.
- Usa emojis para hacerlo visual.
- Agrupa la información de forma lógica.
- Destaca los datos más importantes.
- Formato: título, luego lista de subredes con sus características.
- Responde:
"""
            return await generar_respuesta_gemini(prompt)

        # Consulta de máquinas (consultas informativas):
        maquinas_texto = await listar_maquinas()

        # DETECTAR TIPO DE PREGUNTA PARA ADAPTAR LA RESPUESTA:
        if any(palabra in pregunta_lower for palabra in ['cuántas', 'cuantas', 'número', 'numero', 'total', 'cuantos']):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Analiza cuántas máquinas hay en total.
- Cuenta cuántas están encendidas y cuántas apagadas.
- Proporciona estadísticas claras.
- Usa formato visual con emojis.
- Incluye detalles interesantes sobre el estado general.

EJEMPLO DE FORMATO:
**Resumen del Sistema**
**Total de máquinas**: X
**Encendidas**: Y
**Apagadas**: Z
**Porcentaje activas**: W%

**Lista de máquinas**: [Breve lista con nombres y estados]

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        elif any(palabra in pregunta_lower for palabra in ['ram', "memoria"]):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre la memoria RAM.
- Organiza la información de forma clara.
- Si hay máquinas específicas mencionadas, enfócate en ellas.
- Usa emojis y formato visual.
- Incluye totales si es relevante.

Formato sugerido:
**Información de Memoria RAM**

**Total de RAM en el sistema**: X GB

**Por máquina**:
[Máquina1]: [RAM] GB
[Máquina2]: [RAM] GB

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        elif any(palabra in pregunta_lower for palabra in ['almacenamiento', 'disco', 'disco duro', 'storage', 'gb']):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre el almacenamiento.
- Organiza la información de forma clara.
- Usa emojis y formato visual.
- Incluye totales si es relevante.

Formato sugerido:
**Información de Almacenamiento**
**Total de almacenamiento**: X GB

**Por máquina**:
[Máquina1]: [Almacenamiento] GB
[Máquina2]: [Almacenamiento] GB

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        elif any(palabra in pregunta_lower for palabra in ['cpu', 'procesador', 'núcleo', 'núcleos', 'procesadores']):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre los CPUs/procesadores.
- Organiza la información de forma clara.
- Usa emojis y formato visual.
- Incluye totales si es relevante.

Formato sugerido:
**Información de Procesadores**
**Total de núcleos en el sistema**: X

**Por máquina**:
[Máquina1]: [CPUs] núcleos
[Máquina2]: [CPUs] núcleos

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        elif any(palabra in pregunta_lower for palabra in ['encend', 'apag', 'power', 'on', 'off', 'estado']):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre el estado de encendido/apagado.
- Organiza por estado (encendidas primero, luego apagadas).
- Usa emojis visuales (🟢 para encendidas, 🔴 para apagadas).
- Sé claro y conciso.

Formato sugerido:
**Estado de las Máquinas**
**Encendidas** (X):
[Máquina1] ([IP])
[Máquina2] ([IP])

**Apagadas** (Y):
[Máquina3] ([IP])
[Máquina4] ([IP])

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        elif any(palabra in pregunta_lower for palabra in ['ip', 'dirección', 'direccion', 'red', 'network']):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre las direcciones IP.
- Organiza la información de forma clara.
- Incluye el estado de cada máquina.

Formato sugerido:
**Direcciones IP del Sistema**

**Máquinas y sus IPs**
[Máquina1]: [IP]
[Máquina2]: [IP]
[Máquina3]: [IP]

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        elif any(palabra in pregunta_lower for palabra in ['información', 'info', 'detalles', 'resumen', 'todo', 'general']):
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Proporciona un resumen COMPLETO pero BIEN ESTRUCTURADO de todas las máquinas.
- Agrupa por estado (encendidas primero).
- Para CADA máquina, incluye: estado, IP, RAM, almacenamiento, CPUs y SO.
- Usa un formato CLARO y ORGANIZADO con emojis.
- Separa cada máquina con una línea en blanco.
- Mantén la información CONCISA pero COMPLETA.
- Usa los valores EXACTOS de la información proporcionada.

EJEMPLO DE FORMATO CORRECTO:
**Resumen del Sistema MAAS**

**MÁQUINA: maquinaprueba** (ID: 7mdht4)
IP: 172.16.25.201
RAM: 2 GB | Almacenamiento: 21.0 GB | CPUs: 1 núcleo
SO: ubuntu jammy
Zona: default | Pool: default

**MÁQUINA: maq2** (ID: abc123)
IP: 172.16.25.202
RAM: 4 GB | Almacenamiento: 50.0 GB | CPUs: 2 núcleos
SO: ubuntu focal
Zona: default | Pool: default

**Estadísticas**:
Total: 2 máquinas
Encendidas: 1
Apagadas: 1

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

        else:
            # Pregunta general - usar Gemini para análisis contextual
            prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Analiza qué información es RELEVANTE para responder esta pregunta específica.
- Responde de forma AMIGABLE y ÚTIL.
- Usa emojis para hacer la respuesta más atractiva.
- Si la pregunta es sobre un aspecto concreto, habla solo de ese aspecto.
- Si es una pregunta general, da un resumen breve pero completo.
- Si no hay información relevante, sugiere qué tipo de preguntas puedo responder.
- Sé conversacional pero profesional.

Responde en español:
"""
            return await generar_respuesta_gemini(prompt)

    except Exception as e:
        print(f"Error en responder_pregunta: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo.\n\n Detalle: {str(e)}"