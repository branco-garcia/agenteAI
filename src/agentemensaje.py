import google.generativeai as genai
import asyncio
from maas.client import connect
from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
from datetime import datetime

# ==========================
# Configuración
# ==========================
MAAS_URL = "http://172.16.25.2:5240/MAAS"
MAAS_API_KEY = "E9nebNWw3WhSejrkAL:Av2xxeCgHq2jeGL2rG:skcKZQp85vMdya2WubtERYXhMxf7pTty"
GEMINI_API_KEY = "AIzaSyCVmwiNmBqMaYQrvGDMBzPY_GJwrDNynt4"
TELEGRAM_BOT_TOKEN = "8436841267:AAF5oYG_FiKvDNi-vKGh_JjL4X_v3ReQUHo"  # Reemplaza con tu token
TELEGRAM_CHAT_ID = "5786912071"  # Reemplaza con tu chat ID

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

CORTESIAS = ["gracias", "muchas gracias", "ok gracias", "thank you", "ok", "perfecto"]

# ==========================
# Configuración de Telegram
# ==========================
def enviar_notificacion_telegram(mensaje):
    """Envía una notificación a Telegram"""
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Configuración de Telegram no completada")
            return False
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando notificación a Telegram: {e}")
        return False

# ==========================
# Monitor de estado de máquinas
# ==========================
class MonitorMaquinas:
    def __init__(self):
        self.estados_anteriores = {}
        self.monitoreo_activo = False
        self.intervalo = 30  # Segundos entre verificaciones
    
    async def obtener_estado_actual(self):
        """Obtiene el estado actual de todas las máquinas"""
        try:
            client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
            machines = await client.machines.list()
            estados_actuales = {}
            
            for m in machines:
                m_full = await client.machines.get(m.system_id)
                power_state = m_full._data.get("power_state", "unknown")
                estados_actuales[m_full.hostname] = {
                    "power_state": power_state,
                    "system_id": m_full.system_id,
                    "ip": m_full.ip_addresses[0] if m_full.ip_addresses else "Sin IP"
                }
            
            return estados_actuales
        except Exception as e:
            print(f"Error obteniendo estados: {e}")
            return {}
    
    def detectar_cambios(self, estados_actuales):
        """Detecta cambios en el estado de las máquinas"""
        cambios = []
        
        for hostname, estado_actual in estados_actuales.items():
            estado_anterior = self.estados_anteriores.get(hostname, {})
            
            # Si es la primera vez que vemos esta máquina
            if hostname not in self.estados_anteriores:
                cambios.append(f"🆕 <b>Nueva máquina detectada:</b> {hostname} ({estado_actual['ip']}) - Estado: {estado_actual['power_state']}")
            else:
                # Verificar cambio de estado
                if estado_anterior.get('power_state') != estado_actual['power_state']:
                    if estado_actual['power_state'] == 'on':
                        cambios.append(f"🟢 <b>Máquina encendida:</b> {hostname} ({estado_actual['ip']})")
                    elif estado_actual['power_state'] == 'off':
                        cambios.append(f"🔴 <b>Máquina apagada:</b> {hostname} ({estado_actual['ip']})")
                    else:
                        cambios.append(f"⚫ <b>Estado cambiado:</b> {hostname} ({estado_actual['ip']}) - Nuevo estado: {estado_actual['power_state']}")
        
        # Verificar máquinas desaparecidas
        for hostname in self.estados_anteriores:
            if hostname not in estados_actuales:
                cambios.append(f"❌ <b>Máquina desaparecida:</b> {hostname}")
        
        return cambios
    
    async def verificar_estados(self):
        """Verifica los estados y envía notificaciones si hay cambios"""
        try:
            estados_actuales = await self.obtener_estado_actual()
            
            if self.estados_anteriores:  # Solo notificar después de la primera verificación
                cambios = self.detectar_cambios(estados_actuales)
                
                for cambio in cambios:
                    mensaje_completo = f"🔔 <b>Notificación MAAS</b>\n{cambio}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    if enviar_notificacion_telegram(mensaje_completo):
                        print(f"Notificación enviada: {cambio}")
                    else:
                        print(f"Error enviando notificación: {cambio}")
                    await asyncio.sleep(1)  # Pequeña pausa entre notificaciones
            
            self.estados_anteriores = estados_actuales
            
        except Exception as e:
            print(f"Error en verificación de estados: {e}")
    
    async def iniciar_monitoreo(self):
        """Inicia el monitoreo continuo"""
        self.monitoreo_activo = True
        print("🔍 Iniciando monitoreo de máquinas MAAS...")
        
        # Primera verificación (sin notificaciones)
        try:
            self.estados_anteriores = await self.obtener_estado_actual()
            print(f"📊 Estado inicial capturado: {len(self.estados_anteriores)} máquinas")
        except Exception as e:
            print(f"Error en verificación inicial: {e}")
        
        # Bucle de monitoreo
        while self.monitoreo_activo:
            try:
                await self.verificar_estados()
                await asyncio.sleep(self.intervalo)
            except Exception as e:
                print(f"Error en bucle de monitoreo: {e}")
                await asyncio.sleep(self.intervalo)
    
    def detener_monitoreo(self):
        """Detiene el monitoreo"""
        self.monitoreo_activo = False
        print("⏹️ Monitoreo detenido")

# Instancia global del monitor
monitor = MonitorMaquinas()

# ==========================
# Funciones de MAAS CORREGIDAS (modificadas para notificaciones)
# ==========================
async def obtener_maquinas():
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    return await client.machines.list()

async def listar_maquinas():
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    machines = await client.machines.list()
    lista_texto = ""

    for m in machines:
        m_full = await client.machines.get(m.system_id)

        # INFORMACIÓN BÁSICA - desde atributos directos
        hostname = m_full.hostname
        system_id = m_full.system_id
        status_name = m_full.status_name
        
        # ESTADO DE ENCENDIDO - desde _data
        power_state = m_full._data.get("power_state", "unknown")
        if power_state == "on":
            encendido = "🟢 ENCENDIDA"
        elif power_state == "off":
            encendido = "🔴 APAGADA"
        else:
            encendido = "⚫ DESCONOCIDO"
        
        # IP - desde atributos directos
        ip_principal = m_full.ip_addresses[0] if m_full.ip_addresses else "Sin IP"
        
        # HARDWARE - desde _data
        memoria_mb = m_full._data.get("memory", 0)
        ram_gb = round(memoria_mb / 1024) if memoria_mb and memoria_mb > 0 else "Desconocida"
        
        storage_mb = m_full._data.get("storage", 0)
        storage_gb = round(storage_mb / 1024, 1) if storage_mb and storage_mb > 0 else "Desconocido"
        
        cpu_count = m_full._data.get("cpu_count", "Desconocido")
        
        # SISTEMA OPERATIVO - desde atributos directos
        osystem = m_full.osystem
        distro_series = m_full.distro_series
        
        # ZONA Y POOL - desde atributos directos
        zone_name = m_full.zone.name if m_full.zone else "default"
        pool_name = m_full.pool.name if m_full.pool else "default"

        # Estructura clara para Gemini
        lista_texto += (
            f"🔧 MÁQUINA: {hostname} ({system_id})\n"
            f"📍 Estado MAAS: {status_name}\n"
            f"⚡ Estado: {encendido}\n"
            f"🌐 IP: {ip_principal}\n"
            f"💾 RAM: {ram_gb} GB\n"
            f"💿 Almacenamiento: {storage_gb} GB\n"
            f"🔢 CPUs: {cpu_count} núcleos\n"
            f"🐧 SO: {osystem} {distro_series}\n"
            f"🏷️ Zona: {zone_name} | Pool: {pool_name}\n\n"
            f"────────────────────────────────────\n\n"
        )

    return lista_texto

async def obtener_subredes():
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    return await client.subnets.list()

async def listar_subredes():
    subnets = await obtener_subredes()
    lista_texto = ""
    for s in subnets:
        cidr = getattr(s, "cidr", "Desconocido")
        name = getattr(s, "name", "Sin nombre")
        vlan = getattr(s, "vlan", "No asignada")
        lista_texto += f"- Subred: {name}, CIDR: {cidr}, VLAN: {vlan}\n"
    return lista_texto

# ==========================
# NUEVAS FUNCIONES: ENCENDER Y APAGAR MÁQUINAS (modificadas para notificaciones)
# ==========================
async def encender_maquina(identificador):
    """Enciende una máquina por hostname o system_id"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquinas = await client.machines.list()
        
        maquina_encontrada = None
        for m in maquinas:
            m_full = await client.machines.get(m.system_id)
            if (m_full.hostname.lower() == identificador.lower() or 
                m_full.system_id.lower() == identificador.lower()):
                maquina_encontrada = m_full
                break
        
        if not maquina_encontrada:
            # Notificación de error
            mensaje_error = f"🔔 <b>Error en comando</b>\n❌ <b>Máquina no encontrada:</b> {identificador}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
            return f"❌ No se encontró la máquina: {identificador}"
        
        # Verificar estado actual
        power_state = maquina_encontrada._data.get("power_state", "unknown")
        if power_state == "on":
            return f"⚠️ La máquina {maquina_encontrada.hostname} ya está encendida"
        
        # Notificación de inicio de comando
        ip_maquina = maquina_encontrada.ip_addresses[0] if maquina_encontrada.ip_addresses else "Sin IP"
        mensaje_inicio = f"🔔 <b>Comando ejecutado</b>\n🟢 <b>Encendiendo:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_inicio)).start()
        
        # Encender la máquina
        await maquina_encontrada.power_on()
        await asyncio.sleep(5)  # Esperar más tiempo para cambios
        
        # Verificar nuevo estado
        maquina_actualizada = await client.machines.get(maquina_encontrada.system_id)
        nuevo_estado = maquina_actualizada._data.get("power_state", "unknown")
        
        if nuevo_estado == "on":
            # Notificación de éxito
            mensaje_exito = f"🔔 <b>Comando completado</b>\n✅ <b>Máquina encendida:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_exito)).start()
            return f"✅ Máquina {maquina_encontrada.hostname} encendida exitosamente"
        else:
            return f"⚠️ La máquina {maquina_encontrada.hostname} se está encendiendo (puede tardar unos momentos)"
            
    except Exception as e:
        # Notificación de error
        mensaje_error = f"🔔 <b>Error en comando</b>\n❌ <b>Error al encender:</b> {identificador}\n💬 {str(e)}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
        return f"❌ Error al encender la máquina: {e}"

async def apagar_maquina(identificador):
    """Apaga una máquina por hostname o system_id"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquinas = await client.machines.list()
        
        maquina_encontrada = None
        for m in maquinas:
            m_full = await client.machines.get(m.system_id)
            if (m_full.hostname.lower() == identificador.lower() or 
                m_full.system_id.lower() == identificador.lower()):
                maquina_encontrada = m_full
                break
        
        if not maquina_encontrada:
            # Notificación de error
            mensaje_error = f"🔔 <b>Error en comando</b>\n❌ <b>Máquina no encontrada:</b> {identificador}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
            return f"❌ No se encontró la máquina: {identificador}"
        
        # Verificar estado actual
        power_state = maquina_encontrada._data.get("power_state", "unknown")
        if power_state == "off":
            return f"⚠️ La máquina {maquina_encontrada.hostname} ya está apagada"
        
        # Notificación de inicio de comando
        ip_maquina = maquina_encontrada.ip_addresses[0] if maquina_encontrada.ip_addresses else "Sin IP"
        mensaje_inicio = f"🔔 <b>Comando ejecutado</b>\n🔴 <b>Apagando:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_inicio)).start()
        
        # Apagar la máquina
        await maquina_encontrada.power_off()
        await asyncio.sleep(5)  # Esperar más tiempo para cambios
        
        # Verificar nuevo estado
        maquina_actualizada = await client.machines.get(maquina_encontrada.system_id)
        nuevo_estado = maquina_actualizada._data.get("power_state", "unknown")
        
        if nuevo_estado == "off":
            # Notificación de éxito
            mensaje_exito = f"🔔 <b>Comando completado</b>\n✅ <b>Máquina apagada:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_exito)).start()
            return f"✅ Máquina {maquina_encontrada.hostname} apagada exitosamente"
        else:
            return f"⚠️ La máquina {maquina_encontrada.hostname} se está apagando (puede tardar unos momentos)"
            
    except Exception as e:
        # Notificación de error
        mensaje_error = f"🔔 <b>Error en comando</b>\n❌ <b>Error al apagar:</b> {identificador}\n💬 {str(e)}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
        return f"❌ Error al apagar la máquina: {e}"

async def buscar_maquina_por_ip(ip):
    """Busca una máquina por dirección IP"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquinas = await client.machines.list()
        
        for m in maquinas:
            m_full = await client.machines.get(m.system_id)
            if m_full.ip_addresses and ip in m_full.ip_addresses:
                return m_full
        return None
    except Exception as e:
        print(f"Error buscando máquina por IP: {e}")
        return None

# ==========================
# Funciones de Gemini
# ==========================
def generar_respuesta_gemini(prompt: str) -> str:
    try:
        respuesta = model.generate_content(prompt)
        return respuesta.text.strip()
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"

# ==========================
# Función de chat MEJORADA - con control de máquinas
# ==========================
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
            import re
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
            import re
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

# ==========================
# Servidor Flask con endpoints adicionales
# ==========================
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/preguntar", methods=["POST"])
def preguntar():
    try:
        pregunta = request.json.get("pregunta", "")
        if not pregunta.strip():
            return jsonify({"respuesta": "Por favor, ingresa una pregunta."})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        respuesta = loop.run_until_complete(responder_pregunta(pregunta))
        return jsonify({"respuesta": respuesta})
    except Exception as e:
        return jsonify({"respuesta": f"❌ Error procesando la pregunta: {e}"})

@app.route("/monitor/start", methods=["POST"])
def iniciar_monitor():
    """Endpoint para iniciar el monitoreo"""
    try:
        if not monitor.monitoreo_activo:
            threading.Thread(target=lambda: asyncio.run(monitor.iniciar_monitoreo()), daemon=True).start()
            return jsonify({"estado": "Monitoreo iniciado"})
        else:
            return jsonify({"estado": "El monitoreo ya está activo"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/monitor/stop", methods=["POST"])
def detener_monitor():
    """Endpoint para detener el monitoreo"""
    try:
        monitor.detener_monitoreo()
        return jsonify({"estado": "Monitoreo detenido"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/monitor/status", methods=["GET"])
def estado_monitor():
    """Endpoint para ver el estado del monitoreo"""
    return jsonify({
        "monitoreo_activo": monitor.monitoreo_activo,
        "maquinas_monitoreadas": len(monitor.estados_anteriores),
        "intervalo_segundos": monitor.intervalo
    })

# ==========================
# Inicialización al arrancar
# ==========================
def iniciar_aplicacion():
    """Función para iniciar el monitoreo automáticamente"""
    print("🚀 Iniciando aplicación MAAS Bot...")
    
    # Enviar notificación de inicio (opcional)
    mensaje_inicio = f"🔔 <b>MAAS Bot Iniciado</b>\n✅ Sistema de monitorización listo\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_inicio)).start()

# ==========================
# Ejecutar Flask
# ==========================
if __name__ == "__main__":
    # Iniciar aplicación
    iniciar_aplicacion()
    
    app.run(host="0.0.0.0", port=5000, debug=False)