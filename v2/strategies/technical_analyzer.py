"""
Analizador Técnico Mejorado - v2
Calcula indicadores técnicos con análisis confluente
"""

from typing import List, Optional, Dict
import numpy as np
from enum import Enum
from v2.core.orchestrator import TradeSignal, AnalysisResult
from v2.utils.logger import get_logger


logger = get_logger()


class TechnicalIndicatorType(Enum):
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER = "BOLLINGER"
    SMA = "SMA"
    EMA = "EMA"
    ATR = "ATR"
    STOCHASTIC = "STOCHASTIC"


class TechnicalAnalyzer:
    """Analiza indicadores técnicos y genera señales"""
    
    def __init__(self, rsi_period: int = 14, macd_fast: int = 12,
                 macd_slow: int = 26, bb_period: int = 20,
                 sma_short: int = 20, sma_long: int = 50):
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.bb_period = bb_period
        self.sma_short = sma_short
        self.sma_long = sma_long
    
    def calculate_rsi(self, prices: List[float], period: int = None) -> float:
        """Calcula RSI (Relative Strength Index)"""
        if period is None:
            period = self.rsi_period
        
        if len(prices) < period + 1:
            return 50.0
        
        prices = np.array(prices[-period-1:])
        changes = np.diff(prices)
        
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calcula MACD (Moving Average Convergence Divergence)"""
        if len(prices) < self.macd_slow + 1:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
        prices = np.array(prices)
        
        # Calcular EMAs
        ema_fast = self._calculate_ema(prices, self.macd_fast)
        ema_slow = self._calculate_ema(prices, self.macd_slow)
        
        # MACD
        macd = ema_fast - ema_slow
        
        # Signal line (EMA de 9 del MACD)
        if len(prices) < self.macd_slow + 9:
            signal = 0.0
        else:
            # Recalcular MACD para todos los puntos
            macd_line = []
            for i in range(self.macd_slow - 1, len(prices)):
                ema_f = self._calculate_ema(prices[:i+1], self.macd_fast)
                ema_s = self._calculate_ema(prices[:i+1], self.macd_slow)
                macd_line.append(ema_f - ema_s)
            
            if len(macd_line) > 8:
                signal = self._calculate_ema(np.array(macd_line[-9:]), 9)
            else:
                signal = macd
        
        histogram = macd - signal
        
        return {
            "macd": float(macd),
            "signal": float(signal),
            "histogram": float(histogram),
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = None,
                                 std_dev: float = 2.0) -> Dict[str, float]:
        """Calcula Bandas de Bollinger"""
        if period is None:
            period = self.bb_period
        
        if len(prices) < period:
            return {"upper": 0.0, "middle": 0.0, "lower": 0.0, "width": 0.0}
        
        prices = np.array(prices[-period:])
        
        middle = np.mean(prices)
        std = np.std(prices)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        width = upper - lower
        
        return {
            "upper": float(upper),
            "middle": float(middle),
            "lower": float(lower),
            "width": float(width),
        }
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Calcula SMA (Simple Moving Average)"""
        if len(prices) < period:
            return np.mean(prices)
        
        return float(np.mean(prices[-period:]))
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calcula EMA (Exponential Moving Average)"""
        return self._calculate_ema(np.array(prices), period)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Cálculo interno de EMA"""
        if len(prices) < period:
            return float(np.mean(prices))
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return float(ema)
    
    def calculate_stochastic(self, highs: List[float], lows: List[float],
                           closes: List[float], period: int = 14) -> Dict[str, float]:
        """Calcula Oscilador Estocástico"""
        if len(highs) < period or len(lows) < period or len(closes) < period:
            return {"k": 50.0, "d": 50.0}
        
        highs_arr = np.array(highs[-period:])
        lows_arr = np.array(lows[-period:])
        
        highest_high = np.max(highs_arr)
        lowest_low = np.min(lows_arr)
        
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            k = 50.0
        else:
            k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # D es el SMA de 3 períodos de K
        d = k  # Simplificado para eficiencia
        
        return {
            "k": float(k),
            "d": float(d),
        }
    
    def analyze_technical(self, prices: List[float], highs: List[float],
                         lows: List[float], close_prices: List[float]) -> AnalysisResult:
        """
        Análisis técnico completo con confluencia
        """
        if not prices or not highs or not lows:
            return AnalysisResult(
                analyzer_name="Technical",
                signal=TradeSignal.NO_SIGNAL,
                score=0.0,
                confidence=0.0,
            )
        
        # Calcular indicadores
        rsi = self.calculate_rsi(prices)
        macd = self.calculate_macd(prices)
        bb = self.calculate_bollinger_bands(prices)
        sma_short = self.calculate_sma(prices, self.sma_short)
        sma_long = self.calculate_sma(prices, self.sma_long)
        stoch = self.calculate_stochastic(highs, lows, close_prices)
        
        current_price = prices[-1]
        
        # Contar señales
        signals = 0
        signal_strength = 0.0
        reasoning = []
        
        # Análisis RSI
        if rsi < 30:
            signals += 1
            signal_strength += 1.0
            reasoning.append("RSI oversold (compra)")
        elif rsi > 70:
            signals -= 1
            signal_strength -= 1.0
            reasoning.append("RSI overbought (venta)")
        
        # Análisis MACD
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            signals += 1
            signal_strength += 0.7
            reasoning.append("MACD bullish")
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            signals -= 1
            signal_strength -= 0.7
            reasoning.append("MACD bearish")
        
        # Análisis Bollinger
        if current_price < bb["lower"]:
            signals += 1
            signal_strength += 0.8
            reasoning.append("Precio en banda baja (reversión)")
        elif current_price > bb["upper"]:
            signals -= 1
            signal_strength -= 0.8
            reasoning.append("Precio en banda alta (reversión)")
        
        # Análisis SMA
        if current_price > sma_short and sma_short > sma_long:
            signals += 0.5
            signal_strength += 0.5
            reasoning.append("SMA alcista")
        elif current_price < sma_short and sma_short < sma_long:
            signals -= 0.5
            signal_strength -= 0.5
            reasoning.append("SMA bajista")
        
        # Análisis Estocástico
        if stoch["k"] < 20:
            signals += 0.7
            signal_strength += 0.5
            reasoning.append("Estocástico oversold")
        elif stoch["k"] > 80:
            signals -= 0.7
            signal_strength -= 0.5
            reasoning.append("Estocástico overbought")
        
        # Determinar señal
        if signal_strength > 1.5:
            trade_signal = TradeSignal.STRONG_BUY
            confidence = min(1.0, abs(signal_strength) / 4.0)
        elif signal_strength > 0.5:
            trade_signal = TradeSignal.BUY
            confidence = min(1.0, abs(signal_strength) / 3.0)
        elif signal_strength < -1.5:
            trade_signal = TradeSignal.STRONG_SELL
            confidence = min(1.0, abs(signal_strength) / 4.0)
        elif signal_strength < -0.5:
            trade_signal = TradeSignal.SELL
            confidence = min(1.0, abs(signal_strength) / 3.0)
        else:
            trade_signal = TradeSignal.NEUTRAL
            confidence = 0.5
        
        indicators = {
            "rsi": rsi,
            "macd": macd["macd"],
            "macd_signal": macd["signal"],
            "bb_upper": bb["upper"],
            "bb_lower": bb["lower"],
            "sma_short": sma_short,
            "sma_long": sma_long,
            "stoch_k": stoch["k"],
            "price": current_price,
        }
        
        return AnalysisResult(
            analyzer_name="Technical",
            signal=trade_signal,
            score=abs(signal_strength) / 4.0,
            confidence=confidence,
            indicators=indicators,
            reasoning=" | ".join(reasoning) if reasoning else "Sin señal clara",
        )
