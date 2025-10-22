import asyncio
import re
from config import CORTESIAS
from services.maas_client import listar_maquinas, listar_subredes, encender_maquina, apagar_maquina, buscar_maquina_por_ip
from services.gemini_service import generar_respuesta_gemini

async def responder_pregunta(pregunta):
    pregunta_lower = pregunta.lower()

    # Filtrar cortesías
    if any(c in pregunta_lower for c in CORTESIAS):
        return "¡De nada! 😊"

    # DETECTAR COMANDOS DE CONTROL DE MÁQUINAS
    # Comando para encender máquina
    if any(palabra in pregunta_lower for palabra in ["enciende", "encienda", "prende", "prenda", "power on", "encender"]):
        # Extraer el identificador de la máquina
        identificador = None
        
        # Buscar por nombre de máquina
        maquinas_texto = await listar_maquinas()
        for linea in maquinas_texto.split('\n'):
            if 'MÁQUINA:' in linea:
                partes = linea.split('(')
                if len(partes) > 1:
                    nombre_maquina = partes[0].replace('🔧 MÁQUINA:', '').strip()
                    system_id = partes[1].replace(')', '').strip()
                    
                    if nombre_maquina.lower() in pregunta_lower:
                        identificador = nombre_maquina
                        break
                    elif system_id.lower() in pregunta_lower:
                        identificador = system_id
                        break
        
        # Buscar por IP
        if not identificador:
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ips = re.findall(ip_pattern, pregunta)
            if ips:
                maquina_por_ip = await buscar_maquina_por_ip(ips[0])
                if maquina_por_ip:
                    identificador = maquina_por_ip.hostname
        
        if not identificador:
            # Si no se encontró identificador, pedir clarificación
            return "🤔 ¿Qué máquina quieres encender? Por favor, especifica el nombre o ID de la máquina."
        
        # Ejecutar comando de encender
        resultado = await encender_maquina(identificador)
        return resultado

    # Comando para apagar máquina
    elif any(palabra in pregunta_lower for palabra in ["apaga", "apague", "apagar", "power off", "apagado"]):
        # Extraer el identificador de la máquina
        identificador = None
        
        # Buscar por nombre de máquina
        maquinas_texto = await listar_maquinas()
        for linea in maquinas_texto.split('\n'):
            if 'MÁQUINA:' in linea:
                partes = linea.split('(')
                if len(partes) > 1:
                    nombre_maquina = partes[0].replace('🔧 MÁQUINA:', '').strip()
                    system_id = partes[1].replace(')', '').strip()
                    
                    if nombre_maquina.lower() in pregunta_lower:
                        identificador = nombre_maquina
                        break
                    elif system_id.lower() in pregunta_lower:
                        identificador = system_id
                        break
        
        # Buscar por IP
        if not identificador:
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ips = re.findall(ip_pattern, pregunta)
            if ips:
                maquina_por_ip = await buscar_maquina_por_ip(ips[0])
                if maquina_por_ip:
                    identificador = maquina_por_ip.hostname
        
        if not identificador:
            # Si no se encontró identificador, pedir clarificación
            return "🤔 ¿Qué máquina quieres apagar? Por favor, especifica el nombre o ID de la máquina."
        
        # Ejecutar comando de apagar
        resultado = await apagar_maquina(identificador)
        return resultado

    # Subredes
    if "subred" in pregunta_lower:
        subredes_texto = await listar_subredes()
        prompt = f"""
INFORMACIÓN DE SUBREDES EN MAAS:
{subredes_texto}

PREGUNTA DEL USUARIO: {pregunta}

Responde en español de forma clara y amigable, usando exactamente la información proporcionada.
"""
        return generar_respuesta_gemini(prompt)

    # Máquinas (consultas informativas)
    maquinas_texto = await listar_maquinas()
    
    # DETECTAR TIPO DE PREGUNTA PARA ADAPTAR LA RESPUESTA
    if any(palabra in pregunta_lower for palabra in ["ram", "memoria"]):
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre la memoria RAM
- No menciones información sobre almacenamiento, CPUs, estado de encendido, etc.
- Sé conciso y directo
- Usa los valores EXACTOS de la información proporcionada

Responde en español:
"""
    elif any(palabra in pregunta_lower for palabra in ["almacenamiento", "disco", "disco duro", "storage", "gb", "terabyte"]):
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre el almacenamiento
- No menciones información sobre RAM, CPUs, estado de encendido, etc.
- Sé conciso y directo
- Usa los valores EXACTOS de la información proporcionada

Responde en español:
"""
    elif any(palabra in pregunta_lower for palabra in ["cpu", "procesador", "núcleo", "nucleo", "procesadores"]):
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre los CPUs/procesadores
- No menciones información sobre RAM, almacenamiento, estado de encendido, etc.
- Sé conciso y directo
- Usa los valores EXACTOS de la información proporcionada

Responde en español:
"""
    elif any(palabra in pregunta_lower for palabra in ["encend", "apag", "power", "on", "off", "estado"]):
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre el estado de encendido/apagado
- No menciones información sobre RAM, almacenamiento, CPUs, etc.
- Usa los términos EXACTOS: 🟢 ENCENDIDA, 🔴 APAGADA, ⚫ DESCONOCIDO
- Sé conciso y directo

Responde en español:
"""
    elif any(palabra in pregunta_lower for palabra in ["ip", "dirección", "direccion", "red", "network"]):
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Responde ÚNICAMENTE sobre las direcciones IP
- No menciones información sobre RAM, almacenamiento, CPUs, estado de encendido, etc.
- Sé conciso y directo
- Usa los valores EXACTOS de la información proporcionada

Responde en español:
"""
    elif any(palabra in pregunta_lower for palabra in ["información", "info", "detalles", "resumen", "todo", "general", "máquinas", "maquinas"]):
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Proporciona un resumen COMPLETO pero BIEN ESTRUCTURADO de todas las máquinas
- Para CADA máquina, incluye: estado de encendido, IP, RAM, almacenamiento, CPUs y SO
- Usa un formato CLARO y ORGANIZADO
- Separa cada máquina con una línea en blanco
- Mantén la información CONCISA pero COMPLETA
- Usa los valores EXACTOS de la información proporcionada
- Incluye los emojis para hacerlo más visual

EJEMPLO DE FORMATO CORRECTO:
"🔧 MÁQUINA: maquinaprueba (7mdht4)
📍 Estado: 🟢 ENCENDIDA | 🌐 IP: 172.16.25.201
💾 RAM: 2 GB | 💿 Almacenamiento: 21.0 GB | 🔢 CPUs: 1 núcleo
🐧 SO: ubuntu jammy"

Responde en español:
"""
    else:
        prompt = f"""
INFORMACIÓN ACTUAL DE LAS MÁQUINAS EN MAAS:
{maquinas_texto}

PREGUNTA DEL USUARIO: "{pregunta}"

INSTRUCCIONES ESPECÍFICAS:
- Analiza qué información es RELEVANTE para responder esta pregunta específica
- Responde de forma CONCISA, mencionando solo la información necesaria
- Si la pregunta es sobre un aspecto concreto, habla solo de ese aspecto
- Si es una pregunta general, da un resumen breve pero completo
- Usa los valores EXACTOS de la información proporcionada
- No des información innecesaria o redundante

Responde en español:
"""

    return generar_respuesta_gemini(prompt)