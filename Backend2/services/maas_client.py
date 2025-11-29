import asyncio
from datetime import datetime
from maas.client import connect
import re
import threading

from config import MAAS_URL, MAAS_API_KEY
from services.telegram_service import enviar_notificacion_telegram
from utils.helpers import serializar_objeto_simple

#========================================================
# Funciones básicas de MAAS
#========================================================

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
            encendido = "🟡 DESCONOCIDO"

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
            f"🖥️ MÁQUINA: {hostname} ({system_id})\n"
            f"📊 Estado MAAS: {status_name}\n"
            f"⚡ Estado: {encendido}\n"
            f"🌐 IP: {ip_principal}\n"
            f"💾 RAM: {ram_gb} GB\n"
            f"💿 Almacenamiento: {storage_gb} GB\n"
            f"🔢 CPUs: {cpu_count} núcleos\n"
            f"🖥️ SO: {osystem} {distro_series}\n"
            f"📍 Zona: {zone_name} | Pool: {pool_name}\n\n"
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
        lista_texto += f"🌐 Subred: {name}, CIDR: {cidr}, VLAN: {vlan}\n"
    return lista_texto

#===================================================
# Control de máquinas
#===================================================

async def encender_maquina(identificador):
    """Enciende una máquina por hostname o system_id"""
    print(f"DEBUG [encender_maquina]: Iniciando para identificador: {identificador}")

    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquinas = await client.machines.list()

        maquina_encontrada = None
        for m in maquinas:
            m_full = await client.machines.get(m.system_id)
            if (m_full.hostname.lower() == identificador.lower() or m_full.system_id.lower() == identificador.lower()):
                maquina_encontrada = m_full
                break

        if not maquina_encontrada:
            print(f"DEBUG [encender_maquina]: Máquina no encontrada: {identificador}")
            mensaje_error = f"<b>Error en comando</b>\n❌ <b>Máquina no encontrada:</b> {identificador}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
            return f"❌ No se encontró la máquina: {identificador}"

        # Verificar estado actual
        power_state = maquina_encontrada._data.get("power_state", "unknown")
        print(f"DEBUG [encender_maquina]: Estado actual de {maquina_encontrada.hostname}: {power_state}")

        if power_state == "on":
            print(f"DEBUG [encender_maquina]: La máquina ya está encendida")
            return f"ℹ️ La máquina {maquina_encontrada.hostname} ya está encendida"

        # Notificación de inicio de comando
        ip_maquina = maquina_encontrada.ip_addresses[0] if maquina_encontrada.ip_addresses else "Sin IP"
        mensaje_inicio = f"<b>Comando ejecutado</b>\n🔧 <b>Encendiendo:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_inicio)).start()

        print(f"DEBUG [encender_maquina]: Enviando comando power_on a MAAS")
        # Encender la máquina
        await maquina_encontrada.power_on()
        await asyncio.sleep(5)

        # Verificar nuevo estado
        print(f"DEBUG [encender_maquina]: Verificando nuevo estado")
        maquina_actualizada = await client.machines.get(maquina_encontrada.system_id)
        nuevo_estado = maquina_actualizada._data.get("power_state", "unknown")

        print(f"DEBUG [encender_maquina]: Nuevo estado: {nuevo_estado}")
        if nuevo_estado == "on":
            mensaje_exito = f"<b>Comando completado</b>\n✅ <b>Máquina encendida:</b> {maquina_encontrada.hostname}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_exito)).start()
            return f"✅ Máquina {maquina_encontrada.hostname} encendida exitosamente"
        else:
            return f"🟡 La máquina {maquina_encontrada.hostname} se está encendiendo (puede tardar unos momentos)"

    except Exception as e:
        print(f"DEBUG [encender_maquina]: Error: {e}")
        import traceback
        traceback.print_exc()
        mensaje_error = f"<b>Error en comando</b>\n❌ <b>Error al encender:</b> {identificador}\n📝 {str(e)}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
        return f"❌ Error al encender la máquina: {e}"

async def apagar_maquina(identificador):
    """Apaga una máquina por hostname o system_id"""
    print(f"DEBUG [apagar_maquina]: Iniciando para identificador: {identificador}")

    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquinas = await client.machines.list()

        maquina_encontrada = None
        for m in maquinas:
            m_full = await client.machines.get(m.system_id)
            if (m_full.hostname.lower() == identificador.lower() or m_full.system_id.lower() == identificador.lower()):
                maquina_encontrada = m_full
                break

        if not maquina_encontrada:
            print(f"DEBUG [apagar_maquina]: Máquina no encontrada: {identificador}")
            mensaje_error = f"<b>Error en comando</b>\n❌ <b>Máquina no encontrada:</b> {identificador}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_error)).start()
            return f"❌ No se encontró la máquina: {identificador}"

        # Verificar estado actual
        power_state = maquina_encontrada._data.get("power_state", "unknown")
        print(f"DEBUG [apagar_maquina]: Estado actual de {maquina_encontrada.hostname}: {power_state}")

        if power_state == "off":
            print(f"DEBUG [apagar_maquina]: La máquina ya está apagada")
            return f"ℹ️ La máquina {maquina_encontrada.hostname} ya está apagada"

        # Notificación de inicio de comando
        ip_maquina = maquina_encontrada.ip_addresses[0] if maquina_encontrada.ip_addresses else "Sin IP"
        mensaje_inicio = f"<b>Comando ejecutado</b>\n🔧 <b>Apagando:</b> {maquina_encontrada.hostname} ({ip_maquina})\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_inicio)).start()

        print(f"DEBUG [apagar_maquina]: Enviando comando power_off a MAAS")
        # Apagar la máquina
        await maquina_encontrada.power_off()
        await asyncio.sleep(5)

        # Verificar nuevo estado
        print(f"DEBUG [apagar_maquina]: Verificando nuevo estado")
        maquina_actualizada = await client.machines.get(maquina_encontrada.system_id)
        nuevo_estado = maquina_actualizada._data.get("power_state", "unknown")

        print(f"DEBUG [apagar_maquina]: Nuevo estado: {nuevo_estado}")
        if nuevo_estado == "off":
            mensaje_exito = f"<b>Comando completado</b>\n✅ <b>Máquina apagada:</b> {maquina_encontrada.hostname}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            threading.Thread(target=lambda: enviar_notificacion_telegram(mensaje_exito)).start()
            return f"✅ Máquina {maquina_encontrada.hostname} apagada exitosamente"
        else:
            return f"🟡 La máquina {maquina_encontrada.hostname} se está apagando (puede tardar unos momentos)"

    except Exception as e:
        print(f"DEBUG [apagar_maquina]: Error: {e}")
        import traceback
        traceback.print_exc()
        mensaje_error = f"<b>Error en comando</b>\n❌ <b>Error al apagar:</b> {identificador}\n📝 {str(e)}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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

#===================================================
# Funciones para Dashboard
#===================================================

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
                    "so": f"{m_full.osystem} {m_full.distro_series}" if m_full.osystem else "NO SO",
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
                    subnet_info['vlan'] = f"{vlan_name} (VID: {vlan_vid}, ID: {vlan_id})"
            except Exception as e:
                print(f"Error procesando VLAN: {e}")
                subnet_info['vlan'] = "Error al obtener VLAN"

            try:
                space_obj = getattr(subnet, "space", None)
                if space_obj:
                    space_name = str(getattr(space_obj, "name", "default"))
                    subnet_info['space'] = space_name
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

#===================================================
# Funciones para máquinas nuevas
#===================================================

async def obtener_maquinas_nuevas():
    """Detecta máquinas nuevas en estado 'New' que necesitan commissioning"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        machines = await client.machines.list()
        
        maquinas_nuevas = []
        for m in machines:
            m_full = await client.machines.get(m.system_id)
            # Máquinas en estado 'New' son las recién detectadas
            if m_full.status_name == "New":
                ip_principal = m_full.ip_addresses[0] if m_full.ip_addresses else "Sin IP"
                maquinas_nuevas.append({
                    "hostname": m_full.hostname,
                    "system_id": m_full.system_id,
                    "ip": ip_principal,
                    "status": m_full.status_name,
                    "timestamp": datetime.now().isoformat()
                })
        
        return maquinas_nuevas
    except Exception as e:
        print(f"Error detectando máquinas nuevas: {e}")
        return []

async def abortar_commissioning(system_id):
    """Solo aborta el commissioning automático SIN configurar power"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        print(f"🔧 Abortando commissioning para: {maquina.hostname} (Estado: {maquina.status_name})")
        
        resultado_abort = ""
        
        # Solo abortar commissioning, NO configurar power
        if maquina.status_name == "Commissioning":
            try:
                await maquina.abort()
                resultado_abort = f"✅ Commissioning abortado para {maquina.hostname}"
                print(resultado_abort)
            except Exception as abort_error:
                print(f"❌ Error con abort(): {abort_error}")
                try:
                    await maquina.power_off()
                    resultado_abort = f"✅ Máquina apagada para abortar commissioning: {maquina.hostname}"
                    print(resultado_abort)
                except Exception as power_error:
                    resultado_abort = f"❌ No se pudo abortar commissioning: {str(abort_error)}"
                    print(resultado_abort)
        elif maquina.status_name == "New":
            resultado_abort = f"ℹ️ Máquina {maquina.hostname} en estado New"
            print(resultado_abort)
        else:
            resultado_abort = f"ℹ️ La máquina {maquina.hostname} no está en commissioning. Estado: {maquina.status_name}"
            print(resultado_abort)
        
        return resultado_abort
            
    except Exception as e:
        print(f"❌ Error general al abortar commissioning: {e}")
        return f"❌ Error al abortar commissioning: {str(e)}"


async def configurar_power_virsh(system_id, vm_id):
    """Configura power Virsh y cambia el hostname al VM ID en MAAS 3.5.8"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        hostname_original = maquina.hostname
        print(f"🔌 Configurando power Virsh para: {hostname_original} -> VM ID: {vm_id}")
        
        # Parámetros para Virsh
        power_params = {
            "power_address": "qemu+ssh://branvictus@172.16.25.1/system",
            "power_id": vm_id
        }
        
        print(f"🔧 Estado actual - Power type: {maquina.power_type}")
        print(f"🔧 Estado actual - Hostname: {hostname_original}")
        
        resultados = []
        
        # PASO 1: Configurar power Virsh
        try:
            await maquina.set_power(
                power_type="virsh",
                power_parameters=power_params
            )
            resultados.append(f"✅ Power Virsh configurado con VM ID '{vm_id}'")
            print(f"✅ set_power ejecutado exitosamente")
        except Exception as e_power:
            resultados.append(f"❌ Error configurando power: {str(e_power)}")
            print(f"❌ Error en set_power: {e_power}")
        
        # PASO 2: Cambiar hostname al VM ID
        try:
            resultado_hostname = await cambiar_hostname_maas(system_id, vm_id)
            resultados.append(resultado_hostname)
        except Exception as e_hostname:
            resultados.append(f"❌ Error cambiando hostname: {str(e_hostname)}")
            print(f"❌ Error cambiando hostname: {e_hostname}")
        
        # Verificar configuración final
        maquina_actualizada = await client.machines.get(system_id)
        print(f"🔧 Configuración final - Power type: {maquina_actualizada.power_type}")
        print(f"🔧 Configuración final - Hostname: {maquina_actualizada.hostname}")
        
        # Combinar resultados
        if any("❌" in resultado for resultado in resultados):
            mensaje_final = "⚠️ Configuración parcial:\n" + "\n".join(resultados)
        else:
            mensaje_final = "✅ Configuración completada:\n" + "\n".join(resultados)
        
        return mensaje_final
            
    except Exception as e:
        print(f"❌ Error en configurar_power_virsh: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error en configuración: {str(e)}"

async def debug_maquina_detallado(system_id):
    """Debug detallado del objeto Machine en MAAS 3.5.8"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        print("=== DEBUG DETALLADO MAAS 3.5.8 ===")
        print(f"Hostname: {maquina.hostname}")
        print(f"System ID: {maquina.system_id}")
        print(f"Status: {maquina.status_name}")
        
        # Atributos comunes de power
        power_attrs = ['power_type', 'power_parameters', 'power_state']
        for attr in power_attrs:
            if hasattr(maquina, attr):
                value = getattr(maquina, attr)
                print(f"{attr}: {value}")
            else:
                print(f"{attr}: NO EXISTE")
        
        # Métodos disponibles
        methods = [m for m in dir(maquina) if not m.startswith('_') and callable(getattr(maquina, m))]
        print(f"Métodos disponibles: {methods}")
        
        # Métodos específicos de power
        power_methods = [m for m in methods if 'power' in m.lower()]
        print(f"Métodos de power: {power_methods}")
        
        # Métodos de guardado/actualización
        save_methods = [m for m in methods if any(x in m.lower() for x in ['save', 'update', 'edit', 'configure'])]
        print(f"Métodos de guardado: {save_methods}")
        
        return {
            "hostname": maquina.hostname,
            "power_attrs": {attr: getattr(maquina, attr, "NO EXISTE") for attr in power_attrs},
            "power_methods": power_methods,
            "save_methods": save_methods
        }
    except Exception as e:
        return {"error": str(e)}

async def listar_todas_maquinas_con_ids():
    """Lista todas las máquinas con sus system_ids para debugging"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        machines = await client.machines.list()
        
        maquinas_info = []
        for m in machines:
            m_full = await client.machines.get(m.system_id)
            maquinas_info.append({
                "hostname": m_full.hostname,
                "system_id": m_full.system_id,
                "status": m_full.status_name,
                "power_type": m_full.power_type,
                "ip": m_full.ip_addresses[0] if m_full.ip_addresses else "Sin IP"
            })
        
        return maquinas_info
    except Exception as e:
        print(f"Error listando máquinas: {e}")
        return []

async def debug_power_parameters(system_id):
    """Debug específico para parámetros de power"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        print("=== DEBUG POWER PARAMETERS ===")
        print(f"Hostname: {maquina.hostname}")
        print(f"Power type: {maquina.power_type}")
        print(f"Power state: {maquina.power_state}")
        
        # Obtener parámetros actuales
        try:
            params = await maquina.get_power_parameters()
            print(f"Power parameters: {params}")
        except Exception as e:
            print(f"Error obteniendo power parameters: {e}")
        
        return {
            "hostname": maquina.hostname,
            "power_type": maquina.power_type,
            "power_state": str(maquina.power_state),
            "power_parameters": params if 'params' in locals() else f"Error: {e}"
        }
    except Exception as e:
        return {"error": str(e)}

async def cambiar_hostname_maas(system_id, nuevo_hostname):
    """Cambia el hostname de una máquina en MAAS"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        print(f"🏷️ Cambiando hostname de '{maquina.hostname}' a '{nuevo_hostname}'")
        
        # En MAAS 3.5.8, podemos intentar varias formas de cambiar el hostname
        
        # Método 1: Asignación directa al atributo hostname + save()
        try:
            maquina.hostname = nuevo_hostname
            await maquina.save()
            print(f"✅ Hostname cambiado exitosamente a '{nuevo_hostname}'")
            return f"✅ Hostname cambiado a '{nuevo_hostname}'"
        except Exception as e1:
            print(f"❌ Método 1 falló: {e1}")
            
            # Método 2: Usar update si existe (aunque en el debug no vimos update, por si acaso)
            try:
                if hasattr(maquina, 'update'):
                    await maquina.update(hostname=nuevo_hostname)
                    print(f"✅ Hostname cambiado usando update()")
                    return f"✅ Hostname cambiado a '{nuevo_hostname}'"
            except Exception as e2:
                print(f"❌ Método 2 falló: {e2}")
                
                # Método 3: API REST directa
                try:
                    return await cambiar_hostname_api_directa(system_id, nuevo_hostname)
                except Exception as e3:
                    print(f"❌ Método 3 falló: {e3}")
                    raise Exception(f"Todos los métodos fallaron: {e1}, {e2}, {e3}")
                    
    except Exception as e:
        print(f"❌ Error cambiando hostname: {e}")
        return f"❌ Error cambiando hostname: {str(e)}"

async def cambiar_hostname_api_directa(system_id, nuevo_hostname):
    """Cambia el hostname usando la API REST directamente"""
    try:
        import aiohttp
        import json
        
        # URL de la API de MAAS
        url = f"{MAAS_URL}/api/2.0/machines/{system_id}/"
        
        # Headers con autenticación
        headers = {
            'Authorization': f'ApiKey {MAAS_API_KEY}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Datos para cambiar hostname
        form_data = aiohttp.FormData()
        form_data.add_field('hostname', nuevo_hostname)
        
        # Hacer la petición PUT
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, data=form_data) as response:
                if response.status == 200:
                    return f"✅ Hostname cambiado a '{nuevo_hostname}'"
                else:
                    error_text = await response.text()
                    return f"❌ Error en API: {response.status} - {error_text}"
                    
    except Exception as e:
        return f"❌ Error cambiando hostname via API: {str(e)}"

# Agregar estas funciones al archivo existente

async def listar_maquinas_para_commissioning():
    """Lista solo máquinas disponibles para commissioning (excluye deployed)"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        machines = await client.machines.list()
        
        maquinas_disponibles = []
        for maquina in machines:
            estado = getattr(maquina, 'status_name', f'Código: {maquina.status}')
            # Solo incluir máquinas que NO están en estado Deployed
            if estado != 'Deployed':
                ip_principal = maquina.ip_addresses[0] if maquina.ip_addresses else "Sin IP"
                maquinas_disponibles.append({
                    'hostname': maquina.hostname,
                    'system_id': maquina.system_id,
                    'status': estado,
                    'ip': ip_principal
                })
        
        return maquinas_disponibles
    except Exception as e:
        print(f"Error listando máquinas para commissioning: {e}")
        return []

async def ejecutar_commissioning(system_id, opciones=None):
    """Ejecuta commissioning en una máquina específica"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        # Configuración por defecto - SIN scripts específicos (usa los por defecto)
        opciones_default = {
            'enable_ssh': True,
            'skip_networking': False,
            'skip_storage': False,
            # No especificamos commissioning_scripts para usar los por defecto de MAAS
        }
        
        if opciones:
            opciones_default.update(opciones)
        
        # Verificar estado adecuado
        estado_actual = getattr(maquina, 'status_name', 'Desconocido')
        estados_validos = ['Ready', 'New', 'Failed commissioning']
        
        if estado_actual not in estados_validos:
            return {
                'success': False,
                'message': f'❌ La máquina no está en estado adecuado para commissioning. Estado actual: {estado_actual}',
                'estado_actual': estado_actual
            }
        
        # Ejecutar commissioning
        print(f"🔧 Ejecutando commissioning en {maquina.hostname} con opciones: {opciones_default}")
        resultado = await maquina.commission(**opciones_default)
        
        return {
            'success': True,
            'message': f'✅ Commissioning iniciado para {maquina.hostname}',
            'hostname': maquina.hostname,
            'system_id': system_id
        }
        
    except Exception as e:
        print(f"❌ Error en commissioning: {e}")
        return {
            'success': False,
            'message': f'❌ Error al iniciar commissioning: {str(e)}'
        }
async def obtener_estado_commissioning(system_id):
    """Obtiene el estado actual del commissioning de una máquina"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)
        
        return {
            'hostname': maquina.hostname,
            'system_id': system_id,
            'status': getattr(maquina, 'status_name', 'Desconocido'),
            'status_code': maquina.status
        }
    except Exception as e:
        return {
            'error': str(e)
        }

async def listar_maquinas_para_deploy():
    """Lista solo máquinas disponibles para deploy (estado Ready)"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        machines = await client.machines.list()
        maquinas_lista = []
        for maquina in machines:
            estado = getattr(maquina, 'status_name', f'Código: {maquina.status}')
            # Solo incluir máquinas en estado Ready para deploy
            if estado == 'Ready':
                ip_principal = maquina.ip_addresses[0] if maquina.ip_addresses else "Sin IP"
                maquinas_lista.append({
                    'hostname': maquina.hostname,
                    'system_id': maquina.system_id,
                    'status': estado,
                    'ip': ip_principal,
                    'osystem': getattr(maquina, 'osystem', 'No definido'),
                    'architecture': getattr(maquina, 'architecture', 'No definida'),
                    'memory_gb': round(getattr(maquina, 'memory', 0) / 1024, 1),
                    'cpu_count': getattr(maquina, 'cpu_count', 'N/A')
                })
        return maquinas_lista
    except Exception as e:
        print(f"Error listando máquinas para deploy: {e}")
        return []

async def ejecutar_deploy(system_id, opciones=None):
    """Ejecuta deploy en una máquina específica"""
    try:
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        maquina = await client.machines.get(system_id)

        # Verificar estado
        estado_actual = getattr(maquina, 'status_name', 'Desconocido')
        if estado_actual != 'Ready':
            return {
                'success': False,
                'message': f'❌ La máquina no está en estado Ready. Estado actual: {estado_actual}'
            }

        # Preparar parámetros básicos
        deploy_params = {
            'wait': False
        }

        # Agregar parámetros opcionales si se proporcionan
        if opciones:
            if 'user_data' in opciones:
                deploy_params['user_data'] = opciones['user_data']
            if 'distro_series' in opciones:
                deploy_params['distro_series'] = opciones['distro_series']
            if 'hwe_kernel' in opciones:
                deploy_params['hwe_kernel'] = opciones['hwe_kernel']

        # Ejecutar deploy con los parámetros disponibles
        resultado = await maquina.deploy(**deploy_params)

        return {
            'success': True,
            'message': f'✅ Deploy iniciado para {maquina.hostname}',
            'hostname': maquina.hostname,
            'system_id': system_id
        }

    except Exception as e:
        print(f"Error en deploy: {e}")
        return {
            'success': False,
            'message': f'❌ Error al iniciar deploy: {str(e)}'
        }