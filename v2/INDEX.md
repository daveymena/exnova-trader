# 📋 ÍNDICE DE ARCHIVOS - Trading Bot v2

## 🎯 Documentación Principal

### 📖 Guías
- **[README.md](README.md)** - Guía principal de v2
  - Inicio rápido
  - Estructura del proyecto
  - Configuración centralizada
  - Cómo funciona la confluencia
  
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Cómo migrar de v1 a v2
  - Resumen de cambios
  - Comparación de arquitectura
  - Pasos de migración
  - Preguntas frecuentes
  
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** - Resumen ejecutivo
  - Objetivos principales
  - Resultados clave
  - Estructura implementada
  - Plan de rollout

---

## 🔧 Código Principal

### ⚙️ Configuración
- **[config/settings.py](config/settings.py)** (380 líneas)
  - `TradingConfig` - Parámetros de trading
  - `BrokerConfig` - Credenciales Exnova
  - `LLMConfig` - Configuración de LLM
  - `LoggingConfig` - Configuración de logs
  - `DatabaseConfig` - BD configuration
  - `StrategyConfig` - Parámetros de estrategia
  - `Settings` - Clase principal que carga todo
  
  **Características:**
  - ✅ Validación automática
  - ✅ Carga desde `.env`
  - ✅ Valores por defecto seguros
  - ✅ Documentación en código

### 🎮 Core Trading
- **[core/risk_manager.py](core/risk_manager.py)** (310 líneas)
  - `RiskManager` - Gestor centralizado de riesgos
  - `Position` - Representa una posición abierta
  - `DailyStats` - Estadísticas diarias
  - `RiskLevel` - Enum de niveles de riesgo
  
  **Funcionalidades:**
  - ✅ Validación de precondiciones
  - ✅ Control de Martingala
  - ✅ Límite de posiciones simultáneas
  - ✅ Intervalo mínimo entre trades
  - ✅ Detección de límites diarios
  - ✅ Cálculo dinámico de monto

- **[core/orchestrator.py](core/orchestrator.py)** (420 líneas)
  - `TradingOrchestrator` - Orquestador de decisiones
  - `OrchestratorDecision` - Decisión final
  - `AnalysisResult` - Resultado de análisis
  - `TradeSignal` - Enum de señales
  
  **Funcionalidades:**
  - ✅ Confluencia Score (acuerdo entre análisis)
  - ✅ Fusión ponderada de análisis
  - ✅ Confianza combinada
  - ✅ Generación de reasoning
  - ✅ Historial de decisiones
  - ✅ Estadísticas del orquestador

### 📊 Estrategias de Análisis
- **[strategies/technical_analyzer.py](strategies/technical_analyzer.py)** (390 líneas)
  - `TechnicalAnalyzer` - Analizador de indicadores técnicos
  - `TechnicalIndicatorType` - Enum de indicadores
  
  **Indicadores implementados:**
  - ✅ RSI (Relative Strength Index)
  - ✅ MACD (Moving Average Convergence Divergence)
  - ✅ Bollinger Bands
  - ✅ SMA (Simple Moving Average)
  - ✅ EMA (Exponential Moving Average)
  - ✅ Estocástico
  - ✅ ATR (Average True Range)

- **[strategies/volatility_analyzer.py](strategies/volatility_analyzer.py)** (360 líneas)
  - `VolatilityRegimeAnalyzer` - Analizador de volatilidad
  - `VolatilityLevel` - Enum de niveles de volatilidad
  - `MarketRegime` - Enum de regímenes de mercado
  
  **Funcionalidades:**
  - ✅ Volatilidad histórica
  - ✅ Percentil de volatilidad
  - ✅ ATR (Average True Range)
  - ✅ Detección de régimen (8 tipos)
  - ✅ Detección de breakout
  - ✅ Análisis de tendencia
  - ✅ Soporte y resistencia
  - ✅ Posición de precio en rango

### 📝 Utilidades
- **[utils/logger.py](utils/logger.py)** (140 líneas)
  - `TradingLogger` - Logger singleton
  - `JSONFormatter` - Formatter JSON
  
  **Funcionalidades:**
  - ✅ Logging estructurado
  - ✅ Salida JSON y consola
  - ✅ Rotación automática de archivos
  - ✅ Métodos especializados (trade, signal, analysis)
  - ✅ Niveles de logging

---

## 🧪 Testing

- **[tests/test_core_components.py](tests/test_core_components.py)** (380 líneas)
  - `TestTradingConfig` - Tests de configuración
  - `TestRiskManager` - Tests del gestor de riesgos
  - `TestTradingOrchestrator` - Tests del orquestador
  - `TestTechnicalAnalyzer` - Tests de análisis técnico
  - `TestVolatilityAnalyzer` - Tests de volatilidad
  
  **Cobertura:**
  - ✅ 25+ tests unitarios
  - ✅ pytest framework
  - ✅ Mock objects
  - ✅ Fixtures reutilizables
  - ✅ Assertions comprehensivas

---

## 📚 Ejemplos

- **[example_usage.py](example_usage.py)** (240 líneas)
  - Ejemplo completo de uso
  - Demostración de todos los componentes
  - Simulación de operación
  - Generación de datos de prueba

---

## 📂 Estructura de Directorios

```
v2/
├── README.md                              # Guía principal
├── MIGRATION_GUIDE.md                    # Guía de migración
├── EXECUTIVE_SUMMARY.md                  # Resumen ejecutivo
├── INDEX.md                              # Este archivo
├── example_usage.py                      # Ejemplo completo
│
├── config/
│   ├── __init__.py
│   └── settings.py                       # Configuración centralizada
│
├── core/
│   ├── __init__.py
│   ├── orchestrator.py                   # Orquestador de decisiones
│   └── risk_manager.py                   # Gestor de riesgos
│
├── strategies/
│   ├── __init__.py
│   ├── technical_analyzer.py             # Análisis técnico
│   └── volatility_analyzer.py            # Volatilidad y régimen
│
├── ai/
│   └── __init__.py                       # Placeholder para futura integración
│
├── database/
│   └── __init__.py                       # Placeholder para DB layer
│
├── utils/
│   ├── __init__.py
│   └── logger.py                         # Sistema de logging
│
└── tests/
    ├── __init__.py
    └── test_core_components.py           # Tests unitarios
```

---

## 🎯 Cómo Usar Este Índice

### Para Entender la Arquitectura
1. Lee [README.md](README.md)
2. Revisa [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
3. Examina [core/orchestrator.py](core/orchestrator.py)

### Para Migrar desde v1
1. Lee [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. Revisa [config/settings.py](config/settings.py)
3. Ejecuta [example_usage.py](example_usage.py)

### Para Hacer Testing
1. Instala pytest: `pip install pytest`
2. Ejecuta: `pytest tests/test_core_components.py -v`
3. Revisa resultados

### Para Entender Componentes Específicos

**¿Quiero entender el Risk Manager?**
- Lee: [core/risk_manager.py](core/risk_manager.py)
- Tests: `TestRiskManager` en [tests/test_core_components.py](tests/test_core_components.py)

**¿Quiero entender el Orchestrator?**
- Lee: [core/orchestrator.py](core/orchestrator.py)
- Tests: `TestTradingOrchestrator` en [tests/test_core_components.py](tests/test_core_components.py)

**¿Quiero entender los Indicadores Técnicos?**
- Lee: [strategies/technical_analyzer.py](strategies/technical_analyzer.py)
- Tests: `TestTechnicalAnalyzer` en [tests/test_core_components.py](tests/test_core_components.py)

**¿Quiero entender Volatilidad?**
- Lee: [strategies/volatility_analyzer.py](strategies/volatility_analyzer.py)
- Tests: `TestVolatilityAnalyzer` en [tests/test_core_components.py](tests/test_core_components.py)

---

## 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Archivos Python** | 9 |
| **Archivos Markdown** | 4 |
| **Total de líneas de código** | ~2,600 |
| **Tests unitarios** | 25+ |
| **Clases principales** | 12 |
| **Métodos públicos** | 60+ |
| **Indicadores técnicos** | 7 |
| **Regímenes de mercado** | 8 |
| **Niveles de riesgo** | 4 |
| **Señales de trading** | 6 |

---

## 🚀 Próximos Pasos

### Corto Plazo (v2.1)
- [ ] Database layer
- [ ] RL Agent integration
- [ ] Backtesting framework

### Mediano Plazo (v2.2)
- [ ] Smart Money Analyzer
- [ ] LLM Orchestrator
- [ ] Multi-asset monitoring

### Largo Plazo (v3.0)
- [ ] Web Dashboard
- [ ] Mobile App
- [ ] Cloud deployment

---

## ✅ Checklist de Uso

- [ ] Leí el README.md
- [ ] Configuré el .env
- [ ] Ejecuté example_usage.py
- [ ] Corrí los tests
- [ ] Entiendo la arquitectura
- [ ] Estoy listo para usar v2

---

**Última actualización**: 22 de Marzo, 2026  
**Versión**: 2.0.0  
**Estado**: ✅ Beta Completa
