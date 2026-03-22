# 🚀 EXNOVA TRADING BOT - Paquete Descargable

## Información del Paquete
- **Versión**: 1.0.0
- **Fecha**: 2026-03-22
- **Modo**: PRACTICE (Dinero Simulado)
- **Capital por operación**: $1.00
- **Cuenta**: daveymena16@gmail.com

## ✨ Características

- ✅ Conecta directamente a Exnova API
- ✅ Ejecuta operaciones reales en PRACTICE mode
- ✅ Sin restricciones - Operaciones continuas
- ✅ Sincronización automática de tiempo
- ✅ Logging detallado de operaciones
- ✅ Estadísticas en tiempo real
- ✅ Datos guardados en JSON para análisis

## 📦 Contenido del Paquete

```
exnova-trader/
├── bot_final.py                 ⭐ Bot principal SIN RESTRICCIONES
├── bot_practice_operativo.py    🚀 Ejecutor (llama a bot_final.py)
├── .env.example                 📝 Configuración (renombrar a .env)
├── requirements.txt             📦 Dependencias Python
├── exnovaapi/                   🔌 API de Exnova
├── data/                        📊 Carpeta para logs y resultados
├── config.py                    ⚙️ Configuración
├── README.md                    📖 Documentación
└── ...                          

```

## 🚀 Cómo Usar

### 1. Configuración Inicial

```bash
# Descargar y extraer el paquete
unzip exnova-trader.zip
cd exnova-trader

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
cp .env.example .env
# Editar .env con tus credenciales de Exnova
```

### 2. Ejecutar el Bot

**Opción A: Usar el ejecutor (recomendado)**
```bash
python3 bot_practice_operativo.py
```

**Opción B: Ejecutar el bot directamente**
```bash
python3 bot_final.py
```

### 3. Ver Resultados

Los logs se guardan en:
```
data/operaciones_ejecutadas/
├── sesion_YYYYMMDD_HHMMSS.log    (Logs detallados)
└── trades_YYYYMMDD_HHMMSS.json   (Datos de operaciones)
```

## 📊 Archivos de Configuración

### .env (IMPORTANTE: Renombrar de .env.example)
```env
EXNOVA_EMAIL=tu_email@gmail.com
EXNOVA_PASSWORD=tu_password
ACCOUNT_TYPE=PRACTICE
CAPITAL_PER_TRADE=1.0
EXPIRATION_TIME=60
```

## 📈 Datos de Salida

Cada operación se registra con:
- ID único
- Timestamp
- Activo (EURUSD, GBPUSD, etc)
- Dirección (CALL/PUT)
- Resultado (WIN/LOSS)
- PnL (Ganancia/Pérdida)

## 🔧 Requisitos

- Python 3.7+
- pip
- Conexión a internet
- Cuenta Exnova

## ⚙️ Configuración Avanzada

En `config.py` puedes ajustar:
- `CAPITAL_PER_TRADE`: Dinero por operación
- `EXPIRATION_TIME`: Tiempo de expiración (segundos)
- `MAX_CONSECUTIVE_LOSSES`: Pérdidas máximas consecutivas
- `MAX_DAILY_LOSS`: Pérdida máxima diaria

## 🐛 Troubleshooting

**Error: "Exnova API no disponible"**
- Ejecuta: `pip install -r requirements.txt`

**Error: "No se pudo conectar a Exnova"**
- Verifica credenciales en `.env`
- Verifica conexión a internet
- Verifica que ACCOUNT_TYPE sea "PRACTICE"

**Error: "Operaciones no se están ejecutando"**
- Revisa los logs en `data/operaciones_ejecutadas/`
- Asegúrate de que el .env esté configurado correctamente

## 📝 Notas Importantes

1. **PRACTICE Mode**: Este paquete usa dinero SIMULADO. No hay riesgo real.
2. **Seguridad**: Nunca compartas tu archivo `.env` con credenciales
3. **Logs**: Los logs se guardan automáticamente y pueden ser analizados después
4. **Datos**: Todos los datos se guardan en JSON para análisis posterior

## 🎯 Próximos Pasos

1. Ejecutar el bot y dejar que colecte 100+ operaciones
2. Analizar los resultados (Win Rate, ROI, Sharpe Ratio)
3. Si validamos la estrategia, cambiar ACCOUNT_TYPE a "REAL" para operar con dinero real

## 📞 Soporte

Para problemas o preguntas:
- Revisa los logs en `data/operaciones_ejecutadas/`
- Verifica la configuración en `.env`
- Consulta `README.md` para más información

---

**¡Bot listo para usar! 🚀**

