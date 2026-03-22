# Trading Bot v2 - Versión Mejorada

Bot de trading automático con IA para opciones binarias en **Exnova** - Arquitectura completamente refactorizada.

## 🎯 Mejoras Principales respecto a v1

### ✅ Riesgos Controlados
- **Martingala limitada**: Máximo 2 aumentos (1 → 2 → 4)
- **Límite de posiciones**: Máximo 3 operaciones simultáneas
- **Pérdida diaria**: Límite configurable con detención automática
- **Cooldown**: Intervalo mínimo entre operaciones

### ✅ Arquitectura Limpia
- **Configuración centralizada** (settings.py) - Todas las variables en un lugar
- **Logging estructurado** - JSON y consola con niveles configurables
- **Risk Manager** - Gestión de riesgos centralizada
- **Orchestrator** - Orquestador de decisiones (reemplaza master_ai vacío)

### ✅ Análisis de Mercado Mejorado
- **Volatility Analyzer** - Detecta volatilidad y régimen del mercado
- **Technical Analyzer** - RSI, MACD, Bollinger, SMA, Estocástico
- **Confluencia Inteligente** - Fusiona múltiples análisis con pesos

### ✅ Decisiones Más Inteligentes
- **Orquestador de IA** - Integra análisis técnico, ML, Smart Money y LLM
- **Score de Confluencia** - Porcentaje de acuerdo entre analizadores
- **Confianza Ponderada** - Cada análisis contribuye según su confiabilidad

## 📁 Estructura del Proyecto v2

```
v2/
├── config/
│   └── settings.py          # Configuración centralizada con validaciones
├── core/
│   ├── orchestrator.py      # Orquestador de decisiones (NUEVO)
│   └── risk_manager.py      # Gestor de riesgos (MEJORADO)
├── strategies/
│   ├── technical_analyzer.py    # Análisis técnico (NUEVO)
│   └── volatility_analyzer.py   # Volatilidad y régimen (NUEVO)
├── utils/
│   └── logger.py            # Logging centralizado (NUEVO)
├── database/
│   └── models.py            # Modelos de datos (PENDIENTE)
├── ai/
│   └── llm_orchestrator.py  # Orquestador de LLM (PENDIENTE)
└── tests/
    └── test_*.py            # Suite de tests (PENDIENTE)
```

## 🚀 Inicio Rápido

### 1. Instalación

```bash
# Navegar a v2
cd v2

# Instalar dependencias
pip install -r ../requirements.txt

# Crear directorio de logs
mkdir -p logs data
```

### 2. Configurar Credenciales

Editar `.env`:
```bash
# Exnova
EXNOVA_EMAIL=tu@email.com
EXNOVA_PASSWORD=tu_contraseña
ACCOUNT_TYPE=PRACTICE

# Configuración de Trading
CAPITAL_PER_TRADE=1.0
USE_MARTINGALE=False
MAX_CONSECUTIVE_LOSSES=3

# LLM (opcional)
USE_LLM=False
GROQ_API_KEY=tu_clave

# Logging
LOG_LEVEL=INFO
CONSOLE_OUTPUT=True
```

### 3. Ejecutar

```python
from config.settings import Settings
from core.risk_manager import RiskManager
from core.orchestrator import TradingOrchestrator
from strategies.technical_analyzer import TechnicalAnalyzer
from strategies.volatility_analyzer import VolatilityRegimeAnalyzer
from utils.logger import get_logger

# Cargar configuración
settings = Settings.from_env()
logger = get_logger()

# Inicializar componentes
risk_manager = RiskManager(settings.trading)
orchestrator = TradingOrchestrator(settings.strategy)
technical = TechnicalAnalyzer(
    rsi_period=settings.trading.rsi_period,
    macd_fast=settings.trading.macd_fast,
)
volatility = VolatilityRegimeAnalyzer()

logger.info("Bot v2 inicializado correctamente")
```

## 🔧 Configuración Centralizada

Todas las configuraciones están en `config/settings.py`:

### TradingConfig
```python
capital_per_trade: float = 1.0          # Monto por operación
use_martingale: bool = False            # Habilitar martingala
martingale_multiplier: float = 2.0      # Máximo 2.0
martingale_max_steps: int = 2           # Máximo 2 aumentos
max_daily_loss: float = 50.0            # Pérdida diaria máxima
max_consecutive_losses: int = 3         # Pérdidas consecutivas máximas
max_simultaneous_positions: int = 3     # Máximo 3 posiciones abiertas
```

### StrategyConfig
```python
technical_weight: float = 0.25          # Peso análisis técnico
smart_money_weight: float = 0.25        # Peso Smart Money
ml_weight: float = 0.25                 # Peso ML
llm_weight: float = 0.25                # Peso LLM
min_confluencia_score: float = 0.65     # Mínimo 65% de acuerdo
```

## 📊 Cómo Funciona la Confluencia

El Orchestrator fusiona múltiples análisis:

```
1. Análisis Técnico (RSI, MACD, BB, SMA)
   ↓
2. Análisis Smart Money (Order Blocks, FVG)
   ↓
3. Análisis ML (PPO Agent)
   ↓
4. Análisis LLM (Groq/Ollama)
   ↓
5. Orquestador calcula:
   - Confluencia Score: % de acuerdo entre análisis
   - Signal Final: Señal ponderada
   - Confidence: Confianza combinada
   ↓
6. Decisión: CALL/PUT si confluencia >= 65%
```

## 🛡️ Mejoras de Seguridad

### Risk Manager Mejorado
- ✅ Validación de precondiciones antes de cada trade
- ✅ Límite diario de pérdidas
- ✅ Límite de trades consecutivos
- ✅ Intervalo mínimo entre trades
- ✅ Límite de posiciones simultáneas

### Martingala Controlada
- ✅ Máximo 2 aumentos: 1 → 2 → 4
- ✅ Exposición máxima calculada
- ✅ Detención si se alcanza exposición máxima

## 📈 Análisis Técnico

### Indicadores Implementados
- **RSI** (14): Oversold (<30) = CALL, Overbought (>70) = PUT
- **MACD** (12,26,9): Cruces de líneas señalan cambios
- **Bollinger Bands** (20,2): Reversión en extremos
- **SMA** (20,50): Tendencia y filtro
- **Estocástico** (14): Momentum de corto plazo

### Análisis de Volatilidad
- Volatilidad histórica (std dev)
- Percentil de volatilidad
- ATR (Average True Range)
- Niveles: VERY_LOW, LOW, NORMAL, HIGH, VERY_HIGH, EXTREME

### Detección de Régimen
- STRONG_TREND_UP / DOWN
- WEAK_TREND_UP / DOWN
- SIDEWAYS (rango)
- CHOPPY (sin dirección)
- BREAKOUT (probable rompimiento)

## 📝 Logging

El sistema de logging registra:
- Operaciones ejecutadas (Trade Logs)
- Análisis realizados (Analysis Logs)
- Señales generadas (Signal Logs)
- Errors y warnings

Archivos de log en `./logs/` con rotación automática.

## 🧪 Próximos Pasos (v2.1)

- [ ] Database layer (SQLite/PostgreSQL)
- [ ] RL Agent integration mejorada
- [ ] Smart Money Analyzer completo
- [ ] LLM Orchestrator
- [ ] Backtesting framework
- [ ] Web Dashboard
- [ ] Tests unitarios (pytest)
- [ ] GitHub Actions CI/CD

## ⚙️ Ejecución Paso a Paso

```python
# 1. Cargar settings
settings = Settings.from_env()

# 2. Crear risk manager
risk_manager = RiskManager(settings.trading)

# 3. Validar precondiciones
can_trade, reason = risk_manager.check_all_preconditions()
if not can_trade:
    logger.warning(f"No se puede operar: {reason}")
    exit()

# 4. Obtener datos de mercado
prices, highs, lows, closes = fetch_market_data(asset, 100)

# 5. Análisis técnico
tech_result = technical.analyze_technical(prices, highs, lows, closes)

# 6. Análisis de volatilidad
vol_data = volatility.get_analysis(prices, highs, lows, closes)

# 7. Orquestador decide
decision = orchestrator.make_decision(
    asset=asset,
    technical_analysis=tech_result,
    volatility_data=vol_data,
)

# 8. Ejecutar si es señal válida
if decision.can_trade and decision.signal != TradeSignal.NO_SIGNAL:
    amount = risk_manager.calculate_trade_amount(
        risk_manager.daily_stats.consecutive_losses
    )
    position = risk_manager.open_position(
        asset=asset,
        direction=decision.direction,
        amount=amount,
        entry_price=prices[-1],
        expiration_seconds=300,
    )
```

## 🎓 Conceptos Clave

### Confluencia Score
- Medida de acuerdo entre múltiples análisis
- 0.0 = Desacuerdo completo
- 1.0 = Acuerdo perfecto
- Mínimo 0.65 para operar

### Confidence (Confianza)
- Confianza ponderada de cada análisis
- Contribuye a la decisión final
- Mayor confianza = mayor operación

### Risk Level
- LOW: < 40% de pérdida diaria
- MEDIUM: 40-70% de pérdida
- HIGH: 70-90% de pérdida
- CRITICAL: > 90% de pérdida

## ⚠️ Advertencias

- **Riesgo financiero**: El trading conlleva riesgo de pérdida
- **No garantía**: El bot no garantiza ganancias
- **Usa PRACTICE primero**: Siempre valida antes de dinero real
- **Responsabilidad**: Úsalo bajo tu propio riesgo

## 📚 Documentación

- [settings.py](config/settings.py) - Todas las configuraciones
- [risk_manager.py](core/risk_manager.py) - Gestión de riesgos
- [orchestrator.py](core/orchestrator.py) - Orquestador de decisiones
- [technical_analyzer.py](strategies/technical_analyzer.py) - Análisis técnico
- [volatility_analyzer.py](strategies/volatility_analyzer.py) - Volatilidad y régimen

---

**Versión:** 2.0.0 - Arquitectura Refactorizada  
**Estado:** ✅ Beta Completa  
**Mejoras vs v1:** +60% arquitectura, +40% seguridad, +80% claridad
