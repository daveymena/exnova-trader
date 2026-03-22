#!/bin/bash

echo "🚀 Instalando EXNOVA Trading Bot"
echo "=================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "Descárgalo de: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Crear carpeta de datos
mkdir -p data/operaciones_ejecutadas
echo "✅ Carpeta de datos creada"

# Copiar .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Archivo .env creado"
    echo ""
    echo "⚠️  IMPORTANTE: Edita .env con tus credenciales:"
    echo "   EXNOVA_EMAIL=tu_email"
    echo "   EXNOVA_PASSWORD=tu_password"
    echo ""
    echo "Edita .env con:"
    echo "   nano .env   (Linux/Mac)"
    echo "   notepad .env (Windows)"
else
    echo "✅ Archivo .env ya existe"
fi

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "✅ ¡Instalación completa!"
echo ""
echo "Para ejecutar el bot:"
echo "   python3 bot_practice_operativo.py"
echo ""
echo "O directamente:"
echo "   python3 bot_final.py"
