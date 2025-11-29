import asyncio
import logging
import signal
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_BOT_TOKEN
from services.chat_service import responder_pregunta
from models.monitor import MonitorMaquinas

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotStandalone:
    def __init__(self):
        self.monitor = MonitorMaquinas()
        self.application = None

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Envía un mensaje cuando se emite el comando /start"""
        user = update.effective_user
        welcome_message = (
            f"🤖 ¡Hola {user.first_name}! Soy tu asistente MAAS Bot\n\n"
            "Puedo ayudarte a:\n"
            "• Consultar el estado de las máquinas\n"
            "• Encender y apagar máquinas\n"
            "• Monitorear cambios en el sistema\n"
            "• Consultar información de red\n\n"
            "Ejemplos de comandos:\n"
            "• '¿Qué máquinas están encendidas?'\n"
            "• 'Enciende la máquina X'\n"
            "• 'Apaga la máquina Y'\n"
            "• 'Muestra información de las subredes'\n\n"
            "Usa /monitor para controlar el monitoreo automático"
        )
        await update.message.reply_text(welcome_message)

    async def monitor_command(self, update: Update, context: CallbackContext) -> None:
        """Controla el monitoreo automático"""
        if not self.monitor.monitoreo_activo:
            # Iniciar monitoreo
            asyncio.create_task(self.monitor.iniciar_monitoreo())
            await update.message.reply_text(
                "🔔 Monitoreo iniciado. Recibirás notificaciones de cambios en las máquinas."
            )
        else:
            # Detener monitoreo
            self.monitor.detener_monitoreo()
            await update.message.reply_text("🔕 Monitoreo detenido.")

    async def status_command(self, update: Update, context: CallbackContext) -> None:
        """Muestra el estado actual del monitoreo"""
        status = "🟢 ACTIVO" if self.monitor.monitoreo_activo else "🔴 INACTIVO"
        maquinas_monitoreadas = len(self.monitor.estados_anteriores)
        
        status_message = (
            f"📊 Estado del Sistema:\n"
            f"Monitoreo: {status}\n"
            f"Máquinas monitoreadas: {maquinas_monitoreadas}\n"
            f"Intervalo: {self.monitor.intervalo} segundos"
        )
        await update.message.reply_text(status_message)

    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Procesa mensajes de texto usando la misma lógica del chat web"""
        user_message = update.message.text
        
        if not user_message.strip():
            await update.message.reply_text("Por favor, envía un mensaje válido.")
            return

        try:
            # Mostrar indicador de escritura
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            # Usar la misma función del chat web
            respuesta = await responder_pregunta(user_message)
            
            # Enviar respuesta
            await update.message.reply_text(respuesta, parse_mode='HTML')
            
        except Exception as e:
            error_message = f"❌ Error procesando tu mensaje: {str(e)}"
            await update.message.reply_text(error_message)
            logger.error(f"Error en Telegram bot: {e}")

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Muestra la ayuda"""
        help_text = (
            "🆘 Comandos disponibles:\n\n"
            "/start - Iniciar el bot\n"
            "/help - Mostrar esta ayuda\n"
            "/monitor - Iniciar/detener monitoreo automático\n"
            "/status - Estado del sistema\n\n"
            "💬 También puedes enviar mensajes como:\n"
            "• 'lista las máquinas'\n"
            "• 'enciende servidor01'\n"
            "• 'apaga 172.16.25.201'\n"
            "• 'muestra las subredes'\n"
            "• '¿cuánta RAM tiene la máquina X?'"
        )
        await update.message.reply_text(help_text)

    async def run_bot(self):
        """Inicia el bot de Telegram"""
        try:
            print("🤖 Iniciando bot de Telegram...")
            
            # Crear la aplicación
            self.application = (
                Application.builder()
                .token(TELEGRAM_BOT_TOKEN)
                .build()
            )
            
            # Añadir handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("monitor", self.monitor_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )
            
            print("✅ Bot de Telegram configurado correctamente")
            
            # Iniciar el bot
            await self.application.initialize()
            await self.application.start()
            print("🔄 Bot de Telegram iniciado, comenzando polling...")
            
            # Ejecutar polling
            await self.application.updater.start_polling()
            
            # Mantener el bot corriendo
            print("✅ Bot de Telegram está ahora activo y escuchando mensajes...")
            
            # Esperar indefinidamente
            await asyncio.Event().wait()
            
        except Exception as e:
            print(f"❌ Error en el bot de Telegram: {e}")
            raise

    async def stop_bot(self):
        """Detiene el bot de Telegram correctamente"""
        if self.application:
            print("🛑 Deteniendo bot de Telegram...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            print("✅ Bot de Telegram detenido correctamente")

def signal_handler(signum, frame):
    """Maneja señales de terminación"""
    print(f"\n🛑 Señal {signum} recibida, deteniendo bot...")
    sys.exit(0)

async def main():
    bot = TelegramBotStandalone()
    
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Interrupción por teclado recibida")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
    finally:
        await bot.stop_bot()

if __name__ == "__main__":
    # Ejecutar el bot
    asyncio.run(main())