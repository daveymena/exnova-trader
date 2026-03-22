#!/usr/bin/env python3
"""
🚀 BOT EN VIVO PRACTICE - Operativo 24/7 SIN RESTRICCIONES
Ejecuta operaciones reales en PRACTICE mode de forma continua
"""

import subprocess
import sys
from pathlib import Path

# Simplemente ejecutar el bot de operaciones
bot_path = Path(__file__).parent / "bot_ejecutor_operaciones.py"

print("\n" + "="*70)
print("   🚀 INICIANDO BOT EJECUTOR DE OPERACIONES")
print("="*70 + "\n")

subprocess.run([sys.executable, str(bot_path)])
