"""
Analizador de Volatilidad y Detección de Régimen de Mercado
Identifica el estado del mercado para mejorar la toma de decisiones
"""

from typing import List, Optional
from enum import Enum
import numpy as np
from v2.utils.logger import get_logger


logger = get_logger()


class MarketRegime(Enum):
    """Regímenes de mercado"""
    STRONG_TREND_UP = "STRONG_TREND_UP"
    WEAK_TREND_UP = "WEAK_TREND_UP"
    SIDEWAYS = "SIDEWAYS"
    WEAK_TREND_DOWN = "WEAK_TREND_DOWN"
    STRONG_TREND_DOWN = "STRONG_TREND_DOWN"
    CHOPPY = "CHOPPY"  # Mercado chop
    BREAKOUT = "BREAKOUT"  # Rompimiento esperado
    RANGING = "RANGING"  # Rango establecido


class VolatilityLevel(Enum):
    """Niveles de volatilidad"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    EXTREME = "EXTREME"


class VolatilityRegimeAnalyzer:
    """Analiza volatilidad y régimen del mercado"""
    
    def __init__(self, lookback_periods: int = 100):
        self.lookback_periods = lookback_periods
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """
        Calcula volatilidad histórica usando desviación estándar de retornos
        """
        if len(prices) < 2:
            return 0.0
        
        prices = np.array(prices[-self.lookback_periods:])
        
        # Calcular retornos logarítmicos
        returns = np.diff(np.log(prices))
        
        # Volatilidad = desviación estándar de retornos
        volatility = np.std(returns)
        
        return float(volatility)
    
    def calculate_atr(self, highs: List[float], lows: List[float], 
                     closes: List[float], period: int = 14) -> float:
        """
        Calcula Average True Range (ATR)
        """
        if len(highs) < period or len(lows) < period or len(closes) < period:
            return 0.0
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        
        # Calcular True Range
        tr1 = highs - lows
        tr2 = np.abs(highs - np.roll(closes, 1))
        tr3 = np.abs(lows - np.roll(closes, 1))
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # ATR es el promedio móvil del True Range
        atr = np.mean(tr[-period:])
        
        return float(atr)
    
    def calculate_volatility_percentile(self, prices: List[float], 
                                       period: int = 100) -> float:
        """
        Calcula volatilidad como percentil
        (0-100, donde 100 = volatilidad más alta del período)
        """
        if len(prices) < period:
            return 50.0
        
        # Calcular volatilidad móvil
        volatilities = []
        prices = np.array(prices[-period:])
        
        for i in range(1, len(prices)):
            window = prices[max(0, i - 20):i+1]
            if len(window) > 1:
                vol = np.std(np.diff(np.log(window)))
                volatilities.append(vol)
        
        if not volatilities:
            return 50.0
        
        current_vol = np.std(np.diff(np.log(prices[-20:])))
        
        # Calcular percentil
        percentile = (np.sum(np.array(volatilities) <= current_vol) / len(volatilities)) * 100
        
        return float(percentile)
    
    def get_volatility_level(self, volatility: float, 
                            volatility_percentile: float) -> VolatilityLevel:
        """
        Determina el nivel de volatilidad
        """
        if volatility_percentile < 10 or volatility < 0.0005:
            return VolatilityLevel.VERY_LOW
        elif volatility_percentile < 25 or volatility < 0.001:
            return VolatilityLevel.LOW
        elif volatility_percentile < 50 or volatility < 0.002:
            return VolatilityLevel.NORMAL
        elif volatility_percentile < 75 or volatility < 0.004:
            return VolatilityLevel.HIGH
        elif volatility_percentile < 90 or volatility < 0.007:
            return VolatilityLevel.VERY_HIGH
        else:
            return VolatilityLevel.EXTREME
    
    def detect_regime(self, prices: List[float], highs: List[float],
                     lows: List[float], close_prices: List[float],
                     sma_short: int = 20, sma_long: int = 50) -> MarketRegime:
        """
        Detecta el régimen de mercado usando múltiples indicadores
        """
        if len(prices) < sma_long:
            return MarketRegime.SIDEWAYS
        
        prices = np.array(prices)
        
        # Calcular promedios móviles
        sma_20 = np.mean(prices[-sma_short:])
        sma_50 = np.mean(prices[-sma_long:])
        
        # Calcular tendencia
        price_change = (prices[-1] - prices[0]) / prices[0]
        atr = self.calculate_atr(highs, lows, close_prices)
        
        # Calcular rango (para sideways detection)
        high_20 = np.max(prices[-sma_short:])
        low_20 = np.min(prices[-sma_short:])
        range_20 = (high_20 - low_20) / np.mean(prices[-sma_short:])
        
        # Lógica de detección de régimen
        if sma_20 > sma_50:
            # Tendencia alcista
            if price_change > 0.02:  # > 2%
                return MarketRegime.STRONG_TREND_UP
            elif range_20 < 0.005:  # Muy poco rango
                return MarketRegime.SIDEWAYS
            else:
                return MarketRegime.WEAK_TREND_UP
        
        elif sma_20 < sma_50:
            # Tendencia bajista
            if price_change < -0.02:  # < -2%
                return MarketRegime.STRONG_TREND_DOWN
            elif range_20 < 0.005:
                return MarketRegime.SIDEWAYS
            else:
                return MarketRegime.WEAK_TREND_DOWN
        
        else:
            # Presencia similar de SMA
            if range_20 > 0.01:
                return MarketRegime.CHOPPY
            else:
                return MarketRegime.SIDEWAYS
    
    def detect_breakout(self, prices: List[float], highs: List[float],
                       lows: List[float], lookback: int = 20,
                       threshold: float = 0.7) -> bool:
        """
        Detecta probabilidad de rompimiento
        threshold (0-1): qué tan alto debe ser el % del rango al límite superior/inferior
        """
        if len(prices) < lookback:
            return False
        
        prices = np.array(prices[-lookback:])
        highs_lookback = np.array(highs[-lookback:])
        lows_lookback = np.array(lows[-lookback:])
        
        high = np.max(highs_lookback)
        low = np.min(lows_lookback)
        current_price = prices[-1]
        
        range_val = high - low
        
        if range_val == 0:
            return False
        
        # Posición del precio en el rango
        price_position = (current_price - low) / range_val
        
        # Si está en los extremos del rango, hay probabilidad de rompimiento
        return price_position > threshold or price_position < (1 - threshold)
    
    def is_trending(self, prices: List[float], strength_threshold: float = 0.3) -> bool:
        """
        Determina si hay una tendencia clara
        strength_threshold: qué tan fuerte debe ser la tendencia (0-1)
        """
        if len(prices) < 10:
            return False
        
        prices = np.array(prices[-30:])
        
        # Ajustar línea de regresión
        x = np.arange(len(prices))
        coefficients = np.polyfit(x, prices, 1)
        slope = coefficients[0]
        
        # Calcular fuerza de la tendencia
        mean_price = np.mean(prices)
        trend_strength = abs(slope * len(prices)) / mean_price
        
        return trend_strength > strength_threshold
    
    def get_support_resistance(self, highs: List[float], lows: List[float],
                              lookback: int = 50) -> tuple[float, float]:
        """
        Calcula niveles de soporte y resistencia
        """
        if len(highs) < lookback or len(lows) < lookback:
            return 0.0, 0.0
        
        resistance = np.max(highs[-lookback:])
        support = np.min(lows[-lookback:])
        
        return support, resistance
    
    def calculate_price_position_ratio(self, price: float, support: float,
                                      resistance: float) -> float:
        """
        Calcula posición del precio entre soporte y resistencia
        0.0 = precio en soporte
        0.5 = precio en el medio
        1.0 = precio en resistencia
        """
        if resistance == support:
            return 0.5
        
        ratio = (price - support) / (resistance - support)
        return max(0.0, min(1.0, ratio))
    
    def get_analysis(self, prices: List[float], highs: List[float],
                    lows: List[float], close_prices: List[float]) -> dict:
        """
        Retorna análisis completo de volatilidad y régimen
        """
        volatility = self.calculate_volatility(prices)
        volatility_pct = self.calculate_volatility_percentile(prices)
        vol_level = self.get_volatility_level(volatility, volatility_pct)
        regime = self.detect_regime(prices, highs, lows, close_prices)
        is_breakout = self.detect_breakout(prices, highs, lows)
        is_trend = self.is_trending(prices)
        support, resistance = self.get_support_resistance(highs, lows)
        atr = self.calculate_atr(highs, lows, close_prices)
        
        if len(prices) > 0:
            price_ratio = self.calculate_price_position_ratio(
                prices[-1], support, resistance
            )
        else:
            price_ratio = 0.5
        
        return {
            "volatility": volatility,
            "volatility_percentile": volatility_pct,
            "volatility_level": vol_level.value,
            "regime": regime.value,
            "is_breakout": is_breakout,
            "is_trending": is_trend,
            "support": support,
            "resistance": resistance,
            "atr": atr,
            "price_position_ratio": price_ratio,
        }
