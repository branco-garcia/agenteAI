import asyncio
from datetime import datetime
from services.maas_client import obtener_estado_actual, obtener_maquinas_nuevas
from services.telegram_service import enviar_notificacion_telegram

class MonitorMaquinas:
    def __init__(self):
        self.estados_anteriores = {}
        self.maquinas_nuevas_detectadas = set()  # Para trackear máquinas nuevas ya notificadas
        self.monitoreo_activo = False
        self.intervalo = 30
    
    def detectar_cambios(self, estados_actuales):
        cambios = []
        
        for hostname, estado_actual in estados_actuales.items():
            estado_anterior = self.estados_anteriores.get(hostname, {})
            
            if hostname not in self.estados_anteriores:
                cambios.append(f"🆕 <b>Nueva máquina detectada:</b> {hostname} ({estado_actual['ip']}) - Estado: {estado_actual['power_state']}")
            else:
                if estado_anterior.get('power_state') != estado_actual['power_state']:
                    if estado_actual['power_state'] == 'on':
                        cambios.append(f"🟢 <b>Máquina encendida:</b> {hostname} ({estado_actual['ip']})")
                    elif estado_actual['power_state'] == 'off':
                        cambios.append(f"🔴 <b>Máquina apagada:</b> {hostname} ({estado_actual['ip']})")
                    else:
                        cambios.append(f"🟡 <b>Estado cambiado:</b> {hostname} ({estado_actual['ip']}) - Nuevo estado: {estado_actual['power_state']}")
        
        for hostname in self.estados_anteriores:
            if hostname not in estados_actuales:
                cambios.append(f"❌ <b>Máquina desaparecida:</b> {hostname}")
        
        return cambios
    
    async def verificar_maquinas_nuevas(self):
        """Verifica y notifica sobre máquinas nuevas, abortando commissioning automático"""
        try:
            maquinas_nuevas = await obtener_maquinas_nuevas()
            
            for maquina in maquinas_nuevas:
                maquina_id = maquina['system_id']
                
                # Si no hemos procesado esta máquina nueva aún
                if maquina_id not in self.maquinas_nuevas_detectadas:
                    
                    print(f"🆕 Máquina nueva detectada: {maquina['hostname']} (ID: {maquina_id})")
                    
                    # === ABORTAR COMMISSIONING AUTOMÁTICO ===
                    from services.maas_client import abortar_commissioning
                    resultado_abort = await abortar_commissioning(maquina_id)
                    
                    # Construir mensaje de notificación
                    mensaje = (
                        f"🆕 <b>NUEVA MÁQUINA DETECTADA</b>\n\n"
                        f"🔧 <b>Nombre MAAS:</b> {maquina['hostname']}\n"
                        f"🌐 <b>IP:</b> {maquina['ip']}\n"
                        f"🆔 <b>ID:</b> {maquina['system_id']}\n"
                        f"📊 <b>Estado:</b> {maquina['status']}\n\n"
                        f"🛑 <b>Acción realizada:</b> Commissioning automático abortado\n"
                        f"📝 <b>Resultado:</b> {resultado_abort}\n\n"
                        f"💬 <b>Para configurar el power Virsh:</b>\n"
                        f"Escribe en el chat: <code>configurar máquina</code>\n\n"
                        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    
                    # Enviar notificación por Telegram
                    if enviar_notificacion_telegram(mensaje):
                        print(f"✅ Notificación enviada: {maquina['hostname']}")
                        self.maquinas_nuevas_detectadas.add(maquina_id)
                    else:
                        print(f"❌ Error enviando notificación: {maquina['hostname']}")
            
        except Exception as e:
            print(f"❌ Error en verificación de máquinas nuevas: {e}")
    
    async def verificar_estados(self):
        try:
            estados_actuales = await obtener_estado_actual()
            
            # Verificar máquinas nuevas primero
            await self.verificar_maquinas_nuevas()
            
            if self.estados_anteriores:
                cambios = self.detectar_cambios(estados_actuales)
                
                for cambio in cambios:
                    mensaje_completo = f"<b>🔔 Notificación MAAS</b>\n{cambio}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    if enviar_notificacion_telegram(mensaje_completo):
                        print(f"✅ Notificación enviada: {cambio}")
                    else:
                        print(f"❌ Error enviando notificación: {cambio}")
                    await asyncio.sleep(1)
            
            self.estados_anteriores = estados_actuales
            
        except Exception as e:
            print(f"❌ Error en verificación de estados: {e}")
    
    async def iniciar_monitoreo(self):
        self.monitoreo_activo = True
        print("🚀 Iniciando monitoreo de máquinas MAAS...")
        
        try:
            # Obtener estado inicial y máquinas nuevas
            self.estados_anteriores = await obtener_estado_actual()
            await self.verificar_maquinas_nuevas()  # Verificar máquinas nuevas al iniciar
            print(f"✅ Estado inicial capturado: {len(self.estados_anteriores)} máquinas")
        except Exception as e:
            print(f"❌ Error en verificación inicial: {e}")
        
        while self.monitoreo_activo:
            try:
                await self.verificar_estados()
                await asyncio.sleep(self.intervalo)
            except Exception as e:
                print(f"❌ Error en bucle de monitoreo: {e}")
                await asyncio.sleep(self.intervalo)
    
    def detener_monitoreo(self):
        self.monitoreo_activo = False
        print("🛑 Monitoreo detenido")