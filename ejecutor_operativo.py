#!/usr/bin/env python3
"""
🚀 EJECUTOR OPERATIVO REAL - Lanza bot test_bot_final en modo OPERACIÓN
Ejecuta operaciones REALES detectadas por el bot
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

DATA_DIR = Path(__file__).parent / "data" / "operaciones_en_vivo"
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*70)
print("   🚀 EJECUTOR OPERATIVO REAL - BOT EN VIVO")
print("="*70)
print(f"\n📧 Cuenta: daveymena16@gmail.com")
print(f"💼 Modo: PRACTICE (dinero simulado - sin riesgo)")
print(f"💰 Capital por operación: $1.00")
print(f"\n⚠️  ADVERTENCIA:")
print("   Este bot ejecutará operaciones REALES en tu cuenta Exnova.")
print("   Las operaciones se ejecutarán en PRACTICE mode (sin dinero real).")
print("   Presiona Ctrl+C para cancelar.\n")

input("Presiona Enter para continuar...")

print("\n" + "="*70)
print("🔄 INICIANDO MODO OPERATIVO CONTINUO")
print("="*70)

try:
    session_count = 0
    results = {
        'inicio': datetime.now().isoformat(),
        'sesiones': []
    }
    
    while True:
        session_count += 1
        session_start = datetime.now()
        
        print(f"\n{'─'*70}")
        print(f"🔄 SESIÓN #{session_count} - {session_start.strftime('%H:%M:%S')}")
        print(f"{'─'*70}")
        
        try:
            # Ejecutar bot test que hace operaciones reales
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "test_bot_final.py")],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Procesar salida
            output = result.stdout
            
            # Extraer información
            session_data = {
                'timestamp': session_start.isoformat(),
                'status': 'success' if result.returncode == 0 else 'error',
                'oportunidades': 0,
                'operaciones': [],
            }
            
            # Buscar oportunidades
            if '💎 OPORTUNIDAD ENCONTRADA' in output:
                session_data['oportunidades'] += 1
                
                # Extraer detalles
                for line in output.split('\n'):
                    if 'Activo:' in line:
                        asset = line.split(':')[-1].strip()
                    elif 'Acción:' in line:
                        action = line.split(':')[-1].strip()
                    elif 'Score:' in line:
                        score = line.split(':')[-1].strip()
                    elif 'Setup:' in line:
                        setup = line.split(':')[-1].strip()
                
                session_data['operaciones'].append({
                    'asset': asset,
                    'action': action,
                    'score': score,
                    'setup': setup,
                })
            
            results['sesiones'].append(session_data)
            
            # Mostrar resultados
            print(f"\n✅ Sesión completada")
            print(f"   Oportunidades: {session_data['oportunidades']}")
            print(f"   Status: {session_data['status']}")
            
            # Mostrar líneas importantes
            for line in output.split('\n'):
                if any(kw in line for kw in ['✅ CONECTADO', '✅', 'OPORTUNIDAD', 'Setup', 'Confianza']):
                    print(f"   {line.strip()}")
            
            # Guardar
            with open(DATA_DIR / f"sesion_{session_count}.json", 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Descanso
            print(f"\n⏳ Próxima sesión en 60 segundos...")
            time.sleep(60)
        
        except subprocess.TimeoutExpired:
            print("❌ Timeout")
            results['sesiones'].append({
                'timestamp': datetime.now().isoformat(),
                'status': 'timeout',
            })
        except Exception as e:
            print(f"❌ Error: {e}")
            results['sesiones'].append({
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e),
            })

except KeyboardInterrupt:
    print(f"\n\n⏹️  Modo operativo detenido por usuario")
    
    # Guardar resultados
    results['fin'] = datetime.now().isoformat()
    results['total_sesiones'] = session_count
    
    with open(DATA_DIR / "resultados.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {DATA_DIR / 'resultados.json'}")
    
    # Mostrar estadísticas
    total_oportunidades = sum(s.get('oportunidades', 0) for s in results.get('sesiones', []))
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Total sesiones: {session_count}")
    print(f"   Total oportunidades: {total_oportunidades}")
    print(f"   Promedio oportunidades/sesión: {(total_oportunidades/session_count):.2f}")
