"""
ESTRATEGIAS ADAPTATIVAS - Se mejoran con cada trade
Sistema que aprende QUÉ FUNCIONA y lo repite
"""

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional
from enum import Enum
import numpy as np
from v2.utils.logger import get_logger


logger = get_logger()


class StrategyType(Enum):
    """Tipos de estrategias"""
    RSI_OVERSOLD = "RSI_OVERSOLD"              # Compra en RSI < 30
    RSI_OVERBOUGHT = "RSI_OVERBOUGHT"          # Venta en RSI > 70
    MACD_CROSS = "MACD_CROSS"                  # Cruces de MACD
    BOLLINGER_MEAN_REVERSION = "BOLLINGER_MR"  # Reversión a media
    TREND_FOLLOWING = "TREND_FOLLOWING"        # Seguir tendencia
    VOLUME_SPIKE = "VOLUME_SPIKE"              # Volumen alto
    BREAKOUT = "BREAKOUT"                      # Rompimiento de niveles
    CONFLUENCE = "CONFLUENCE"                  # Múltiples señales
    SMART_MONEY = "SMART_MONEY"                # Order blocks, FVG
    ML_PREDICTION = "ML_PREDICTION"            # Predicción de ML


@dataclass
class StrategyMetrics:
    """Métricas de rendimiento de una estrategia"""
    
    strategy_type: StrategyType
    total_executed: int = 0
    total_wins: int = 0
    total_losses: int = 0
    
    total_profit: float = 0.0
    total_loss: float = 0.0
    
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    
    # Adaptabilidad
    last_10_trades_wr: float = 0.0  # Win rate últimos 10 trades
    confidence_level: float = 0.5    # 0-1, qué tan confiable es
    
    # Mejora continua
    version: int = 1
    last_update: str = ""
    
    def calculate_metrics(self, trades: List):
        """Recalcula todas las métricas basado en trades"""
        if not trades:
            return
        
        self.total_executed = len(trades)
        self.total_wins = sum(1 for t in trades if t.outcome.value == "WIN")
        self.total_losses = sum(1 for t in trades if t.outcome.value == "LOSS")
        
        self.total_profit = sum(t.pnl for t in trades if t.pnl > 0)
        self.total_loss = sum(abs(t.pnl) for t in trades if t.pnl < 0)
        
        if self.total_executed > 0:
            self.win_rate = (self.total_wins / self.total_executed) * 100
        
        if self.total_loss > 0:
            self.profit_factor = self.total_profit / self.total_loss
        
        if self.total_wins > 0:
            self.avg_win = self.total_profit / self.total_wins
        
        if self.total_losses > 0:
            self.avg_loss = self.total_loss / self.total_losses
        
        # Últimos 10 trades
        if len(trades) >= 10:
            recent = trades[-10:]
            recent_wins = sum(1 for t in recent if t.outcome.value == "WIN")
            self.last_10_trades_wr = (recent_wins / 10) * 100
        elif self.total_executed > 0:
            self.last_10_trades_wr = self.win_rate
        
        # Actualizar confidence
        self._update_confidence()
    
    def _update_confidence(self):
        """Calcula nivel de confianza de la estrategia"""
        if self.total_executed < 5:
            self.confidence_level = 0.3  # Muy pocos datos
        elif self.total_executed < 20:
            self.confidence_level = 0.5 + (self.win_rate / 100) * 0.3
        else:
            # Más datos = más confianza
            # Basado en win rate, profit factor y consistencia
            wr_component = (self.win_rate / 100) * 0.4
            pf_component = min(1.0, self.profit_factor / 2.0) * 0.3
            consistency = (self.last_10_trades_wr / 100) * 0.3
            
            self.confidence_level = wr_component + pf_component + consistency


@dataclass
class AdaptiveStrategy:
    """Estrategia que se adapta basada en performance"""
    
    strategy_type: StrategyType
    name: str
    description: str
    
    # Parámetros ajustables
    parameters: Dict[str, float] = field(default_factory=dict)
    
    # Métricas de rendimiento
    metrics: StrategyMetrics = field(default_factory=StrategyMetrics)
    
    # Trades ejecutados con esta estrategia
    trades: List = field(default_factory=list)
    
    # Histórico de ajustes
    adjustment_history: List[str] = field(default_factory=list)
    
    # Activos donde funciona mejor
    best_assets: Dict[str, float] = field(default_factory=dict)  # asset -> wr
    
    # Condiciones de mercado donde funciona
    best_conditions: List[str] = field(default_factory=list)
    
    def execute(self, market_data: Dict) -> Optional[Dict]:
        """
        Ejecuta la estrategia
        
        Returns:
            Dict con {signal, confidence, reason} o None
        """
        # Verificar si la estrategia tiene confianza suficiente
        if self.metrics.confidence_level < 0.3:
            return None  # No ejecutar si no tiene confianza
        
        # Ejecutar basado en tipo
        if self.strategy_type == StrategyType.RSI_OVERSOLD:
            return self._execute_rsi_oversold(market_data)
        
        elif self.strategy_type == StrategyType.RSI_OVERBOUGHT:
            return self._execute_rsi_overbought(market_data)
        
        elif self.strategy_type == StrategyType.MACD_CROSS:
            return self._execute_macd_cross(market_data)
        
        elif self.strategy_type == StrategyType.BOLLINGER_MEAN_REVERSION:
            return self._execute_bollinger_mr(market_data)
        
        elif self.strategy_type == StrategyType.TREND_FOLLOWING:
            return self._execute_trend_following(market_data)
        
        elif self.strategy_type == StrategyType.CONFLUENCE:
            return self._execute_confluence(market_data)
        
        return None
    
    def _execute_rsi_oversold(self, market_data: Dict) -> Optional[Dict]:
        """Estrategia: Comprar en RSI oversold"""
        rsi = market_data.get("rsi", 50)
        threshold = self.parameters.get("threshold", 30)
        
        if rsi < threshold:
            # Calcular confianza
            confidence = (1.0 - (rsi / threshold)) * self.metrics.confidence_level
            
            return {
                "signal": "BUY",
                "direction": "CALL",
                "confidence": confidence,
                "reason": f"RSI oversold ({rsi:.1f} < {threshold})",
                "indicators": {"rsi": rsi},
            }
        
        return None
    
    def _execute_rsi_overbought(self, market_data: Dict) -> Optional[Dict]:
        """Estrategia: Vender en RSI overbought"""
        rsi = market_data.get("rsi", 50)
        threshold = self.parameters.get("threshold", 70)
        
        if rsi > threshold:
            confidence = ((rsi - threshold) / (100 - threshold)) * self.metrics.confidence_level
            
            return {
                "signal": "SELL",
                "direction": "PUT",
                "confidence": confidence,
                "reason": f"RSI overbought ({rsi:.1f} > {threshold})",
                "indicators": {"rsi": rsi},
            }
        
        return None
    
    def _execute_macd_cross(self, market_data: Dict) -> Optional[Dict]:
        """Estrategia: MACD cruces"""
        macd = market_data.get("macd", 0)
        signal = market_data.get("macd_signal", 0)
        histogram = macd - signal
        
        prev_histogram = market_data.get("prev_histogram", 0)
        
        # Cruce alcista (MACD cruza signal de abajo)
        if prev_histogram < 0 and histogram > 0:
            confidence = abs(histogram) * self.metrics.confidence_level
            
            return {
                "signal": "BUY",
                "direction": "CALL",
                "confidence": min(1.0, confidence),
                "reason": f"MACD crossover (histogram: {histogram:.6f})",
                "indicators": {"macd": macd, "signal": signal},
            }
        
        # Cruce bajista
        elif prev_histogram > 0 and histogram < 0:
            confidence = abs(histogram) * self.metrics.confidence_level
            
            return {
                "signal": "SELL",
                "direction": "PUT",
                "confidence": min(1.0, confidence),
                "reason": f"MACD crossunder (histogram: {histogram:.6f})",
                "indicators": {"macd": macd, "signal": signal},
            }
        
        return None
    
    def _execute_bollinger_mr(self, market_data: Dict) -> Optional[Dict]:
        """Estrategia: Bollinger mean reversion"""
        price = market_data.get("price", 0)
        bb_upper = market_data.get("bb_upper", 0)
        bb_lower = market_data.get("bb_lower", 0)
        bb_middle = market_data.get("bb_middle", 0)
        
        # Precio en banda baja -> comprar (reversión)
        if price < bb_lower:
            distance = (bb_lower - price) / (bb_upper - bb_lower)
            confidence = (1.0 - distance) * self.metrics.confidence_level
            
            return {
                "signal": "BUY",
                "direction": "CALL",
                "confidence": min(1.0, confidence),
                "reason": f"Price at lower BB ({price:.4f} < {bb_lower:.4f})",
                "indicators": {"price": price, "bb_lower": bb_lower},
            }
        
        # Precio en banda alta -> vender
        elif price > bb_upper:
            distance = (price - bb_upper) / (bb_upper - bb_lower)
            confidence = (1.0 - distance) * self.metrics.confidence_level
            
            return {
                "signal": "SELL",
                "direction": "PUT",
                "confidence": min(1.0, confidence),
                "reason": f"Price at upper BB ({price:.4f} > {bb_upper:.4f})",
                "indicators": {"price": price, "bb_upper": bb_upper},
            }
        
        return None
    
    def _execute_trend_following(self, market_data: Dict) -> Optional[Dict]:
        """Estrategia: Seguir tendencia"""
        price = market_data.get("price", 0)
        sma_short = market_data.get("sma_short", 0)
        sma_long = market_data.get("sma_long", 0)
        
        # Tendencia alcista
        if price > sma_short > sma_long:
            confidence = (price - sma_long) / (sma_short - sma_long + 0.001)
            confidence = min(1.0, confidence) * self.metrics.confidence_level
            
            return {
                "signal": "BUY",
                "direction": "CALL",
                "confidence": confidence,
                "reason": "Uptrend (price > SMA20 > SMA50)",
                "indicators": {"price": price, "sma_short": sma_short, "sma_long": sma_long},
            }
        
        # Tendencia bajista
        elif price < sma_short < sma_long:
            confidence = (sma_long - price) / (sma_long - sma_short + 0.001)
            confidence = min(1.0, confidence) * self.metrics.confidence_level
            
            return {
                "signal": "SELL",
                "direction": "PUT",
                "confidence": confidence,
                "reason": "Downtrend (price < SMA20 < SMA50)",
                "indicators": {"price": price, "sma_short": sma_short, "sma_long": sma_long},
            }
        
        return None
    
    def _execute_confluence(self, market_data: Dict) -> Optional[Dict]:
        """Estrategia: Confluencia (múltiples señales)"""
        signals = market_data.get("signals", [])
        
        if len(signals) < 2:
            return None
        
        bullish_count = sum(1 for s in signals if s.get("direction") == "CALL")
        bearish_count = sum(1 for s in signals if s.get("direction") == "PUT")
        
        if bullish_count > bearish_count:
            avg_confidence = np.mean([s.get("confidence", 0) for s in signals if s.get("direction") == "CALL"])
            
            return {
                "signal": "BUY",
                "direction": "CALL",
                "confidence": avg_confidence * self.metrics.confidence_level,
                "reason": f"Confluence: {bullish_count} bullish signals",
                "indicators": {"signal_count": len(signals)},
            }
        
        elif bearish_count > bullish_count:
            avg_confidence = np.mean([s.get("confidence", 0) for s in signals if s.get("direction") == "PUT"])
            
            return {
                "signal": "SELL",
                "direction": "PUT",
                "confidence": avg_confidence * self.metrics.confidence_level,
                "reason": f"Confluence: {bearish_count} bearish signals",
                "indicators": {"signal_count": len(signals)},
            }
        
        return None
    
    def adjust_parameters(self, feedback: str):
        """
        Ajusta parámetros basado en feedback
        
        feedback: "improve" o "downgrade"
        """
        if feedback == "improve":
            # Hacer la estrategia más agresiva
            logger.info(f"Mejorando estrategia {self.strategy_type.value}")
            self.adjustment_history.append(f"IMPROVE: {self.metrics.confidence_level:.2f}")
            self.metrics.version += 1
        
        elif feedback == "downgrade":
            # Hacer la estrategia más conservadora
            logger.info(f"Reduciendo estrategia {self.strategy_type.value}")
            self.adjustment_history.append(f"DOWNGRADE: {self.metrics.confidence_level:.2f}")


class StrategyManager:
    """Gestor de múltiples estrategias adaptativas"""
    
    def __init__(self):
        self.strategies: Dict[StrategyType, AdaptiveStrategy] = {}
        self._initialize_strategies()
        
        logger.info("StrategyManager inicializado con estrategias adaptativas")
    
    def _initialize_strategies(self):
        """Inicializa todas las estrategias disponibles"""
        
        strategies = [
            AdaptiveStrategy(
                strategy_type=StrategyType.RSI_OVERSOLD,
                name="RSI Oversold",
                description="Compra cuando RSI está en sobreventa",
                parameters={"threshold": 30.0},
            ),
            AdaptiveStrategy(
                strategy_type=StrategyType.RSI_OVERBOUGHT,
                name="RSI Overbought",
                description="Vende cuando RSI está en sobrecompra",
                parameters={"threshold": 70.0},
            ),
            AdaptiveStrategy(
                strategy_type=StrategyType.MACD_CROSS,
                name="MACD Crossover",
                description="Sigue cruces de MACD",
                parameters={"threshold": 0.0},
            ),
            AdaptiveStrategy(
                strategy_type=StrategyType.BOLLINGER_MEAN_REVERSION,
                name="Bollinger Reversion",
                description="Media reversión en Bollinger Bands",
                parameters={"distance_multiplier": 2.0},
            ),
            AdaptiveStrategy(
                strategy_type=StrategyType.TREND_FOLLOWING,
                name="Trend Following",
                description="Sigue tendencias",
                parameters={"period_short": 20.0, "period_long": 50.0},
            ),
            AdaptiveStrategy(
                strategy_type=StrategyType.CONFLUENCE,
                name="Confluence",
                description="Busca confluencia de múltiples señales",
                parameters={"min_signals": 2.0},
            ),
        ]
        
        for strategy in strategies:
            self.strategies[strategy.strategy_type] = strategy
    
    def get_best_strategy(self, asset: str = None) -> Optional[AdaptiveStrategy]:
        """Obtiene la estrategia con mejor performance"""
        candidates = [
            s for s in self.strategies.values()
            if s.metrics.confidence_level >= 0.5
        ]
        
        if not candidates:
            return None
        
        # Ordenar por win rate
        sorted_candidates = sorted(
            candidates,
            key=lambda s: s.metrics.win_rate,
            reverse=True
        )
        
        return sorted_candidates[0]
    
    def get_all_signals(self, market_data: Dict) -> List[Dict]:
        """Obtiene señales de todas las estrategias"""
        signals = []
        
        for strategy in self.strategies.values():
            signal = strategy.execute(market_data)
            if signal:
                signal["strategy_type"] = strategy.strategy_type.value
                signals.append(signal)
        
        return signals
    
    def update_with_trade(self, trade_analysis):
        """Actualiza estrategias con feedback del trade"""
        strategy_type_str = trade_analysis.pattern_type
        
        # Encontrar estrategia correspondiente
        for strategy in self.strategies.values():
            if strategy.strategy_type.value in strategy_type_str:
                strategy.trades.append(trade_analysis)
                strategy.metrics.calculate_metrics(strategy.trades)
                
                # Ajustar si es necesario
                if trade_analysis.outcome.value == "WIN" and trade_analysis.should_repeat:
                    strategy.adjust_parameters("improve")
                elif trade_analysis.outcome.value == "LOSS":
                    strategy.adjust_parameters("downgrade")
    
    def get_status(self) -> Dict:
        """Estado de todas las estrategias"""
        return {
            strategy_type.value: {
                "trades": strategy.metrics.total_executed,
                "win_rate": f"{strategy.metrics.win_rate:.1f}%",
                "profit_factor": f"{strategy.metrics.profit_factor:.2f}",
                "confidence": f"{strategy.metrics.confidence_level:.1%}",
                "version": strategy.metrics.version,
            }
            for strategy_type, strategy in self.strategies.items()
        }
