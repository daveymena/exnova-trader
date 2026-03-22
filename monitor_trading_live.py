#!/usr/bin/env python3
"""
MONITOR DE BOT EN VIVO - Supervisa el trading continuamente
Ejecuta sesiones de trading, monitorea rentabilidad, y mejora automáticamente
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import subprocess
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'data' / 'monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variables
BOT_SCRIPT = Path(__file__).parent / "run_adaptive_bot.py"
DATA_DIR = Path(__file__).parent / "data" / "adaptive_trading"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_REPORT = DATA_DIR / "monitor_report.json"

# Historial de sesiones
SESSIONS_HISTORY = []


def run_trading_session(session_number: int) -> Dict:
    """Ejecuta una sesión de trading y retorna resultados"""
    
    logger.info(f"═" * 70)
    logger.info(f"🚀 INICIANDO SESIÓN #{session_number}")
    logger.info(f"═" * 70)
    
    try:
        # Ejecutar bot
        result = subprocess.run(
            [sys.executable, str(BOT_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Extraer información del reporte
        if result.returncode == 0:
            # Buscar archivo de reporte más reciente
            reports = sorted(DATA_DIR.glob("session_report_*.json"), reverse=True)
            
            if reports:
                with open(reports[0]) as f:
                    report = json.load(f)
                
                logger.info(f"✅ Sesión #{session_number} completada")
                logger.info(f"   Win Rate: {report['win_rate']}")
                logger.info(f"   PnL: {report['daily_pnl']}")
                logger.info(f"   ROI: {report['roi']}")
                
                return report
        else:
            logger.error(f"❌ Error ejecutando sesión: {result.stderr[:200]}")
    
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Sesión #{session_number} timeout")
    except Exception as e:
        logger.error(f"❌ Error en sesión #{session_number}: {e}")
    
    return None


def analyze_performance(sessions: List[Dict]) -> Dict:
    """Analiza el rendimiento de múltiples sesiones"""
    
    if not sessions:
        return {}
    
    win_rates = [float(s['win_rate'].strip('%')) for s in sessions if 'win_rate' in s]
    rois = [float(s['roi'].strip('%')) for s in sessions if 'roi' in s]
    pnls = [float(s['daily_pnl'].strip('$')) for s in sessions if 'daily_pnl' in s]
    
    analysis = {
        'total_sessions': len(sessions),
        'avg_win_rate': f"{sum(win_rates)/len(win_rates):.1f}%" if win_rates else "N/A",
        'avg_roi': f"{sum(rois)/len(rois):.1f}%" if rois else "N/A",
        'total_pnl': f"${sum(pnls):.2f}" if pnls else "$0.00",
        'best_win_rate': f"{max(win_rates):.1f}%" if win_rates else "N/A",
        'worst_win_rate': f"{min(win_rates):.1f}%" if win_rates else "N/A",
        'best_roi': f"{max(rois):.1f}%" if rois else "N/A",
        'worst_roi': f"{min(rois):.1f}%" if rois else "N/A",
        'timestamp': datetime.now().isoformat(),
    }
    
    return analysis


def print_monitor_status(sessions: List[Dict], analysis: Dict):
    """Imprime estado del monitor"""
    
    print("\n" + "="*70)
    print("📊 REPORTE DE MONITOREO - BOT EN VIVO")
    print("="*70)
    
    print(f"\n📈 RENDIMIENTO ACUMULADO:")
    print(f"  Sesiones ejecutadas:................ {analysis.get('total_sessions', 0)}")
    print(f"  Win Rate promedio:.................. {analysis.get('avg_win_rate', 'N/A')}")
    print(f"  ROI promedio:........................ {analysis.get('avg_roi', 'N/A')}")
    print(f"  PnL Total acumulado:................ {analysis.get('total_pnl', 'N/A')}")
    
    print(f"\n📊 EXTREMOS:")
    print(f"  Mejor Win Rate:..................... {analysis.get('best_win_rate', 'N/A')}")
    print(f"  Peor Win Rate:....................... {analysis.get('worst_win_rate', 'N/A')}")
    print(f"  Mejor ROI:.......................... {analysis.get('best_roi', 'N/A')}")
    print(f"  Peor ROI:........................... {analysis.get('worst_roi', 'N/A')}")
    
    print(f"\n📝 ÚLTIMAS SESIONES:")
    for i, session in enumerate(sessions[-3:] if len(sessions) > 3 else sessions, start=max(1, len(sessions)-2)):
        print(f"  #{i}: WR={session.get('win_rate', 'N/A')} | ROI={session.get('roi', 'N/A')} | PnL={session.get('daily_pnl', 'N/A')}")
    
    print("\n💡 EVALUACIÓN:")
    try:
        avg_roi = float(analysis.get('avg_roi', '0%').strip('%'))
        avg_wr = float(analysis.get('avg_win_rate', '0%').strip('%'))
        
        if avg_roi >= 50 and avg_wr >= 85:
            print("  ✅ EXCELENTE: Sistema es altamente rentable")
            print("  🎯 Próximo paso: Escalado a cuenta REAL")
        elif avg_roi >= 30 and avg_wr >= 70:
            print("  ✅ MUY BUENO: Sistema es consistentemente rentable")
            print("  🎯 Próximo paso: Ejecutar más sesiones para validar")
        elif avg_roi >= 15 and avg_wr >= 60:
            print("  ✅ BUENO: Sistema es rentable con mejora necesaria")
            print("  🎯 Próximo paso: Ajustar parámetros de estrategias")
        else:
            print("  ⚠️  REQUIERE MEJORA: ROI o Win Rate insuficientes")
            print("  🎯 Próximo paso: Revisar lógica de entrada/salida")
    except:
        pass
    
    print("\n" + "="*70)


def save_monitor_report(analysis: Dict):
    """Guarda reporte del monitor"""
    with open(MONITOR_REPORT, 'w') as f:
        json.dump(analysis, f, indent=2)


def main():
    """Función principal del monitor"""
    
    print("\n" + "="*70)
    print("   🤖 MONITOR DE BOT EN VIVO - SISTEMA OPERATIVO REAL v3")
    print("="*70)
    print(f"\n📍 Ejecutando en: {Path.cwd()}")
    print(f"💾 Datos guardados en: {DATA_DIR}")
    print(f"📝 Log guardado en: {Path(__file__).parent / 'data' / 'monitor.log'}")
    
    logger.info("Monitor iniciado")
    
    try:
        num_sessions = 3  # Ejecutar 3 sesiones de prueba
        
        print(f"\n🔄 Ejecutando {num_sessions} sesiones de trading...")
        
        for i in range(1, num_sessions + 1):
            session_result = run_trading_session(i)
            
            if session_result:
                SESSIONS_HISTORY.append(session_result)
            
            # Descanso entre sesiones
            if i < num_sessions:
                logger.info(f"⏳ Descansando 5 segundos antes de siguiente sesión...")
                time.sleep(5)
        
        # Analizar rendimiento
        analysis = analyze_performance(SESSIONS_HISTORY)
        save_monitor_report(analysis)
        
        # Mostrar status
        print_monitor_status(SESSIONS_HISTORY, analysis)
        
        logger.info("Monitor completado exitosamente")
        
        print("\n✅ Monitoreo completado")
        print(f"📊 Reporte guardado en: {MONITOR_REPORT}\n")
        
    except KeyboardInterrupt:
        logger.warning("Monitor interrumpido por usuario")
        print("\n\n⚠️  Monitor interrumpido\n")
    except Exception as e:
        logger.error(f"Error crítico: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
