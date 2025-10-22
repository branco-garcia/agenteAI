import asyncio
from datetime import datetime
from maas.client import connect
import re
import threading

from config import MAAS_URL, MAAS_API_KEY
from services.telegram_service import enviar_notificacion_telegram
from utils.helpers import serializar_objeto_simple

# ==========================
# Funciones básicas de MAAS
# ==========================

async def obtener_maquinas():
    """Obtiene lista de todas las máquinas"""
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    return await client.machines.list()

async def obtener_estado_actual():
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

async def listar_maquinas():
    """Lista todas las máquinas en formato texto legible"""
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    machines = await client.machines.list()
    lista_texto = ""

    for m in machines:
        m_full = await client.machines.get(m.system_id)

        # INFORMACIÓN BÁSICA
        hostname = m_full.hostname
        system_id = m_full.system_id
        status_name = m_full.status_name
        
        # ESTADO DE ENCENDIDO
        power_state = m_full._data.get("power_state", "unknown")
        if power_state == "on":
            encendido = "🟢 ENCENDIDA"
        elif power_state == "off":
            encendido = "🔴 APAGADA"
        else:
            encendido = "⚫ DESCONOCIDO"
        
        # IP
        ip_principal = m_full.ip_addresses[0] if m_full.ip_addresses else "Sin IP"
        
        # HARDWARE
        memoria_mb = m_full._data.get("memory", 0)
        ram_gb = round(memoria_mb / 1024) if memoria_mb and memoria_mb > 0 else "Desconocida"
        
        storage_mb = m_full._data.get("storage", 0)
        storage_gb = round(storage_mb / 1024, 1) if storage_mb and storage_mb > 0 else "Desconocido"
        
        cpu_count = m_full._data.get("cpu_count", "Desconocido")
        
        # SISTEMA OPERATIVO
        osystem = m_full.osystem
        distro_series = m_full.distro_series
        
        # ZONA Y POOL
        zone_name = m_full.zone.name if m_full.zone else "default"
        pool_name = m_full.pool.name if m_full.pool else "default"

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
    """Obtiene lista de todas las subredes"""
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    return await client.subnets.list()

async def listar_subredes():
    """Lista todas las subredes en formato texto legible"""
    subnets = await obtener_subredes()
    lista_texto = ""
    for s in subnets:
        cidr = getattr(s, "cidr", "Desconocido")
        name = getattr(s, "name", "Sin nombre")
        vlan = getattr(s, "vlan", "No asignada")
        lista_texto += f"- Subred: {name}, CIDR: {cidr}, VLAN: {vlan}\n"
    return lista_texto

# ==========================
# Control de máquinas
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
        await asyncio.sleep(5)
        
        # Verificar nuevo estado
        maquina_actualizada = await client.machines.get(maquina_encontrada.system_id)
        nuevo_estado = maquina_actualizada._data.get("power_state", "unknown")
        
        if nuevo_estado == "on":
            mensaje_exito = f"🔔 <b>Comando completado</b>\n✅ <b>Máquina encendida:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_exito)).start()
            return f"✅ Máquina {maquina_encontrada.hostname} encendida exitosamente"
        else:
            return f"⚠️ La máquina {maquina_encontrada.hostname} se está encendiendo (puede tardar unos momentos)"
            
    except Exception as e:
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
        await asyncio.sleep(5)
        
        # Verificar nuevo estado
        maquina_actualizada = await client.machines.get(maquina_encontrada.system_id)
        nuevo_estado = maquina_actualizada._data.get("power_state", "unknown")
        
        if nuevo_estado == "off":
            mensaje_exito = f"🔔 <b>Comando completado</b>\n✅ <b>Máquina apagada:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_exito)).start()
            return f"✅ Máquina {maquina_encontrada.hostname} apagada exitosamente"
        else:
            return f"⚠️ La máquina {maquina_encontrada.hostname} se está apagando (puede tardar unos momentos)"
            
    except Exception as e:
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

async def buscar_maquina_por_nombre_o_id(identificador):
    """Busca una máquina por nombre o system_id"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquinas = await client.machines.list()
        
        for m in maquinas:
            m_full = await client.machines.get(m.system_id)
            if (m_full.hostname.lower() == identificador.lower() or 
                m_full.system_id.lower() == identificador.lower()):
                return m_full
        return None
    except Exception as e:
        print(f"Error buscando máquina: {e}")
        return None

# ==========================
# Funciones para Dashboard
# ==========================

async def obtener_metricas_dashboard():
    """Obtiene métricas completas para el dashboard"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        machines = await client.machines.list()
        
        metricas = {
            "resumen": await obtener_resumen_general(client, machines),
            "maquinas": await obtener_detalle_maquinas(client, machines),
            "red": await obtener_metricas_red(client),
            "alertas": await obtener_alertas_activas(client, machines),
            "rendimiento": await obtener_metricas_rendimiento(client, machines)
        }
        
        return serializar_objeto_simple(metricas)
        
    except Exception as e:
        print(f"Error obteniendo métricas del dashboard: {e}")
        return {
            "resumen": {},
            "maquinas": [],
            "red": {},
            "alertas": [],
            "rendimiento": {},
            "error": str(e)
        }

async def obtener_resumen_general(client, machines):
    """Obtiene resumen general del sistema"""
    try:
        total_maquinas = len(machines)
        maquinas_encendidas = 0
        maquinas_apagadas = 0
        total_ram = 0
        total_cpu = 0
        total_almacenamiento = 0
        
        for m in machines:
            m_full = await client.machines.get(m.system_id)
            power_state = m_full._data.get("power_state", "unknown")
            
            if power_state == "on":
                maquinas_encendidas += 1
            elif power_state == "off":
                maquinas_apagadas += 1
                
            # Recursos
            total_ram += m_full._data.get("memory", 0)
            total_cpu += m_full._data.get("cpu_count", 0)
            total_almacenamiento += m_full._data.get("storage", 0)
        
        return {
            "total_maquinas": total_maquinas,
            "maquinas_encendidas": maquinas_encendidas,
            "maquinas_apagadas": maquinas_apagadas,
            "maquinas_desconocidas": total_maquinas - maquinas_encendidas - maquinas_apagadas,
            "total_ram_gb": round(total_ram / 1024, 1),
            "total_cpu_cores": total_cpu,
            "total_almacenamiento_gb": round(total_almacenamiento / 1024, 1),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error en resumen general: {e}")
        return {}

async def obtener_detalle_maquinas(client, machines):
    """Obtiene detalle de todas las máquinas"""
    try:
        detalle_maquinas = []
        
        for m in machines:
            try:
                m_full = await client.machines.get(m.system_id)
                
                power_state = m_full._data.get("power_state", "unknown")
                status_name = m_full.status_name
                
                # Calcular estado de salud
                salud = "healthy"
                if status_name in ["Failed", "Error"]:
                    salud = "critical"
                elif status_name in ["Deploying", "Commissioning"]:
                    salud = "warning"
                elif power_state == "unknown":
                    salud = "unknown"
                
                # Extraer información de forma segura
                zona_info = "default"
                pool_info = "default"
                
                try:
                    if m_full.zone:
                        zona_info = getattr(m_full.zone, "name", "default")
                except:
                    pass
                    
                try:
                    if m_full.pool:
                        pool_info = getattr(m_full.pool, "name", "default")
                except:
                    pass
                
                # Obtener IP de forma segura
                ip_principal = "Sin IP"
                try:
                    if m_full.ip_addresses and len(m_full.ip_addresses) > 0:
                        ip_principal = m_full.ip_addresses[0]
                except:
                    pass
                
                detalle_maquinas.append({
                    "hostname": m_full.hostname,
                    "system_id": m_full.system_id,
                    "power_state": power_state,
                    "status": status_name,
                    "salud": salud,
                    "ip": ip_principal,
                    "ram_gb": round(m_full._data.get("memory", 0) / 1024) if m_full._data.get("memory") else 0,
                    "almacenamiento_gb": round(m_full._data.get("storage", 0) / 1024, 1) if m_full._data.get("storage") else 0,
                    "cpu_cores": m_full._data.get("cpu_count", 0),
                    "so": f"{m_full.osystem} {m_full.distro_series}" if m_full.osystem else "No SO",
                    "zona": zona_info,
                    "pool": pool_info,
                    "ultima_actualizacion": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"Error procesando máquina {m.system_id}: {e}")
                detalle_maquinas.append({
                    "hostname": f"Error-{m.system_id}",
                    "system_id": m.system_id,
                    "power_state": "unknown",
                    "status": "Error",
                    "salud": "critical",
                    "ip": "Error",
                    "ram_gb": 0,
                    "almacenamiento_gb": 0,
                    "cpu_cores": 0,
                    "so": "Error al cargar",
                    "zona": "default",
                    "pool": "default",
                    "ultima_actualizacion": datetime.now().isoformat(),
                    "error": str(e)
                })
        
        return detalle_maquinas
    except Exception as e:
        print(f"Error obteniendo detalle de máquinas: {e}")
        return []

async def obtener_metricas_red(client):
    """Obtiene métricas de red"""
    try:
        subnets = await client.subnets.list()
        
        metricas_red = {
            "total_subredes": len(subnets),
            "subredes": [],
            "ips_utilizadas": 0,
            "ips_disponibles": 0
        }
        
        for subnet in subnets:
            subnet_info = {
                "nombre": str(getattr(subnet, "name", "Sin nombre")),
                "cidr": str(getattr(subnet, "cidr", "Desconocido")),
                "vlan": "No asignada",
                "space": "default",
                "gateway": str(getattr(subnet, "gateway_ip", "No configurado"))
            }
            
            try:
                vlan_obj = getattr(subnet, "vlan", None)
                if vlan_obj:
                    vlan_id = str(getattr(vlan_obj, "id", "N/A"))
                    vlan_name = str(getattr(vlan_obj, "name", "Sin nombre"))
                    vlan_vid = str(getattr(vlan_obj, "vid", "N/A"))
                    
                    subnet_info["vlan"] = f"{vlan_name} (VID: {vlan_vid}, ID: {vlan_id})"
            except Exception as e:
                print(f"Error procesando VLAN: {e}")
                subnet_info["vlan"] = "Error al obtener VLAN"
            
            try:
                space_obj = getattr(subnet, "space", None)
                if space_obj:
                    space_name = str(getattr(space_obj, "name", "default"))
                    subnet_info["space"] = space_name
            except Exception as e:
                print(f"Error procesando space: {e}")
            
            metricas_red["subredes"].append(subnet_info)
        
        return metricas_red
    except Exception as e:
        print(f"Error obteniendo métricas de red: {e}")
        return {
            "total_subredes": 0,
            "subredes": [],
            "ips_utilizadas": 0,
            "ips_disponibles": 0,
            "error": str(e)
        }

async def obtener_alertas_activas(client, machines):
    """Identifica alertas activas en el sistema"""
    try:
        alertas = []
        
        for m in machines:
            m_full = await client.machines.get(m.system_id)
            status_name = m_full.status_name
            power_state = m_full._data.get("power_state", "unknown")
            
            if status_name == "Failed":
                alertas.append({
                    "tipo": "critical",
                    "maquina": m_full.hostname,
                    "mensaje": "Máquina en estado Failed",
                    "timestamp": datetime.now().isoformat()
                })
            elif status_name == "Error":
                alertas.append({
                    "tipo": "critical", 
                    "maquina": m_full.hostname,
                    "mensaje": "Máquina en estado Error",
                    "timestamp": datetime.now().isoformat()
                })
            elif power_state == "unknown":
                alertas.append({
                    "tipo": "warning",
                    "maquina": m_full.hostname,
                    "mensaje": "Estado de energía desconocido",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alertas
    except Exception as e:
        print(f"Error obteniendo alertas: {e}")
        return []

async def obtener_metricas_rendimiento(client, machines):
    """Obtiene métricas de rendimiento"""
    try:
        maquinas_encendidas = 0
        for m in machines:
            m_full = await client.machines.get(m.system_id)
            if m_full._data.get("power_state") == "on":
                maquinas_encendidas += 1
        
        return {
            "uso_cpu_promedio": 0,
            "uso_memoria_promedio": 0,
            "io_disponible": "Normal",
            "latencia_red": "Baja",
            "maquinas_activas": maquinas_encendidas
        }
    except Exception as e:
        print(f"Error obteniendo métricas de rendimiento: {e}")
        return {}

# ==========================
# Funciones de utilidad para búsqueda
# ==========================

def extraer_identificador_maquina(pregunta, maquinas_texto):
    """Extrae el identificador de máquina de una pregunta"""
    pregunta_lower = pregunta.lower()
    identificador = None
    
    # Buscar por nombre de máquina
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
            return ips[0]
    
    return identificador