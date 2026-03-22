# 🚀 EXNOVA Trading Bot - Versión Descargable

**Bot de trading automático sin restricciones para Exnova en modo PRACTICE**

## ⚡ Inicio Rápido (3 pasos)

### 1️⃣ Configurar
```bash
cp .env.example .env
# Editar .env con tus credenciales
nano .env
```

### 2️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3️⃣ Ejecutar
```bash
python3 bot_practice_operativo.py
```

## ✨ Lo que hace

- ✅ Conecta directamente a Exnova API
- ✅ Ejecuta operaciones automáticas en PRACTICE mode
- ✅ Sincroniza tiempo del servidor automáticamente
- ✅ Sin restricciones - Operaciones continuas 24/7
- ✅ Logs detallados de cada operación
- ✅ Datos guardados en JSON para análisis

## 📊 Archivos Generados

Durante la ejecución se crean:

```
data/operaciones_ejecutadas/
├── sesion_20260322_230526.log    ← Logs detallados
└── trades_20260322_230526.json   ← Datos de operaciones
```

Cada operación incluye:
- Timestamp
- Activo (EURUSD, GBPUSD, etc)
- Dirección (CALL/PUT)
- Resultado (WIN/LOSS)
- Ganancia/Pérdida

## 🎯 Configuración

Edita `.env` para cambiar:

```env
# Dinero por operación (sin riesgo real, es PRACTICE)
CAPITAL_PER_TRADE=1.0

# Tiempo de expiración en segundos
EXPIRATION_TIME=60

# Tipo de cuenta (PRACTICE = sin riesgo)
ACCOUNT_TYPE=PRACTICE
```

## 📈 Resultados

El bot automáticamente:
1. Conecta a Exnova
2. Sincroniza el tiempo
3. Ejecuta operaciones cada 75 segundos (65s de operación + 10s de espera)
4. Registra ganancia/pérdida
5. Guarda todos los datos

## 🔧 Requisitos

- Python 3.7+
- pip
- Conexión a internet
- Cuenta Exnova (cualquier cuenta, puede ser demo)

## 🛑 Detener el Bot

Presiona: `Ctrl + C`

El bot mostrará estadísticas finales:
- Total de operaciones
- Ganancias vs Pérdidas
- Win Rate
- PnL Total

## 🐛 Solución de Problemas

**"No se puede conectar"**
- Verifica `.env` tenga email y password correctos
- Verifica conexión a internet
- Verifica ACCOUNT_TYPE=PRACTICE

**"API no disponible"**
- Ejecuta: `pip install -r requirements.txt --upgrade`

**"Operaciones no se están ejecutando"**
- Revisa logs en `data/operaciones_ejecutadas/`
- Verifica que el .env esté bien configurado

## 📝 Notas

1. **PRACTICE Mode**: Dinero SIMULADO - Sin riesgo real
2. **Logs**: Todo se guarda automáticamente para análisis
3. **Datos**: JSON format para fácil análisis
4. **24/7**: El bot puede correr continuamente

## 🚀 Próximos Pasos

1. Ejecutar bot y recolectar 100+ operaciones
2. Analizar resultados (Win Rate, ROI, Sharpe Ratio)
3. Si performance > 55% WR → cambiar a modo REAL con capital real

## 📦 Archivos Principales

- `bot_final.py` ⭐ Bot principal SIN RESTRICCIONES
- `bot_practice_operativo.py` 🚀 Ejecutor
- `.env.example` 📝 Configuración (renombrar a .env)
- `requirements.txt` 📦 Dependencias
- `exnovaapi/` 🔌 API de Exnova
- `data/` 📊 Resultados y logs

---

**¡Listo para operar! 🎉**

