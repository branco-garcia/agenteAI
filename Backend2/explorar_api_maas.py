#!/usr/bin/env python3

import asyncio
from maas.client import connect
from config import MAAS_URL, MAAS_API_KEY

async def listar_maquinas_ready():
    """Lista solo las máquinas en estado Ready para deploy"""
    client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
    machines = await client.machines.list()
    
    print("\n" + "="*80)
    print("🚀 MÁQUINAS LISTAS PARA DEPLOY (Estado: Ready)")
    print("="*80)
    
    maquinas_ready = []
    
    for i, maquina in enumerate(machines, 1):
        estado = getattr(maquina, 'status_name', f'Código: {maquina.status}')
        
        # Solo incluir máquinas en estado Ready
        if estado == 'Ready':
            # Obtener información adicional útil para deploy
            sistema_operativo = getattr(maquina, 'osystem', 'No definido')
            arquitectura = getattr(maquina, 'architecture', 'No definida')
            
            print(f"{i}. {maquina.hostname} | SO: {sistema_operativo} | Arquitectura: {arquitectura} | ID: {maquina.system_id}")
            maquinas_ready.append(maquina)
    
    return maquinas_ready

async def hacer_deploy(maquina):
    """Ejecuta deploy en la máquina seleccionada"""
    print(f"\n🎯 Preparando deploy en: {maquina.hostname}")
    print(f"📊 Estado actual: {getattr(maquina, 'status_name', 'Desconocido')}")
    
    try:
        # Verificar si la máquina está en estado Ready
        estado_actual = getattr(maquina, 'status_name', 'Desconocido')
        
        if estado_actual != 'Ready':
            print(f"❌ La máquina no está en estado Ready para deploy")
            print(f"💡 Estado actual: {estado_actual}")
            print(f"💡 Estado requerido: Ready")
            return
        
        # Mostrar información de la máquina
        sistema_operativo = getattr(maquina, 'osystem', 'No definido')
        arquitectura = getattr(maquina, 'architecture', 'No definida')
        memoria = getattr(maquina, 'memory', 0) / 1024  # Convertir a GB
        
        print(f"\n📋 Información de la máquina:")
        print(f"   • Hostname: {maquina.hostname}")
        print(f"   • Sistema Operativo: {sistema_operativo}")
        print(f"   • Arquitectura: {arquitectura}")
        print(f"   • Memoria: {memoria:.1f} GB")
        print(f"   • CPU: {getattr(maquina, 'cpu_count', 'N/A')} cores")
        
        # Confirmar deploy
        print(f"\n⚠️  ¿Estás seguro de hacer DEPLOY en {maquina.hostname}?")
        confirmar = input("   (s/n): ").lower().strip()
        
        if confirmar != 's':
            print("❌ Deploy cancelado")
            return
        
        # Configurar opciones de deploy
        print("\n🔧 Opciones de deploy:")
        print("1. Deploy estándar")
        print("2. Deploy con usuario SSH")
        print("3. Deploy personalizado")
        
        opcion = input("   Elige opción (1-3, Enter=1): ").strip() or "1"
        
        if opcion == "1":
            # Deploy estándar
            resultado = await maquina.deploy(wait=False)
        elif opcion == "2":
            # Deploy con usuario SSH
            usuario_ssh = input("   Usuario SSH: ").strip()
            if not usuario_ssh:
                usuario_ssh = "ubuntu"  # Default
            
            resultado = await maquina.deploy(
                user_data=None,
                distro_series=None,
                hwe_kernel=None,
                wait=False,
                install_rackd=False
            )
        elif opcion == "3":
            # Deploy personalizado
            usuario_ssh = input("   Usuario SSH (Enter para default 'ubuntu'): ").strip() or "ubuntu"
            serie_distro = input("   Serie distro (Ej: focal, jammy - Enter para default): ").strip() or None
            kernel = input("   Kernel HWE (Ej: hwe-22.04 - Enter para default): ").strip() or None
            
            resultado = await maquina.deploy(
                user_data=None,
                distro_series=serie_distro,
                hwe_kernel=kernel,
                wait=False,
                install_rackd=False
            )
        else:
            print("❌ Opción no válida")
            return
        
        print("✅ Deploy iniciado correctamente")
        
        # Monitorear progreso
        print("\n⏳ Monitoreando progreso del deploy...")
        client = await connect(MAAS_URL, apikey=MAAS_API_KEY)
        
        for i in range(60):  # 10 minutos máximo (deploy suele tomar más tiempo)
            await asyncio.sleep(10)
            maquina_actualizada = await client.machines.get(maquina.system_id)
            estado_actual = getattr(maquina_actualizada, 'status_name', f'Código: {maquina_actualizada.status}')
            print(f"   [{i+1}/60] Estado: {estado_actual}")
            
            # Estados finales
            if estado_actual in ['Deployed', 'Failed', 'Broken']:
                if estado_actual == 'Deployed':
                    print("🎉 DEPLOY COMPLETADO EXITOSAMENTE!")
                    # Obtener IP si está disponible
                    direcciones_ip = getattr(maquina_actualizada, 'ip_addresses', [])
                    if direcciones_ip:
                        print(f"🌐 Dirección IP: {', '.join(direcciones_ip)}")
                else:
                    print(f"⚠️ Deploy terminó con estado: {estado_actual}")
                break
            
            # Si sigue en deploy
            if estado_actual in ['Deploying', 'Allocating']:
                continue
                
        else:
            print("⏰ Deploy aún en progreso después de 10 minutos")
            
    except Exception as e:
        print(f"❌ Error durante deploy: {e}")

async def main():
    """Función principal - Menú interactivo para deploy"""
    try:
        print("🚀 DEPLOY DE MÁQUINAS MAAS")
        print("="*80)
        
        while True:
            # Listar solo máquinas en estado Ready
            maquinas = await listar_maquinas_ready()
            
            if not maquinas:
                print("❌ No hay máquinas disponibles para deploy")
                print("💡 Las máquinas deben estar en estado 'Ready'")
                return
            
            # Seleccionar máquina
            print("\n" + "-"*80)
            seleccion = input("👉 Elige una máquina (número) o 'q' para salir: ").strip()
            
            if seleccion.lower() == 'q':
                print("👋 ¡Hasta luego!")
                break
            
            try:
                indice = int(seleccion) - 1
                if 0 <= indice < len(maquinas):
                    maquina_seleccionada = maquinas[indice]
                    await hacer_deploy(maquina_seleccionada)
                else:
                    print("❌ Número de máquina no válido")
            except ValueError:
                print("❌ Entrada no válida. Ingresa un número.")
            
            # Preguntar si quiere continuar
            print("\n" + "-"*80)
            continuar = input("¿Quieres elegir otra máquina? (s/n): ").lower().strip()
            if continuar != 's':
                print("👋 ¡Hasta luego!")
                break
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())