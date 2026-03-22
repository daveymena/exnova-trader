"""
Tests unitarios para componentes clave del Trading Bot v2
"""

import pytest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime, timedelta

# Configurar PYTHONPATH
import sys
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import (
    Settings, TradingConfig, BrokerConfig, LLMConfig,
    LoggingConfig, DatabaseConfig, StrategyConfig, AccountType
)
from core.risk_manager import RiskManager, DailyStats, RiskLevel
from core.orchestrator import TradingOrchestrator, TradeSignal, AnalysisResult
from strategies.technical_analyzer import TechnicalAnalyzer
from strategies.volatility_analyzer import VolatilityRegimeAnalyzer, VolatilityLevel, MarketRegime


class TestTradingConfig:
    """Tests para TradingConfig"""
    
    def test_config_creation(self):
        """Verifica creación correcta de TradingConfig"""
        config = TradingConfig(
            capital_per_trade=1.0,
            use_martingale=False,
        )
        assert config.capital_per_trade == 1.0
        assert config.use_martingale == False
    
    def test_martingale_max_steps_limit(self):
        """Verifica límite de pasos de Martingala"""
        config = TradingConfig(martingale_max_steps=5)
        
        with pytest.raises(ValueError):
            config.validate()
    
    def test_capital_per_trade_positive(self):
        """Verifica que capital_per_trade sea positivo"""
        config = TradingConfig(capital_per_trade=-1.0)
        
        with pytest.raises(ValueError):
            config.validate()
    
    def test_max_simultaneous_positions_limit(self):
        """Verifica límite de posiciones simultáneas"""
        config = TradingConfig(max_simultaneous_positions=15)
        
        with pytest.raises(ValueError):
            config.validate()


class TestRiskManager:
    """Tests para RiskManager"""
    
    @pytest.fixture
    def config(self):
        return TradingConfig(
            capital_per_trade=1.0,
            max_daily_loss=50.0,
            max_consecutive_losses=3,
            max_simultaneous_positions=3,
        )
    
    @pytest.fixture
    def risk_manager(self, config):
        return RiskManager(config)
    
    def test_initialization(self, risk_manager):
        """Verifica inicialización correcta"""
        assert risk_manager.config is not None
        assert len(risk_manager.positions) == 0
        assert risk_manager.daily_stats.trades_count == 0
    
    def test_check_daily_loss_limit(self, risk_manager):
        """Verifica verificación de límite diario"""
        # Debería estar permitido inicialmente
        assert risk_manager.check_daily_loss_limit() == True
        
        # Simular pérdida diaria
        risk_manager.daily_stats.loss_amount = 60.0
        assert risk_manager.check_daily_loss_limit() == False
    
    def test_check_consecutive_losses(self, risk_manager):
        """Verifica límite de pérdidas consecutivas"""
        assert risk_manager.check_consecutive_losses() == True
        
        risk_manager.daily_stats.consecutive_losses = 3
        assert risk_manager.check_consecutive_losses() == False
    
    def test_check_simultaneous_positions(self, risk_manager):
        """Verifica límite de posiciones simultáneas"""
        assert risk_manager.check_simultaneous_positions() == True
        
        # Agregar 3 posiciones (límite)
        for i in range(3):
            position = MagicMock()
            position.is_expired = False
            risk_manager.positions.append(position)
        
        assert risk_manager.check_simultaneous_positions() == False
    
    def test_calculate_trade_amount_without_martingale(self, risk_manager):
        """Verifica cálculo de monto sin Martingala"""
        amount = risk_manager.calculate_trade_amount(consecutive_losses=0)
        assert amount == 1.0
    
    def test_calculate_trade_amount_with_martingale(self, risk_manager):
        """Verifica cálculo de monto con Martingala"""
        risk_manager.config.use_martingale = True
        risk_manager.config.martingale_multiplier = 2.0
        
        # Primera pérdida: 1 * 2^1 = 2
        amount = risk_manager.calculate_trade_amount(consecutive_losses=1)
        assert amount == 2.0
        
        # Segunda pérdida: 1 * 2^2 = 4
        amount = risk_manager.calculate_trade_amount(consecutive_losses=2)
        assert amount == 4.0
        
        # Tercera pérdida limitada a max_steps: 1 * 2^2 = 4
        amount = risk_manager.calculate_trade_amount(consecutive_losses=3)
        assert amount == 4.0
    
    def test_get_risk_level(self, risk_manager):
        """Verifica cálculo del nivel de riesgo"""
        risk_manager.daily_stats.loss_amount = 10.0
        assert risk_manager.get_risk_level() == RiskLevel.LOW
        
        risk_manager.daily_stats.loss_amount = 25.0
        assert risk_manager.get_risk_level() == RiskLevel.MEDIUM
        
        risk_manager.daily_stats.loss_amount = 40.0
        assert risk_manager.get_risk_level() == RiskLevel.HIGH
        
        risk_manager.daily_stats.loss_amount = 48.0
        assert risk_manager.get_risk_level() == RiskLevel.CRITICAL


class TestTradingOrchestrator:
    """Tests para TradingOrchestrator"""
    
    @pytest.fixture
    def strategy_config(self):
        return StrategyConfig(
            technical_weight=0.5,
            smart_money_weight=0.5,
            ml_weight=0.0,
            llm_weight=0.0,
        )
    
    @pytest.fixture
    def orchestrator(self, strategy_config):
        return TradingOrchestrator(strategy_config)
    
    def test_initialization(self, orchestrator):
        """Verifica inicialización correcta"""
        assert orchestrator.config is not None
        assert len(orchestrator.history) == 0
    
    def test_calculate_confluencia_perfect_agreement(self, orchestrator):
        """Verifica confluencia con acuerdo perfecto"""
        analyses = [
            AnalysisResult("A", TradeSignal.BUY, 0.8, 0.9),
            AnalysisResult("B", TradeSignal.BUY, 0.8, 0.9),
        ]
        weights = {"A": 0.5, "B": 0.5}
        
        confluencia = orchestrator._calculate_confluencia(analyses, weights)
        assert confluencia == 1.0
    
    def test_calculate_final_signal_strong_buy(self, orchestrator):
        """Verifica señal final para STRONG_BUY"""
        analyses = [
            AnalysisResult("A", TradeSignal.STRONG_BUY, 0.8, 0.95),
        ]
        weights = {"A": 1.0}
        
        signal = orchestrator._calculate_final_signal(analyses, weights)
        assert signal == TradeSignal.STRONG_BUY
    
    def test_determine_direction_call(self, orchestrator):
        """Verifica dirección para señales alcistas"""
        direction = orchestrator._determine_direction(TradeSignal.BUY)
        assert direction == "CALL"
        
        direction = orchestrator._determine_direction(TradeSignal.STRONG_BUY)
        assert direction == "CALL"
    
    def test_determine_direction_put(self, orchestrator):
        """Verifica dirección para señales bajistas"""
        direction = orchestrator._determine_direction(TradeSignal.SELL)
        assert direction == "PUT"
        
        direction = orchestrator._determine_direction(TradeSignal.STRONG_SELL)
        assert direction == "PUT"
    
    def test_make_decision_insufficient_confluencia(self, orchestrator):
        """Verifica decisión con confluencia insuficiente"""
        orchestrator.config.min_confluencia_score = 0.9
        
        analyses = [
            AnalysisResult("A", TradeSignal.BUY, 0.5, 0.8),
            AnalysisResult("B", TradeSignal.SELL, 0.5, 0.8),
        ]
        weights = {"A": 0.5, "B": 0.5}
        
        decision = orchestrator.make_decision(
            asset="EURUSD",
            technical_analysis=analyses[0],
        )
        
        assert decision.can_trade == False


class TestTechnicalAnalyzer:
    """Tests para TechnicalAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def sample_prices(self):
        """Genera precios de prueba"""
        prices = [100]
        for i in range(99):
            prices.append(prices[-1] + (1 if i % 2 == 0 else -1))
        return prices
    
    def test_calculate_rsi(self, analyzer, sample_prices):
        """Verifica cálculo de RSI"""
        rsi = analyzer.calculate_rsi(sample_prices)
        assert 0 <= rsi <= 100
    
    def test_calculate_rsi_short_period(self, analyzer):
        """Verifica RSI con período muy corto"""
        prices = [100, 101, 102]
        rsi = analyzer.calculate_rsi(prices, period=14)
        assert rsi == 50.0  # Sin datos suficientes
    
    def test_calculate_macd(self, analyzer, sample_prices):
        """Verifica cálculo de MACD"""
        macd = analyzer.calculate_macd(sample_prices)
        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd
    
    def test_calculate_bollinger_bands(self, analyzer, sample_prices):
        """Verifica cálculo de Bollinger Bands"""
        bb = analyzer.calculate_bollinger_bands(sample_prices)
        assert bb["upper"] >= bb["middle"] >= bb["lower"]
        assert bb["width"] > 0
    
    def test_calculate_sma(self, analyzer):
        """Verifica cálculo de SMA"""
        prices = [100, 101, 102, 103, 104]
        sma = analyzer.calculate_sma(prices, period=3)
        expected = (102 + 103 + 104) / 3
        assert abs(sma - expected) < 0.01
    
    def test_analyze_technical(self, analyzer, sample_prices):
        """Verifica análisis técnico completo"""
        highs = [p + 1 for p in sample_prices]
        lows = [p - 1 for p in sample_prices]
        
        result = analyzer.analyze_technical(
            sample_prices, highs, lows, sample_prices
        )
        
        assert result.analyzer_name == "Technical"
        assert result.signal in [TradeSignal.BUY, TradeSignal.SELL, 
                                 TradeSignal.NEUTRAL, TradeSignal.NO_SIGNAL]
        assert 0 <= result.confidence <= 1


class TestVolatilityAnalyzer:
    """Tests para VolatilityRegimeAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return VolatilityRegimeAnalyzer()
    
    def test_calculate_volatility(self, analyzer):
        """Verifica cálculo de volatilidad"""
        prices = [100 + i for i in range(100)]
        volatility = analyzer.calculate_volatility(prices)
        assert volatility >= 0
    
    def test_get_volatility_level_very_low(self, analyzer):
        """Verifica detección de volatilidad muy baja"""
        vol_level = analyzer.get_volatility_level(0.0001, 5.0)
        assert vol_level == VolatilityLevel.VERY_LOW
    
    def test_get_volatility_level_extreme(self, analyzer):
        """Verifica detección de volatilidad extrema"""
        vol_level = analyzer.get_volatility_level(0.01, 95.0)
        assert vol_level == VolatilityLevel.EXTREME
    
    def test_detect_regime_uptrend(self, analyzer):
        """Verifica detección de tendencia alcista"""
        prices = [100 + i for i in range(100)]
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]
        
        regime = analyzer.detect_regime(prices, highs, lows, prices)
        assert regime in [MarketRegime.STRONG_TREND_UP, MarketRegime.WEAK_TREND_UP]
    
    def test_detect_breakout(self, analyzer):
        """Verifica detección de breakout"""
        prices = list(range(100, 120))
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]
        
        is_breakout = analyzer.detect_breakout(prices, highs, lows)
        assert isinstance(is_breakout, bool)
    
    def test_get_support_resistance(self, analyzer):
        """Verifica cálculo de soporte y resistencia"""
        highs = [100, 105, 110, 108, 109]
        lows = [95, 98, 102, 101, 103]
        
        support, resistance = analyzer.get_support_resistance(highs, lows, lookback=5)
        assert support == 95
        assert resistance == 110


# Ejecutar tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
