#!/usr/bin/env python3
"""
🚀 BOT EN VIVO PRACTICE - Operativo 24/7
Ejecuta operaciones reales en PRACTICE mode de forma continua
"""

import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "operaciones_practice_vivo"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = DATA_DIR / f"bot_operando_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    """Log a mensaje"""
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

print("\n" + "="*70)
print("   🚀 BOT EN VIVO PRACTICE - OPERATIVO 24/7")
print("="*70)
print(f"\n📧 Cuenta: daveymena16@gmail.com")
print(f"💼 Modo: PRACTICE (dinero simulado)")
print(f"💰 Capital por operación: $1.00")
print(f"📊 Log: {LOG_FILE}")
print(f"\n⚠️  El bot está operando EN VIVO en PRACTICE mode.")
print("   Presiona Ctrl+C para detener.\n")

log("\n" + "="*70)
log("🚀 INICIANDO BOT EN PRACTICE OPERATIVO CONTINUO")
log("="*70)

sesion = 0
try:
    while True:
        sesion += 1
        sesion_start = datetime.now()
        
        log(f"\n{'─'*70}")
        log(f"🔄 SESIÓN #{sesion} - {sesion_start.strftime('%H:%M:%S')}")
        log(f"{'─'*70}")
        
        try:
            # Ejecutar bot
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "test_bot_final.py")],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            output = result.stdout
            
            # Log de líneas importantes
            for line in output.split('\n'):
                if any(kw in line for kw in ['✅', '💎 OPORTUNIDAD', 'RSI:', 'CONECTADO', 'Disponibles']):
                    log(f"   {line}")
            
            # Contar oportunidades
            oportunidades = output.count('💎 OPORTUNIDAD')
            
            if oportunidades > 0:
                log(f"✅ Sesión #{sesion}: {oportunidades} oportunidad(es) detectada(s)")
            else:
                log(f"⏳ Sesión #{sesion}: Escaneando mercado")
            
            elapsed = (datetime.now() - sesion_start).total_seconds()
            log(f"   Tiempo: {elapsed:.0f}s")
            
            # Pequeño descanso
            log(f"⏳ Esperando 30 segundos para siguiente escaneo...")
            time.sleep(30)
        
        except subprocess.TimeoutExpired:
            log(f"❌ Sesión #{sesion}: Timeout")
        except Exception as e:
            log(f"❌ Sesión #{sesion}: Error - {e}")
        
        # Cada 10 sesiones, mostrar estadísticas
        if sesion % 10 == 0:
            log(f"\n📊 ESTADÍSTICAS (primeras {sesion} sesiones):")
            log(f"   Total sesiones: {sesion}")
            log(f"   Tiempo corriendo: {(datetime.now() - sesion_start).total_seconds() / 60:.0f} minutos")

except KeyboardInterrupt:
    log(f"\n\n⏹️  BOT DETENIDO POR USUARIO")
    log(f"   Total sesiones: {sesion}")
    log(f"   Tiempo total: {(datetime.now().now()).isoformat()}")
    log("="*70 + "\n")

print(f"\n✅ Bot detenido. Log guardado en: {LOG_FILE}")
