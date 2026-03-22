"""
SISTEMA DE REPORTES Y MÉTRICAS - Análisis Detallado
Evaluación completa de cada aspecto del trading
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from v2.utils.logger import get_logger


logger = get_logger()


@dataclass
class DailyReport:
    """Reporte diario de trading"""
    
    date: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    
    total_pnl: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    
    best_trade_pnl: float = 0.0
    worst_trade_pnl: float = 0.0
    
    longest_win_streak: int = 0
    longest_loss_streak: int = 0
    
    best_asset: str = ""
    worst_asset: str = ""
    
    best_strategy: str = ""
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def profit_factor(self) -> float:
        if self.total_loss == 0:
            return float('inf') if self.total_profit > 0 else 0.0
        return self.total_profit / self.total_loss
    
    def __str__(self) -> str:
        return f"""
═══════════════════════════════════════════════════════════════
📅 REPORTE DIARIO - {self.date}
═══════════════════════════════════════════════════════════════

📊 RESUMEN:
  • Total de trades:        {self.total_trades}
  • Ganados:                {self.winning_trades} ({self.win_rate:.1f}%)
  • Perdidos:               {self.losing_trades}
  • Empates:                {self.breakeven_trades}

💰 RESULTADO FINANCIERO:
  • PnL Total:              ${self.total_pnl:+.2f}
  • Ganancias:              ${self.total_profit:.2f}
  • Pérdidas:               ${-self.total_loss:.2f}
  • Profit Factor:          {self.profit_factor:.2f}

📈 EXTREMOS:
  • Mejor trade:            ${self.best_trade_pnl:+.2f}
  • Peor trade:             ${self.worst_trade_pnl:.2f}
  • Mayor racha ganadora:   {self.longest_win_streak}
  • Mayor racha perdedora:  {self.longest_loss_streak}

🎯 ASSETS Y ESTRATEGIAS:
  • Mejor asset:            {self.best_asset}
  • Peor asset:             {self.worst_asset}
  • Mejor estrategia:       {self.best_strategy}

═══════════════════════════════════════════════════════════════
"""


@dataclass
class WeeklyReport:
    """Reporte semanal de trading"""
    
    week_start: str
    week_end: str
    
    daily_reports: List[DailyReport]
    
    @property
    def total_trades(self) -> int:
        return sum(d.total_trades for d in self.daily_reports)
    
    @property
    def total_pnl(self) -> float:
        return sum(d.total_pnl for d in self.daily_reports)
    
    @property
    def win_rate(self) -> float:
        total_wins = sum(d.winning_trades for d in self.daily_reports)
        total = self.total_trades
        if total == 0:
            return 0.0
        return (total_wins / total) * 100
    
    @property
    def profit_factor(self) -> float:
        total_profit = sum(d.total_profit for d in self.daily_reports)
        total_loss = sum(d.total_loss for d in self.daily_reports)
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0
        return total_profit / total_loss
    
    def __str__(self) -> str:
        return f"""
═══════════════════════════════════════════════════════════════
📆 REPORTE SEMANAL - {self.week_start} a {self.week_end}
═══════════════════════════════════════════════════════════════

📊 RESUMEN SEMANAL:
  • Total de trades:        {self.total_trades}
  • Win Rate:               {self.win_rate:.1f}%
  • Profit Factor:          {self.profit_factor:.2f}
  • PnL Total:              ${self.total_pnl:+,.2f}

📈 ANÁLISIS DIARIO:
"""


class MetricsCalculator:
    """Calcula métricas detalladas de trading"""
    
    @staticmethod
    def calculate_drawdown(trades_pnls: List[float]) -> Dict:
        """Calcula máximo drawdown y características"""
        if not trades_pnls:
            return {"max_drawdown": 0.0, "current_drawdown": 0.0}
        
        cumulative_pnl = np.cumsum(trades_pnls)
        
        # Máximo drawdown
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = (cumulative_pnl - running_max) / (running_max + 0.01)
        
        max_drawdown = np.min(drawdown)
        current_drawdown = drawdown[-1]
        
        return {
            "max_drawdown": max_drawdown,
            "current_drawdown": current_drawdown,
            "max_drawdown_percent": abs(max_drawdown) * 100,
        }
    
    @staticmethod
    def calculate_sharpe_ratio(trades_pnls: List[float], risk_free_rate: float = 0.0) -> float:
        """Calcula Sharpe Ratio (riesgo ajustado)"""
        if len(trades_pnls) < 2:
            return 0.0
        
        returns = np.array(trades_pnls)
        excess_returns = returns - risk_free_rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns)
    
    @staticmethod
    def calculate_sortino_ratio(trades_pnls: List[float], target_return: float = 0.0) -> float:
        """Calcula Sortino Ratio (solo mira riesgo bajista)"""
        if len(trades_pnls) < 2:
            return 0.0
        
        returns = np.array(trades_pnls) - target_return
        
        # Solo desviación de retornos negativos
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = np.std(downside_returns)
        
        if downside_std == 0:
            return 0.0
        
        return np.mean(returns) / downside_std
    
    @staticmethod
    def calculate_recovery_factor(total_pnl: float, max_drawdown: float) -> float:
        """Recovery Factor = Total Profit / |Max Drawdown|"""
        if max_drawdown == 0:
            return float('inf') if total_pnl > 0 else 0.0
        return total_pnl / abs(max_drawdown)
    
    @staticmethod
    def analyze_winning_trades(trades: List) -> Dict:
        """Analiza características de trades ganadores"""
        winning_trades = [t for t in trades if t.outcome.value == "WIN"]
        
        if not winning_trades:
            return {}
        
        durations = [t.duration_seconds for t in winning_trades]
        pnls = [t.pnl for t in winning_trades]
        efficiencies = [t.profit_efficiency for t in winning_trades]
        
        return {
            "count": len(winning_trades),
            "avg_pnl": np.mean(pnls),
            "avg_duration": np.mean(durations),
            "avg_efficiency": np.mean(efficiencies),
            "max_pnl": np.max(pnls),
            "min_pnl": np.min(pnls),
        }
    
    @staticmethod
    def analyze_losing_trades(trades: List) -> Dict:
        """Analiza características de trades perdedores"""
        losing_trades = [t for t in trades if t.outcome.value == "LOSS"]
        
        if not losing_trades:
            return {}
        
        durations = [t.duration_seconds for t in losing_trades]
        pnls = [abs(t.pnl) for t in losing_trades]
        efficiencies = [abs(t.profit_efficiency) for t in losing_trades]
        
        return {
            "count": len(losing_trades),
            "avg_loss": np.mean(pnls),
            "avg_duration": np.mean(durations),
            "avg_efficiency": np.mean(efficiencies),
            "max_loss": np.max(pnls),
            "min_loss": np.min(pnls),
        }
    
    @staticmethod
    def identify_best_hours(trades: List) -> Dict[int, float]:
        """Identifica mejores horas para tradar"""
        best_hours = {}
        
        for hour in range(24):
            hour_trades = [t for t in trades if t.entry_time.hour == hour]
            
            if not hour_trades:
                continue
            
            wins = sum(1 for t in hour_trades if t.outcome.value == "WIN")
            wr = (wins / len(hour_trades)) * 100
            best_hours[hour] = wr
        
        return best_hours
    
    @staticmethod
    def identify_best_assets(trades: List) -> Dict[str, Dict]:
        """Identifica mejores activos"""
        asset_stats = {}
        
        for trade in trades:
            if trade.asset not in asset_stats:
                asset_stats[trade.asset] = {
                    "total": 0,
                    "wins": 0,
                    "total_pnl": 0.0,
                }
            
            asset_stats[trade.asset]["total"] += 1
            asset_stats[trade.asset]["total_pnl"] += trade.pnl
            
            if trade.outcome.value == "WIN":
                asset_stats[trade.asset]["wins"] += 1
        
        # Calcular win rate para cada asset
        for asset, stats in asset_stats.items():
            stats["win_rate"] = (stats["wins"] / stats["total"]) * 100
        
        return asset_stats


class ComprehensiveReport:
    """Reporte completo y detallado de performance"""
    
    def __init__(self, trades: List, operative_learning):
        self.trades = trades
        self.learning = operative_learning
    
    def generate_comprehensive_report(self) -> str:
        """Genera reporte completo en formato legible"""
        
        if not self.trades:
            return "No hay trades para reportar"
        
        # Calcular métricas
        pnls = [t.pnl for t in self.trades]
        
        drawdown_data = MetricsCalculator.calculate_drawdown(pnls)
        sharpe = MetricsCalculator.calculate_sharpe_ratio(pnls)
        sortino = MetricsCalculator.calculate_sortino_ratio(pnls)
        recovery = MetricsCalculator.recovery_factor(
            sum(pnls), 
            drawdown_data.get("max_drawdown", 0) * 100
        )
        
        winning_analysis = MetricsCalculator.analyze_winning_trades(self.trades)
        losing_analysis = MetricsCalculator.analyze_losing_trades(self.trades)
        
        best_hours = MetricsCalculator.identify_best_hours(self.trades)
        best_assets = MetricsCalculator.identify_best_assets(self.trades)
        
        best_patterns = self.learning.get_best_patterns(5) if hasattr(self.learning, 'get_best_patterns') else []
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    📊 REPORTE COMPLETO DE TRADING - v3                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📈 ESTADÍSTICAS GENERALES
{'─' * 80}
  Total de Trades:               {len(self.trades)}
  Trades Ganadores:              {self.learning.winning_trades} ({self.learning.win_rate:.1f}%)
  Trades Perdedores:             {self.learning.losing_trades}
  PnL Total:                     ${self.learning.total_pnl:+,.2f}
  Profit Factor:                 {self.learning.profit_factor:.2f}
  Promedio por Trade:            ${self.learning.average_pnl:+.2f}

💰 ANÁLISIS FINANCIERO
{'─' * 80}
  Ganancias Totales:             ${self.learning.total_profit:,.2f}
  Pérdidas Totales:              ${self.learning.total_loss:,.2f}
  Drawdown Máximo:               {drawdown_data.get('max_drawdown_percent', 0):.2f}%
  Sharpe Ratio:                  {sharpe:.2f}
  Sortino Ratio:                 {sortino:.2f}
  Recovery Factor:               {recovery:.2f}

🎯 TRADES GANADORES
{'─' * 80}
  Cantidad:                      {winning_analysis.get('count', 0)}
  Promedio de Ganancia:          ${winning_analysis.get('avg_pnl', 0):+.2f}
  Máxima Ganancia:               ${winning_analysis.get('max_pnl', 0):+.2f}
  Eficiencia Promedio:           {winning_analysis.get('avg_efficiency', 0):.1f}%
  Duración Promedio:             {winning_analysis.get('avg_duration', 0):.0f}s

❌ TRADES PERDEDORES
{'─' * 80}
  Cantidad:                      {losing_analysis.get('count', 0)}
  Promedio de Pérdida:           ${losing_analysis.get('avg_loss', 0):.2f}
  Pérdida Máxima:                ${losing_analysis.get('max_loss', 0):.2f}
  Duración Promedio:             {losing_analysis.get('avg_duration', 0):.0f}s

⏰ MEJORES HORAS PARA TRADAR
{'─' * 80}
{self._format_best_hours(best_hours)}

💎 MEJORES ACTIVOS
{'─' * 80}
{self._format_best_assets(best_assets)}

🏆 PATRONES GANADORES IDENTIFICADOS
{'─' * 80}
{self._format_best_patterns(best_patterns)}

📊 NIVEL DE CONFIANZA DEL SISTEMA
{'─' * 80}
  Confianza Actual:              {self.learning.system_confidence:.1%}
  Recomendación:                 {self._get_recommendation()}

╚═══════════════════════════════════════════════════════════════════════════════╝
"""
        return report
    
    def _format_best_hours(self, best_hours: Dict[int, float]) -> str:
        """Formatea horas en formato legible"""
        if not best_hours:
            return "  Sin datos suficientes"
        
        sorted_hours = sorted(best_hours.items(), key=lambda x: x[1], reverse=True)[:5]
        
        lines = []
        for hour, wr in sorted_hours:
            lines.append(f"  {hour:02d}:00 - {hour+1:02d}:00    WR: {wr:.1f}%")
        
        return "\n".join(lines)
    
    def _format_best_assets(self, best_assets: Dict[str, Dict]) -> str:
        """Formatea activos en formato legible"""
        if not best_assets:
            return "  Sin datos suficientes"
        
        sorted_assets = sorted(
            best_assets.items(),
            key=lambda x: x[1].get('win_rate', 0),
            reverse=True
        )[:5]
        
        lines = []
        for asset, stats in sorted_assets:
            lines.append(
                f"  {asset:<12} | WR: {stats['win_rate']:5.1f}% | "
                f"Trades: {stats['total']:3d} | PnL: ${stats['total_pnl']:+7.2f}"
            )
        
        return "\n".join(lines)
    
    def _format_best_patterns(self, best_patterns: List[tuple]) -> str:
        """Formatea patrones ganadores"""
        if not best_patterns:
            return "  Sin patrones identificados aún"
        
        lines = []
        for pattern, score in best_patterns:
            lines.append(f"  {pattern:<30} | Score: {score:.1f}%")
        
        return "\n".join(lines)
    
    def _get_recommendation(self) -> str:
        """Da recomendación basada en performance"""
        if self.learning.system_confidence >= 0.8:
            return "✅ Sistema muy confiable - Aumentar tamaño de posición"
        elif self.learning.system_confidence >= 0.6:
            return "✓ Sistema confiable - Mantener tamaño actual"
        elif self.learning.system_confidence >= 0.4:
            return "⚠ Sistema moderado - Ser más selectivo"
        else:
            return "❌ Sistema poco confiable - Estudiar más patrones"
