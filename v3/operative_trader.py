"""
SISTEMA DE OPERATIVA REAL v3 - El Corazón del Bot
Enfocado en: Ganar dinero, Aprender, Mejorar, Retroalimentarse
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from v2.utils.logger import get_logger


logger = get_logger()


class EntryQuality(Enum):
    """Calidad de la entrada (qué tan buena fue)"""
    EXCELLENT = "EXCELLENT"  # 90-100% confianza
    GOOD = "GOOD"            # 75-90%
    FAIR = "FAIR"            # 60-75%
    POOR = "POOR"            # 45-60%
    TERRIBLE = "TERRIBLE"    # < 45%


class ExitQuality(Enum):
    """Calidad de la salida"""
    PERFECT = "PERFECT"      # Salió en el mejor punto
    GOOD = "GOOD"            # Salió bien
    ACCEPTABLE = "ACCEPTABLE"
    MISSED = "MISSED"        # Perdió oportunidad
    TERRIBLE = "TERRIBLE"    # Peor salida posible


class TradeOutcome(Enum):
    """Resultado de la operación"""
    WIN = "WIN"              # Ganancia
    LOSS = "LOSS"            # Pérdida
    BREAKEVEN = "BREAKEVEN"  # Empate
    PARTIAL = "PARTIAL"      # Ganancia parcial


@dataclass
class TradeAnalysis:
    """Análisis detallado de una operación realizada"""
    
    # Identificación
    trade_id: str
    asset: str
    direction: str  # CALL o PUT
    timestamp: datetime
    
    # Entrada
    entry_price: float
    entry_time: datetime
    entry_confidence: float  # 0-1
    entry_reason: str  # Por qué entramos
    entry_signals: Dict[str, float]  # RSI, MACD, etc.
    entry_quality: EntryQuality
    
    # Salida
    exit_price: float
    exit_time: datetime
    exit_reason: str  # Por qué salimos
    exit_quality: ExitQuality
    
    # Resultado
    pnl: float
    pnl_percentage: float
    outcome: TradeOutcome
    duration_seconds: float
    
    # Análisis Post-Trade
    max_profit_opportunity: float  # Mejor ganancia posible
    max_loss_opportunity: float    # Peor pérdida posible
    profit_efficiency: float  # (pnl / max_profit_opportunity) * 100
    risk_reward_ratio: float  # Ganancia/Pérdida posible
    
    # Patrones Identificados
    pattern_type: str  # Tipo de patrón: "RSI_OVERSOLD", "MACD_CROSS", etc.
    market_condition: str  # Tendencia, sideways, volátil
    
    # Para Aprendizaje
    should_repeat: bool  # ¿Debería repetir este tipo de entrada?
    lessons_learned: List[str] = field(default_factory=list)
    
    def get_score(self) -> float:
        """Calcula score global de la operación (0-100)"""
        # Componentes del score:
        # - Entry quality (40%)
        # - Exit quality (40%)
        # - Profitability (20%)
        
        entry_scores = {
            EntryQuality.EXCELLENT: 100,
            EntryQuality.GOOD: 80,
            EntryQuality.FAIR: 60,
            EntryQuality.POOR: 40,
            EntryQuality.TERRIBLE: 20,
        }
        
        exit_scores = {
            ExitQuality.PERFECT: 100,
            ExitQuality.GOOD: 80,
            ExitQuality.ACCEPTABLE: 60,
            ExitQuality.MISSED: 30,
            ExitQuality.TERRIBLE: 10,
        }
        
        entry_score = entry_scores.get(self.entry_quality, 50)
        exit_score = exit_scores.get(self.exit_quality, 50)
        
        # Profit score
        if self.pnl > 0:
            profit_score = min(100, (self.profit_efficiency / 100) * 100)
        else:
            profit_score = max(0, 50 - (abs(self.pnl_percentage) * 10))
        
        # Score final ponderado
        score = (entry_score * 0.4) + (exit_score * 0.4) + (profit_score * 0.2)
        
        return score


@dataclass
class OperativeLearning:
    """Sistema de aprendizaje basado en operaciones reales"""
    
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    total_pnl: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    
    # Patrones ganadores identificados
    winning_patterns: Dict[str, int] = field(default_factory=dict)  # patrón -> count
    winning_pattern_scores: Dict[str, float] = field(default_factory=dict)  # patrón -> avg_score
    
    # Condiciones de mercado mejores
    best_market_conditions: Dict[str, int] = field(default_factory=dict)
    
    # Horarios mejores
    best_entry_hours: Dict[int, int] = field(default_factory=dict)
    
    # Activos que funcionan mejor
    best_assets: Dict[str, float] = field(default_factory=dict)  # asset -> winrate
    
    # Errores comunes
    common_mistakes: List[str] = field(default_factory=list)
    
    # Score de confianza del sistema
    system_confidence: float = 0.5
    
    @property
    def win_rate(self) -> float:
        """Porcentaje de trades ganadores"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def average_pnl(self) -> float:
        """PnL promedio por trade"""
        if self.total_trades == 0:
            return 0.0
        return self.total_pnl / self.total_trades
    
    @property
    def profit_factor(self) -> float:
        """Ganancia/Pérdida - debe ser > 1.0"""
        if self.total_loss == 0:
            return float('inf') if self.total_profit > 0 else 0.0
        return self.total_profit / abs(self.total_loss)


class OperativeTrader:
    """Sistema de trading operativo - ENFOCADO EN GANAR DINERO"""
    
    def __init__(self):
        self.trades_history: List[TradeAnalysis] = []
        self.learning = OperativeLearning()
        self.open_trade: Optional[TradeAnalysis] = None
        
        logger.info("OperativeTrader inicializado - Sistema de Operativa Real")
    
    def execute_entry(
        self,
        asset: str,
        direction: str,
        entry_price: float,
        confidence: float,
        reason: str,
        signals: Dict[str, float],
    ) -> str:
        """
        ENTRA en una operación
        
        Args:
            asset: Par de divisas
            direction: CALL o PUT
            entry_price: Precio de entrada
            confidence: Confianza 0-1
            reason: Por qué entramos
            signals: Indicadores técnicos
        
        Returns:
            trade_id para identificar la operación
        """
        trade_id = f"T_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Determinar calidad de entrada basado en confianza
        if confidence >= 0.9:
            entry_quality = EntryQuality.EXCELLENT
        elif confidence >= 0.75:
            entry_quality = EntryQuality.GOOD
        elif confidence >= 0.6:
            entry_quality = EntryQuality.FAIR
        elif confidence >= 0.45:
            entry_quality = EntryQuality.POOR
        else:
            entry_quality = EntryQuality.TERRIBLE
        
        # Crear trade
        self.open_trade = TradeAnalysis(
            trade_id=trade_id,
            asset=asset,
            direction=direction,
            timestamp=datetime.now(),
            entry_price=entry_price,
            entry_time=datetime.now(),
            entry_confidence=confidence,
            entry_reason=reason,
            entry_signals=signals,
            entry_quality=entry_quality,
            exit_price=0.0,
            exit_time=datetime.now(),
            exit_reason="",
            exit_quality=ExitQuality.GOOD,
            pnl=0.0,
            pnl_percentage=0.0,
            outcome=TradeOutcome.WIN,
            duration_seconds=0.0,
            max_profit_opportunity=0.0,
            max_loss_opportunity=0.0,
            profit_efficiency=0.0,
            risk_reward_ratio=0.0,
            pattern_type="",
            market_condition="",
            should_repeat=False,
        )
        
        logger.log_trade(
            asset=asset,
            direction=direction,
            entry=entry_price,
            exit=0.0,
            result="ENTRY",
            reason=reason,
            confidence=confidence,
        )
        
        return trade_id
    
    def execute_exit(
        self,
        exit_price: float,
        max_price_after_entry: float,
        min_price_after_entry: float,
        exit_reason: str,
    ) -> Optional[TradeAnalysis]:
        """
        SALE de la operación y la analiza
        
        Returns:
            TradeAnalysis completamente analizado
        """
        if self.open_trade is None:
            logger.warning("No hay trade abierto para cerrar")
            return None
        
        # Calcular resultado
        pnl = exit_price - self.open_trade.entry_price
        if self.open_trade.direction == "PUT":
            pnl = -pnl  # Invertir para PUT
        
        pnl_percentage = (pnl / self.open_trade.entry_price) * 100
        
        # Determinar outcome
        if pnl > 0:
            outcome = TradeOutcome.WIN
        elif pnl < 0:
            outcome = TradeOutcome.LOSS
        else:
            outcome = TradeOutcome.BREAKEVEN
        
        # Calcular oportunidades perdidas
        if self.open_trade.direction == "CALL":
            max_profit_opp = (max_price_after_entry - self.open_trade.entry_price)
            max_loss_opp = (self.open_trade.entry_price - min_price_after_entry)
        else:  # PUT
            max_profit_opp = (self.open_trade.entry_price - min_price_after_entry)
            max_loss_opp = (max_price_after_entry - self.open_trade.entry_price)
        
        # Calcular efficiency
        if max_profit_opp > 0:
            profit_efficiency = (pnl / max_profit_opp) * 100
        else:
            profit_efficiency = 0.0
        
        # Determinar calidad de salida
        if profit_efficiency >= 90:
            exit_quality = ExitQuality.PERFECT
        elif profit_efficiency >= 70:
            exit_quality = ExitQuality.GOOD
        elif profit_efficiency >= 50:
            exit_quality = ExitQuality.ACCEPTABLE
        elif profit_efficiency >= 20:
            exit_quality = ExitQuality.MISSED
        else:
            exit_quality = ExitQuality.TERRIBLE
        
        # Risk/Reward ratio
        if max_loss_opp > 0:
            risk_reward_ratio = max_profit_opp / max_loss_opp
        else:
            risk_reward_ratio = 0.0
        
        # Actualizar trade
        self.open_trade.exit_price = exit_price
        self.open_trade.exit_time = datetime.now()
        self.open_trade.exit_reason = exit_reason
        self.open_trade.exit_quality = exit_quality
        self.open_trade.pnl = pnl
        self.open_trade.pnl_percentage = pnl_percentage
        self.open_trade.outcome = outcome
        self.open_trade.duration_seconds = (
            self.open_trade.exit_time - self.open_trade.entry_time
        ).total_seconds()
        self.open_trade.max_profit_opportunity = max_profit_opp
        self.open_trade.max_loss_opportunity = max_loss_opp
        self.open_trade.profit_efficiency = profit_efficiency
        self.open_trade.risk_reward_ratio = risk_reward_ratio
        
        # Guardar en historial
        self.trades_history.append(self.open_trade)
        
        # Aprender de esta operación
        self._learn_from_trade(self.open_trade)
        
        logger.log_trade(
            asset=self.open_trade.asset,
            direction=self.open_trade.direction,
            entry=self.open_trade.entry_price,
            exit=exit_price,
            result=outcome.value,
            reason=exit_reason,
            confidence=self.open_trade.entry_confidence,
        )
        
        trade_closed = self.open_trade
        self.open_trade = None
        
        return trade_closed
    
    def _learn_from_trade(self, trade: TradeAnalysis):
        """
        APRENDE de la operación cerrada
        Actualiza patrones, condiciones, y ajusta estrategia
        """
        
        # Actualizar estadísticas
        self.learning.total_trades += 1
        self.learning.total_pnl += trade.pnl
        
        if trade.outcome == TradeOutcome.WIN:
            self.learning.winning_trades += 1
            self.learning.total_profit += trade.pnl
        else:
            self.learning.losing_trades += 1
            self.learning.total_loss += abs(trade.pnl)
        
        # Registrar patrones ganadores
        if trade.outcome == TradeOutcome.WIN:
            pattern_key = f"{trade.pattern_type}_{trade.direction}"
            
            if pattern_key not in self.learning.winning_patterns:
                self.learning.winning_patterns[pattern_key] = 0
                self.learning.winning_pattern_scores[pattern_key] = 0.0
            
            self.learning.winning_patterns[pattern_key] += 1
            score = trade.get_score()
            self.learning.winning_pattern_scores[pattern_key] = (
                (self.learning.winning_pattern_scores[pattern_key] * 
                 (self.learning.winning_patterns[pattern_key] - 1) + score) /
                self.learning.winning_patterns[pattern_key]
            )
            
            # Decidir si repetir este tipo de entrada
            if self.learning.winning_pattern_scores[pattern_key] >= 70:
                trade.should_repeat = True
                trade.lessons_learned.append(f"Patrón ganador: Repetir {pattern_key}")
        
        # Registrar condiciones de mercado
        condition_key = trade.market_condition
        if condition_key not in self.learning.best_market_conditions:
            self.learning.best_market_conditions[condition_key] = 0
        self.learning.best_market_conditions[condition_key] += 1
        
        # Registrar horarios
        hour = trade.entry_time.hour
        if hour not in self.learning.best_entry_hours:
            self.learning.best_entry_hours[hour] = 0
        if trade.outcome == TradeOutcome.WIN:
            self.learning.best_entry_hours[hour] += 1
        
        # Registrar activos
        if trade.asset not in self.learning.best_assets:
            self.learning.best_assets[trade.asset] = 0.0
        
        asset_trades = sum(1 for t in self.trades_history if t.asset == trade.asset)
        asset_wins = sum(1 for t in self.trades_history 
                        if t.asset == trade.asset and t.outcome == TradeOutcome.WIN)
        if asset_trades > 0:
            self.learning.best_assets[trade.asset] = (asset_wins / asset_trades) * 100
        
        # Actualizar confianza del sistema
        self._update_system_confidence()
        
        logger.info(
            f"Aprendizaje: Trade #{self.learning.total_trades} | "
            f"WR: {self.learning.win_rate:.1f}% | "
            f"PF: {self.learning.profit_factor:.2f} | "
            f"Confidence: {self.learning.system_confidence:.1%}"
        )
    
    def _update_system_confidence(self):
        """Actualiza confianza del sistema basado en performance"""
        if self.learning.total_trades < 10:
            # Menos de 10 trades, mantener confianza media
            self.learning.system_confidence = 0.5
            return
        
        # Factores:
        # - Win rate (40%)
        # - Profit factor (40%)
        # - Consistency (20%)
        
        win_rate_factor = (self.learning.win_rate / 100) * 0.4
        
        if self.learning.profit_factor > 0:
            pf_factor = min(1.0, self.learning.profit_factor / 2.0) * 0.4
        else:
            pf_factor = 0.0
        
        # Consistency: desviación estándar de retornos
        if len(self.trades_history) >= 5:
            recent_pnls = [t.pnl_percentage for t in self.trades_history[-5:]]
            consistency = 1.0 - (np.std(recent_pnls) / 10.0)
            consistency_factor = max(0, min(1.0, consistency)) * 0.2
        else:
            consistency_factor = 0.1
        
        self.learning.system_confidence = win_rate_factor + pf_factor + consistency_factor
    
    def get_best_patterns(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Obtiene los patrones ganadores más confiables"""
        sorted_patterns = sorted(
            self.learning.winning_pattern_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_patterns[:top_n]
    
    def get_best_conditions(self) -> Dict[str, float]:
        """Obtiene las mejores condiciones de mercado"""
        best_conditions = {}
        for condition, count in self.learning.best_market_conditions.items():
            wins = sum(1 for t in self.trades_history 
                      if t.market_condition == condition and t.outcome == TradeOutcome.WIN)
            if count > 0:
                best_conditions[condition] = (wins / count) * 100
        
        return dict(sorted(best_conditions.items(), key=lambda x: x[1], reverse=True))
    
    def should_focus_on_asset(self, asset: str) -> bool:
        """Determina si debería enfocarse en un activo específico"""
        if asset not in self.learning.best_assets:
            return False
        return self.learning.best_assets[asset] >= 55.0  # WR >= 55%
    
    def get_status(self) -> Dict:
        """Estado completo del sistema operativo"""
        return {
            "total_trades": self.learning.total_trades,
            "win_rate": f"{self.learning.win_rate:.1f}%",
            "profit_factor": f"{self.learning.profit_factor:.2f}",
            "total_pnl": f"${self.learning.total_pnl:.2f}",
            "average_pnl": f"${self.learning.average_pnl:.2f}",
            "system_confidence": f"{self.learning.system_confidence:.1%}",
            "best_patterns": self.get_best_patterns(3),
            "best_conditions": self.get_best_conditions(),
            "best_assets": sorted(
                self.learning.best_assets.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
        }
