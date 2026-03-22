"""
Gestor de Riesgos Mejorado - v2
Controla y limita la exposición de capital
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
from v2.config.settings import TradingConfig
from v2.utils.logger import get_logger


logger = get_logger()


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Position:
    """Representa una posición abierta"""
    asset: str
    direction: str  # "CALL" o "PUT"
    entry_price: float
    amount: float
    entry_time: datetime
    expiration_time: datetime
    martingale_level: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() >= self.expiration_time
    
    @property
    def time_elapsed(self) -> float:
        return (datetime.now() - self.entry_time).total_seconds()


@dataclass
class DailyStats:
    """Estadísticas diarias"""
    date: str
    trades_count: int = 0
    wins: int = 0
    losses: int = 0
    profit: float = 0.0
    loss_amount: float = 0.0
    consecutive_losses: int = 0
    last_trade_time: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        if self.trades_count == 0:
            return 0.0
        return (self.wins / self.trades_count) * 100
    
    @property
    def daily_net(self) -> float:
        return self.profit - self.loss_amount


class RiskManager:
    """Gestor centralizado de riesgos"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.positions: List[Position] = []
        self.daily_stats = self._init_daily_stats()
        self.hourly_trades: dict = {}  # hour -> count
        self.last_trade_time: Optional[datetime] = None
        
        logger.info("RiskManager inicializado")
    
    def _init_daily_stats(self) -> DailyStats:
        """Inicializa estadísticas del día"""
        today = datetime.now().strftime("%Y-%m-%d")
        return DailyStats(date=today)
    
    def _reset_daily_if_needed(self):
        """Reinicia estadísticas diarias si es un nuevo día"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_stats.date != today:
            logger.info(f"Reseteando estadísticas diarias. Nuevo día: {today}")
            self.daily_stats = self._init_daily_stats()
            self.hourly_trades = {}
    
    def check_daily_loss_limit(self) -> bool:
        """Verifica si se ha alcanzado el límite de pérdidas diarias"""
        self._reset_daily_if_needed()
        
        if self.daily_stats.loss_amount >= self.config.max_daily_loss:
            logger.warning(
                f"Límite de pérdidas diarias alcanzado: ${self.daily_stats.loss_amount:.2f}"
            )
            return False
        
        return True
    
    def check_daily_trade_limit(self) -> bool:
        """Verifica si se ha alcanzado el límite diario de trades"""
        self._reset_daily_if_needed()
        
        if self.daily_stats.trades_count >= self.config.max_daily_trades:
            logger.warning(
                f"Límite diario de trades alcanzado: {self.daily_stats.trades_count}"
            )
            return False
        
        return True
    
    def check_consecutive_losses(self) -> bool:
        """Verifica si hay demasiadas pérdidas consecutivas"""
        if self.daily_stats.consecutive_losses >= self.config.max_consecutive_losses:
            logger.warning(
                f"Límite de pérdidas consecutivas alcanzado: {self.daily_stats.consecutive_losses}"
            )
            return False
        
        return True
    
    def check_hourly_limit(self) -> bool:
        """Verifica límite de trades por hora"""
        current_hour = datetime.now().hour
        
        if current_hour not in self.hourly_trades:
            self.hourly_trades[current_hour] = 0
        
        if self.hourly_trades[current_hour] >= self.config.max_hourly_trades:
            logger.warning(
                f"Límite de trades por hora alcanzado: {self.hourly_trades[current_hour]}"
            )
            return False
        
        return True
    
    def check_trade_interval(self) -> bool:
        """Verifica intervalo mínimo entre trades"""
        if self.last_trade_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_trade_time).total_seconds()
        
        if elapsed < self.config.min_trade_interval:
            logger.debug(f"Intervalo entre trades insuficiente: {elapsed:.1f}s")
            return False
        
        return True
    
    def check_simultaneous_positions(self) -> bool:
        """Verifica límite de posiciones simultáneas"""
        active_positions = [p for p in self.positions if not p.is_expired]
        
        if len(active_positions) >= self.config.max_simultaneous_positions:
            logger.debug(
                f"Límite de posiciones simultáneas alcanzado: {len(active_positions)}"
            )
            return False
        
        return True
    
    def check_all_preconditions(self) -> tuple[bool, str]:
        """Verifica todas las precondiciones antes de ejecutar un trade"""
        self._reset_daily_if_needed()
        
        if not self.check_daily_loss_limit():
            return False, "Límite de pérdidas diarias alcanzado"
        
        if not self.check_daily_trade_limit():
            return False, "Límite diario de trades alcanzado"
        
        if not self.check_consecutive_losses():
            return False, "Demasiadas pérdidas consecutivas"
        
        if not self.check_hourly_limit():
            return False, "Límite de trades por hora alcanzado"
        
        if not self.check_trade_interval():
            return False, "Intervalo mínimo entre trades no cumplido"
        
        if not self.check_simultaneous_positions():
            return False, "Límite de posiciones simultáneas alcanzado"
        
        return True, "Precondiciones cumplidas"
    
    def calculate_trade_amount(self, consecutive_losses: Optional[int] = None) -> float:
        """Calcula el monto de la operación considerando martingala"""
        if not self.config.use_martingale or consecutive_losses is None:
            return self.config.capital_per_trade
        
        # Limitar Martingala a max_steps
        martingale_level = min(consecutive_losses, self.config.martingale_max_steps)
        
        # Calcular monto: capital * (multiplier ^ level)
        amount = self.config.capital_per_trade * (self.config.martingale_multiplier ** martingale_level)
        
        # Asegurar límite máximo de exposición
        max_exposure = self.config.capital_per_trade * (self.config.martingale_multiplier ** self.config.martingale_max_steps)
        
        if amount > max_exposure:
            logger.warning(f"Monto de Martingala excede límite. Usando máximo: ${max_exposure:.2f}")
            amount = max_exposure
        
        return amount
    
    def open_position(self, asset: str, direction: str, amount: float, 
                     entry_price: float, expiration_seconds: int) -> Position:
        """Abre una nueva posición"""
        entry_time = datetime.now()
        expiration_time = entry_time + timedelta(seconds=expiration_seconds)
        
        position = Position(
            asset=asset,
            direction=direction,
            entry_price=entry_price,
            amount=amount,
            entry_time=entry_time,
            expiration_time=expiration_time,
            martingale_level=len([p for p in self.positions 
                                if p.asset == asset and 
                                   self.daily_stats.consecutive_losses > 0])
        )
        
        self.positions.append(position)
        self.last_trade_time = entry_time
        
        current_hour = entry_time.hour
        if current_hour not in self.hourly_trades:
            self.hourly_trades[current_hour] = 0
        self.hourly_trades[current_hour] += 1
        
        logger.log_trade(
            asset=asset,
            direction=direction,
            entry=entry_price,
            exit=0.0,
            result="OPEN",
            reason="Nueva posición abierta",
            confidence=0.0
        )
        
        return position
    
    def close_position(self, position: Position, exit_price: float, 
                      result: str, pnl: float):
        """Cierra una posición"""
        if position in self.positions:
            self.positions.remove(position)
        
        # Actualizar estadísticas
        self.daily_stats.trades_count += 1
        
        if result == "WIN":
            self.daily_stats.wins += 1
            self.daily_stats.profit += pnl
            self.daily_stats.consecutive_losses = 0
            logger.info(f"GANANCIA en {position.asset}: +${pnl:.2f}")
        
        elif result == "LOSS":
            self.daily_stats.losses += 1
            self.daily_stats.loss_amount += abs(pnl)
            self.daily_stats.consecutive_losses += 1
            logger.warning(f"PÉRDIDA en {position.asset}: -${abs(pnl):.2f}")
        
        logger.log_trade(
            asset=position.asset,
            direction=position.direction,
            entry=position.entry_price,
            exit=exit_price,
            result=result,
            reason=f"Posición cerrada. PnL: ${pnl:.2f}",
            confidence=abs(pnl / position.amount)
        )
    
    def get_risk_level(self) -> RiskLevel:
        """Determina el nivel de riesgo actual"""
        self._reset_daily_if_needed()
        
        loss_ratio = self.daily_stats.loss_amount / self.config.max_daily_loss if self.config.max_daily_loss > 0 else 0
        
        if loss_ratio >= 0.9:
            return RiskLevel.CRITICAL
        elif loss_ratio >= 0.7:
            return RiskLevel.HIGH
        elif loss_ratio >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_status(self) -> dict:
        """Retorna estado actual del gestor de riesgos"""
        self._reset_daily_if_needed()
        
        active_positions = [p for p in self.positions if not p.is_expired]
        
        return {
            "daily_trades": self.daily_stats.trades_count,
            "daily_wins": self.daily_stats.wins,
            "daily_losses": self.daily_stats.losses,
            "daily_win_rate": self.daily_stats.win_rate,
            "daily_profit": self.daily_stats.profit,
            "daily_loss": self.daily_stats.loss_amount,
            "consecutive_losses": self.daily_stats.consecutive_losses,
            "active_positions": len(active_positions),
            "risk_level": self.get_risk_level().value,
        }
