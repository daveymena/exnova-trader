#!/usr/bin/env python3
"""
🤖 MONITOR DE BOT EN VIVO - Ejecutor Principal
Conecta a Exnova PRACTICE, ejecuta trades, aprende y mejora
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Setup
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

EMAIL = os.getenv('EXNOVA_EMAIL')
ACCOUNT_TYPE = os.getenv('ACCOUNT_TYPE', 'PRACTICE')
DATA_DIR = Path(__file__).parent / "data" / "live_sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MONITOR_LOG = DATA_DIR / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
SESSION_HISTORY = DATA_DIR / "session_history.json"


def log_message(msg: str, level: str = "INFO"):
    """Registra mensaje en log y consola"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {msg}"
    print(log_entry)
    with open(MONITOR_LOG, 'a') as f:
        f.write(log_entry + '\n')


def run_trading_bot():
    """Ejecuta el bot test_bot_final.py que funciona"""
    
    log_message("="*70)
    log_message("🚀 INICIANDO BOT DE TRADING EN VIVO")
    log_message(f"📧 Cuenta: {EMAIL}")
    log_message(f"💼 Modo: {ACCOUNT_TYPE}")
    log_message(f"🕐 Hora: {datetime.now()}")
    log_message("="*70)
    
    try:
        # Ejecutar bot
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "test_bot_final.py")],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(Path(__file__).parent)
        )
        
        log_message("✅ Bot completó ejecución")
        
        # Mostrar salida importante
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if any(keyword in line for keyword in ['✅', '❌', '💎', 'PnL', 'Win', 'ROI', 'Trade', 'OPORTUNIDAD']):
                print(line)
        
        return True
        
    except subprocess.TimeoutExpired:
        log_message("❌ Bot timeout", "ERROR")
        return False
    except Exception as e:
        log_message(f"❌ Error: {e}", "ERROR")
        return False


def run_headless_bot():
    """Ejecuta bot headless en modo continuo"""
    
    log_message("🚀 Iniciando BOT HEADLESS (modo continuo)")
    
    try:
        # Ejecutar bot headless
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).parent / "main_headless.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        log_message(f"✅ Bot ejecutándose con PID: {proc.pid}")
        
        # Mostrar output en tiempo real
        start_time = time.time()
        max_runtime = 600  # 10 minutos máximo
        
        while time.time() - start_time < max_runtime:
            line = proc.stdout.readline()
            if not line:
                break
            
            line = line.strip()
            if line and any(keyword in line for keyword in ['✅', '❌', '💎', 'Trade', 'PnL', 'WIN', 'LOSS']):
                print(line)
                log_message(line)
        
        proc.terminate()
        log_message("⏹️  Bot detenido")
        return True
        
    except Exception as e:
        log_message(f"❌ Error en headless: {e}", "ERROR")
        return False


def print_menu():
    """Muestra menú de opciones"""
    print("\n" + "="*70)
    print("   🤖 MONITOR DE BOT EN VIVO - EXNOVA TRADING")
    print("="*70)
    print(f"\n📧 Cuenta: {EMAIL}")
    print(f"💼 Modo: {ACCOUNT_TYPE}")
    print(f"💾 Datos: {DATA_DIR}\n")
    print("Opciones:")
    print("  1. Ejecutar bot TEST (búsqueda de oportunidades)")
    print("  2. Ejecutar bot HEADLESS (operativo continuo)")
    print("  3. Ver log actual")
    print("  4. Ver historial de sesiones")
    print("  0. Salir\n")


def view_log():
    """Muestra log actual"""
    if MONITOR_LOG.exists():
        print("\n" + "="*70)
        print("📋 LOG ACTUAL")
        print("="*70)
        with open(MONITOR_LOG) as f:
            lines = f.readlines()
            # Mostrar últimas 50 líneas
            for line in lines[-50:]:
                print(line.rstrip())
    else:
        print("❌ No hay log disponible")


def view_history():
    """Muestra historial de sesiones"""
    print("\n" + "="*70)
    print("📊 HISTORIAL DE SESIONES")
    print("="*70)
    
    if SESSION_HISTORY.exists():
        try:
            with open(SESSION_HISTORY) as f:
                history = json.load(f)
            
            if isinstance(history, list):
                for i, session in enumerate(history[-10:], 1):
                    print(f"\n#{i} - {session.get('timestamp', 'N/A')}")
                    print(f"   Resultado: {session.get('result', 'N/A')}")
                    print(f"   Duración: {session.get('duration', 'N/A')}")
            else:
                print(json.dumps(history, indent=2))
        except:
            print("❌ Error leyendo historial")
    else:
        print("📭 Sin historial aún")


def main():
    """Función principal"""
    
    print_menu()
    
    while True:
        try:
            choice = input("Selecciona opción (0-4): ").strip()
            
            if choice == '1':
                success = run_trading_bot()
                if success:
                    log_message("✅ Sesión completada exitosamente")
                else:
                    log_message("❌ Error en sesión", "ERROR")
            
            elif choice == '2':
                success = run_headless_bot()
                if success:
                    log_message("✅ Bot headless completado")
                else:
                    log_message("❌ Error en bot headless", "ERROR")
            
            elif choice == '3':
                view_log()
            
            elif choice == '4':
                view_history()
            
            elif choice == '0':
                log_message("👋 Monitor cerrado")
                print("\n✅ ¡Hasta luego!\n")
                break
            
            else:
                print("❌ Opción inválida")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitor interrumpido\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
