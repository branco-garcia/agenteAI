import asyncio
from datetime import datetime
from services.maas_client import obtener_estado_actual
from services.telegram_service import enviar_notificacion_telegram

class MonitorMaquinas:
    def __init__(self):
        self.estados_anteriores = {}
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
                        cambios.append(f"⚫ <b>Estado cambiado:</b> {hostname} ({estado_actual['ip']}) - Nuevo estado: {estado_actual['power_state']}")
        
        for hostname in self.estados_anteriores:
            if hostname not in estados_actuales:
                cambios.append(f"❌ <b>Máquina desaparecida:</b> {hostname}")
        
        return cambios
    
    async def verificar_estados(self):
        try:
            estados_actuales = await obtener_estado_actual()
            
            if self.estados_anteriores:
                cambios = self.detectar_cambios(estados_actuales)
                
                for cambio in cambios:
                    mensaje_completo = f"🔔 <b>Notificación MAAS</b>\n{cambio}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    if enviar_notificacion_telegram(mensaje_completo):
                        print(f"Notificación enviada: {cambio}")
                    else:
                        print(f"Error enviando notificación: {cambio}")
                    await asyncio.sleep(1)
            
            self.estados_anteriores = estados_actuales
            
        except Exception as e:
            print(f"Error en verificación de estados: {e}")
    
    async def iniciar_monitoreo(self):
        self.monitoreo_activo = True
        print("🔍 Iniciando monitoreo de máquinas MAAS...")
        
        try:
            self.estados_anteriores = await obtener_estado_actual()
            print(f"📊 Estado inicial capturado: {len(self.estados_anteriores)} máquinas")
        except Exception as e:
            print(f"Error en verificación inicial: {e}")
        
        while self.monitoreo_activo:
            try:
                await self.verificar_estados()
                await asyncio.sleep(self.intervalo)
            except Exception as e:
                print(f"Error en bucle de monitoreo: {e}")
                await asyncio.sleep(self.intervalo)
    
    def detener_monitoreo(self):
        self.monitoreo_activo = False
        print("⏹️ Monitoreo detenido")