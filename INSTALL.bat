@echo off
echo 🚀 Instalando EXNOVA Trading Bot
echo ==================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado
    echo Descargalo de: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python encontrado: %PYTHON_VERSION%

REM Crear carpeta de datos
if not exist "data\operaciones_ejecutadas" (
    mkdir data\operaciones_ejecutadas
    echo ✅ Carpeta de datos creada
)

REM Copiar .env
if not exist ".env" (
    copy .env.example .env
    echo ✅ Archivo .env creado
    echo.
    echo ⚠️  IMPORTANTE: Edita .env con tus credenciales:
    echo    EXNOVA_EMAIL=tu_email
    echo    EXNOVA_PASSWORD=tu_password
    echo.
    echo Abre .env con notepad: notepad .env
    echo.
) else (
    echo ✅ Archivo .env ya existe
)

REM Instalar dependencias
echo.
echo 📦 Instalando dependencias...
pip install -r requirements.txt

echo.
echo ✅ ¡Instalacion completa!
echo.
echo Para ejecutar el bot:
echo    python bot_practice_operativo.py
echo.
echo O directamente:
echo    python bot_final.py
echo.
pause
