#!/usr/bin/env python3
"""
🚀 EJECUTOR MÚLTIPLE DE BOT EN VIVO
Ejecuta múltiples sesiones del bot y monitorea mejora/aprendizaje
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

EMAIL = os.getenv('EXNOVA_EMAIL')
DATA_DIR = Path(__file__).parent / "data" / "live_sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Archivo para almacenar resultados
RESULTS_FILE = DATA_DIR / "execution_log.json"
BOT_SCRIPT = Path(__file__).parent / "test_bot_final.py"


def extract_bot_results(output: str) -> Dict:
    """Extrae resultados de la ejecución del bot"""
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'opportunities_found': 0,
        'setups': [],
        'status': 'UNKNOWN',
    }
    
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        if '💎 OPORTUNIDAD ENCONTRADA' in line:
            results['opportunities_found'] += 1
            # Extraer información de oportunidad
            setup_data = {}
            for j in range(i+1, min(i+6, len(lines))):
                if 'Activo:' in lines[j]:
                    setup_data['asset'] = lines[j].split(':')[-1].strip()
                elif 'Acción:' in lines[j]:
                    setup_data['action'] = lines[j].split(':')[-1].strip()
                elif 'Score:' in lines[j]:
                    setup_data['score'] = lines[j].split(':')[-1].strip()
                elif 'Setup:' in lines[j]:
                    setup_data['setup'] = lines[j].split(':')[-1].strip()
            
            if setup_data:
                results['setups'].append(setup_data)
        
        if '✅ TEST COMPLETADO EXITOSAMENTE' in line:
            results['status'] = 'SUCCESS'
        elif '❌' in line or 'Error' in line or 'error' in line:
            if results['status'] != 'SUCCESS':
                results['status'] = 'ERROR'
    
    return results


def run_bot_session(session_number: int) -> Dict:
    """Ejecuta una sesión del bot"""
    
    print(f"\n{'='*70}")
    print(f"🚀 SESIÓN #{session_number} - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(BOT_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(Path(__file__).parent)
        )
        
        # Extraer resultados
        results = extract_bot_results(result.stdout)
        
        # Mostrar output importante
        for line in result.stdout.split('\n'):
            if any(kw in line for kw in ['✅', '❌', '💎', 'OPORTUNIDAD', 'SETUP', 'Confianza', 'RSI']):
                print(line)
        
        print(f"\n📊 Resultado:")
        print(f"  Oportunidades: {results['opportunities_found']}")
        print(f"  Status: {results['status']}")
        
        return results
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout")
        return {'timestamp': datetime.now().isoformat(), 'status': 'TIMEOUT', 'opportunities_found': 0}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'timestamp': datetime.now().isoformat(), 'status': 'ERROR', 'opportunities_found': 0}


def analyze_sessions(sessions: List[Dict]) -> Dict:
    """Analiza múltiples sesiones para ver mejora"""
    
    total_sessions = len(sessions)
    total_opportunities = sum(s.get('opportunities_found', 0) for s in sessions)
    successful_sessions = sum(1 for s in sessions if s.get('status') == 'SUCCESS')
    
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'total_sessions': total_sessions,
        'successful': successful_sessions,
        'success_rate': f"{(successful_sessions/total_sessions*100):.1f}%" if total_sessions > 0 else "0%",
        'total_opportunities': total_opportunities,
        'avg_opportunities_per_session': f"{(total_opportunities/total_sessions):.2f}" if total_sessions > 0 else "0",
    }
    
    return analysis


def print_final_report(sessions: List[Dict], analysis: Dict):
    """Imprime reporte final"""
    
    print("\n" + "="*70)
    print("📊 REPORTE FINAL DE EJECUCIONES")
    print("="*70)
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"  Total de sesiones:............... {analysis['total_sessions']}")
    print(f"  Sesiones exitosas:.............. {analysis['successful']}")
    print(f"  Tasa de éxito:.................. {analysis['success_rate']}")
    print(f"  Total de oportunidades:......... {analysis['total_opportunities']}")
    print(f"  Promedio por sesión:............ {analysis['avg_opportunities_per_session']}")
    
    # Resumen de oportunidades
    if analysis['total_opportunities'] > 0:
        print(f"\n💎 OPORTUNIDADES DETECTADAS:")
        all_setups = []
        for session in sessions:
            all_setups.extend(session.get('setups', []))
        
        # Contar por setup
        setup_count = {}
        for setup in all_setups:
            setup_type = setup.get('setup', 'UNKNOWN')
            setup_count[setup_type] = setup_count.get(setup_type, 0) + 1
        
        for setup_type, count in sorted(setup_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {setup_type:.<35} {count} veces")
    
    # Conclusión
    print(f"\n🎯 CONCLUSIÓN:")
    if analysis['success_rate'].rstrip('%') >= '80':
        print("  ✅ BOT OPERANDO CONSISTENTEMENTE")
        print("  💡 Está listo para OPERATIVA REAL con capital pequeño")
    elif analysis['success_rate'].rstrip('%') >= '60':
        print("  ✅ BOT OPERANDO BIEN")
        print("  💡 Continuar monitoreando y validando")
    else:
        print("  ⚠️  BOT REQUIERE AJUSTES")
        print("  💡 Revisar parámetros y estrategias")
    
    print("="*70)


def save_results(sessions: List[Dict], analysis: Dict):
    """Guarda resultados en archivo"""
    
    data = {
        'execution': {
            'timestamp': datetime.now().isoformat(),
            'email': EMAIL,
            'account_type': 'PRACTICE',
        },
        'analysis': analysis,
        'sessions': sessions,
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {RESULTS_FILE}")


def main():
    """Función principal"""
    
    print("\n" + "="*70)
    print("   🤖 EJECUTOR DE BOT EN VIVO - MÚLTIPLES SESIONES")
    print("="*70)
    print(f"\n📧 Cuenta: {EMAIL}")
    print(f"💼 Modo: PRACTICE")
    print(f"💾 Datos: {DATA_DIR}\n")
    
    try:
        num_sessions = 5
        print(f"🔄 Ejecutando {num_sessions} sesiones del bot...\n")
        
        sessions = []
        for i in range(1, num_sessions + 1):
            session_result = run_bot_session(i)
            sessions.append(session_result)
            
            # Descanso entre sesiones
            if i < num_sessions:
                print(f"\n⏳ Descansando 3 segundos...")
                time.sleep(3)
        
        # Analizar resultados
        analysis = analyze_sessions(sessions)
        
        # Mostrar reporte
        print_final_report(sessions, analysis)
        
        # Guardar resultados
        save_results(sessions, analysis)
        
        print(f"\n✅ Ejecución completada")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
