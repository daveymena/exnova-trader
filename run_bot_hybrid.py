#!/usr/bin/env python3
"""
BOT HYBRID - Simula operaciones REALES con mercado realista
Basado en Exnova API pero sin necesidad de conectar (pre-producción)
Aprende continuamente y mejora estrategias
"""

import os
import sys
import time
import json
import logging
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'data' / 'bot_hybrid.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

# Config
EMAIL = os.getenv('EXNOVA_EMAIL')
PASSWORD = os.getenv('EXNOVA_PASSWORD')
CAPITAL_PER_TRADE = float(os.getenv('CAPITAL_PER_TRADE', 1.0))

DATA_DIR = Path(__file__).parent / "data" / "hybrid_trades"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSION_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
TRADES_FILE = DATA_DIR / f"trades_{SESSION_ID}.json"
PERFORMANCE_FILE = DATA_DIR / f"performance_{SESSION_ID}.json"
STRATEGY_FILE = DATA_DIR / "strategies.json"


class MarketSimulator:
    """Simula movimientos reales de mercado"""
    
    def __init__(self, asset: str):
        self.asset = asset
        self.prices = self._generate_price_history()
        self.current_idx = 0
        
        # Precio base para cada activo
        self.base_prices = {
            'EURUSD': 1.0950,
            'GBPUSD': 1.2750,
            'AUDUSD': 0.6750,
            'NZDUSD': 0.5850,
            'USDJPY': 149.50,
            'USDCAD': 1.3650,
        }
    
    def _generate_price_history(self) -> List[float]:
        """Genera histórico de precios realista"""
        base = self.base_prices.get(self.asset, 1.0)
        prices = [base]
        
        for _ in range(100):
            # Movimiento browniano geométrico
            change = np.random.normal(0, 0.001)
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        return prices
    
    def get_price(self) -> float:
        """Obtiene precio actual"""
        if self.current_idx >= len(self.prices):
            self.current_idx = 0
            self.prices = self._generate_price_history()
        
        price = self.prices[self.current_idx]
        self.current_idx += 1
        return price
    
    def get_price_range(self, seconds: int) -> Tuple[float, float, float]:
        """Obtiene rango de precios en N segundos"""
        start_price = self.get_price()
        prices = [start_price]
        
        for _ in range(max(1, seconds // 5)):
            prices.append(self.get_price())
        
        return min(prices), max(prices), prices[-1]


class TechnicalAnalyzer:
    """Analiza técnicamente el mercado"""
    
    @staticmethod
    def analyze_entry(asset: str, direction: str) -> Dict[str, float]:
        """Analiza si hay buena entrada"""
        signals = {}
        
        # RSI simulado
        rsi = random.uniform(20, 80)
        signals['rsi'] = rsi
        signals['rsi_oversold'] = 1.0 if rsi < 30 else 0.0
        signals['rsi_overbought'] = 1.0 if rsi > 70 else 0.0
        
        # MACD simulado
        macd = random.uniform(-2, 2)
        signals['macd'] = macd
        signals['macd_cross'] = 1.0 if abs(macd) < 0.1 else 0.0
        
        # Bollinger Bands simulado
        bb_pos = random.uniform(-1, 1)
        signals['bb_position'] = bb_pos
        signals['bb_reversion'] = 1.0 if abs(bb_pos) > 0.8 else 0.0
        
        # Trend
        trend = random.choice([-1, 0, 1])
        signals['trend'] = trend
        signals['trend_follow'] = 1.0 if trend == (1 if direction.upper() == 'CALL' else -1) else 0.0
        
        # Soporte/Resistencia
        support_bounce = random.uniform(0, 1)
        signals['support_bounce'] = support_bounce
        
        # Confluence (múltiples señales)
        confluence_count = sum([signals.get(k, 0) for k in ['rsi_oversold', 'macd_cross', 'bb_reversion']])
        signals['confluence'] = min(1.0, confluence_count / 3)
        
        return signals


class AdaptiveStrategy:
    """Estrategia que aprende y mejora"""
    
    def __init__(self):
        self.strategies = {
            'rsi_oversold': {'confidence': 0.60, 'wins': 0, 'losses': 0, 'enabled': True},
            'macd_cross': {'confidence': 0.55, 'wins': 0, 'losses': 0, 'enabled': True},
            'bollinger': {'confidence': 0.58, 'wins': 0, 'losses': 0, 'enabled': True},
            'support_bounce': {'confidence': 0.65, 'wins': 0, 'losses': 0, 'enabled': True},
            'confluence': {'confidence': 0.70, 'wins': 0, 'losses': 0, 'enabled': True},
            'trend_follow': {'confidence': 0.60, 'wins': 0, 'losses': 0, 'enabled': True},
        }
        self.load()
    
    def load(self):
        """Carga estrategias previas"""
        if STRATEGY_FILE.exists():
            try:
                with open(STRATEGY_FILE) as f:
                    saved = json.load(f)
                    self.strategies.update(saved)
                    logger.info("📚 Estrategias cargadas del historial")
            except:
                pass
    
    def save(self):
        """Guarda estrategias actuales"""
        with open(STRATEGY_FILE, 'w') as f:
            json.dump(self.strategies, f, indent=2)
    
    def select_best_strategy(self) -> str:
        """Selecciona mejor estrategia por confianza"""
        enabled = {k: v for k, v in self.strategies.items() if v['enabled']}
        if not enabled:
            # Si todas están deshabilitadas, habilitar la mejor
            best = max(self.strategies.items(), key=lambda x: x[1]['confidence'])
            best[1]['enabled'] = True
            return best[0]
        
        return max(enabled.items(), key=lambda x: x[1]['confidence'])[0]
    
    def update(self, strategy: str, outcome: str):
        """Actualiza confianza basado en resultado"""
        if strategy not in self.strategies:
            return
        
        strat = self.strategies[strategy]
        
        if outcome == 'WIN':
            strat['wins'] += 1
            strat['confidence'] = min(0.95, strat['confidence'] + 0.025)
            logger.info(f"🎯 {strategy} WIN: Conf={strat['confidence']:.1%} (W:{strat['wins']} L:{strat['losses']})")
        else:
            strat['losses'] += 1
            strat['confidence'] = max(0.05, strat['confidence'] - 0.04)
            logger.info(f"📉 {strategy} LOSS: Conf={strat['confidence']:.1%} (W:{strat['wins']} L:{strat['losses']})")
        
        # Deshabilitar estrategias con muy baja confianza
        if strat['confidence'] < 0.15 and (strat['wins'] + strat['losses']) > 5:
            strat['enabled'] = False
            logger.warning(f"🚫 {strategy} deshabilitada (baja confianza)")
        
        self.save()
    
    def print_status(self):
        """Imprime estado de estrategias"""
        print("\n📊 ESTADO DE ESTRATEGIAS:")
        print("─" * 70)
        for name, data in sorted(self.strategies.items(), key=lambda x: x[1]['confidence'], reverse=True):
            total = data['wins'] + data['losses']
            wr = (data['wins'] / total * 100) if total > 0 else 0
            status = "✓" if data['enabled'] else "✗"
            bar = "█" * int(data['confidence'] * 20) + "░" * (20 - int(data['confidence'] * 20))
            print(f"{status} {name:.<20} {bar} {data['confidence']:>5.1%} | W:{data['wins']:>2} L:{data['losses']:>2} | WR:{wr:>5.1f}%")


class HybridTradingBot:
    """Bot híbrido que opera con mercado simulado realista"""
    
    def __init__(self):
        self.strategy_manager = AdaptiveStrategy()
        self.analyzer = TechnicalAnalyzer()
        self.trades = []
        self.session_pnl = 0.0
        self.session_wins = 0
        self.session_losses = 0
        self.session_start = datetime.now()
        self.max_consecutive_losses = 0
        self.current_consecutive_losses = 0
    
    def execute_trade(self, asset: str, direction: str, strategy: str, signals: Dict) -> Dict:
        """Ejecuta un trade individual"""
        
        logger.info(f"📍 Trade: {asset} {direction} usando {strategy}")
        
        # Precio de entrada
        market = MarketSimulator(asset)
        entry_price = market.get_price()
        
        # Simular operación por 60 segundos
        low_price, high_price, exit_price = market.get_price_range(60)
        
        # Determinar resultado basado en dirección
        if direction.upper() == 'CALL':
            is_win = exit_price > entry_price
        else:  # PUT
            is_win = exit_price < entry_price
        
        # Ajustar probabilidad basada en confianza de estrategia
        confidence = self.strategy_manager.strategies[strategy]['confidence']
        
        # Si tenemos baja confianza, reducir probabilidad de ganar
        if random.random() > confidence:
            is_win = not is_win
        
        # Calcular PnL
        if is_win:
            # Ganancia: 50-95% del capital
            pnl = CAPITAL_PER_TRADE * random.uniform(0.50, 0.95)
            outcome = 'WIN'
            self.session_wins += 1
            self.current_consecutive_losses = 0
        else:
            # Pérdida: 100% del capital
            pnl = -CAPITAL_PER_TRADE
            outcome = 'LOSS'
            self.session_losses += 1
            self.current_consecutive_losses += 1
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.current_consecutive_losses)
        
        # Calcular eficiencia
        if is_win:
            potential_profit = abs(high_price - entry_price) / entry_price * 100
            actual_profit = pnl / CAPITAL_PER_TRADE * 100
            efficiency = min(100, (actual_profit / potential_profit * 100)) if potential_profit > 0 else 0
        else:
            efficiency = 0
        
        # Construir registro de trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'asset': asset,
            'direction': direction,
            'strategy': strategy,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'outcome': outcome,
            'pnl': pnl,
            'efficiency': efficiency,
            'signals': signals,
            'strategy_confidence': confidence,
        }
        
        # Actualizar estado
        self.trades.append(trade_record)
        self.session_pnl += pnl
        
        # Actualizar estrategia
        self.strategy_manager.update(strategy, outcome)
        
        # Imprimir resultado
        symbol = "✅" if outcome == 'WIN' else "❌"
        print(f"{symbol} {asset} {direction} | PnL: ${pnl:+.2f} | Eff: {efficiency:.0f}% | {strategy}")
        
        # Guardar trade
        with open(TRADES_FILE, 'a') as f:
            f.write(json.dumps(trade_record) + '\n')
        
        return trade_record
    
    def check_risk_limits(self) -> bool:
        """Verifica límites de riesgo"""
        if self.current_consecutive_losses >= 5:
            logger.warning("⚠️  Alcanzado máximo de pérdidas consecutivas")
            return False
        
        if self.session_pnl < -50.0:
            logger.warning("⚠️  Alcanzado límite de pérdida del día")
            return False
        
        return True
    
    def run_session(self, num_trades: int = 15):
        """Ejecuta sesión de trading"""
        
        print("\n" + "="*70)
        print("🚀 SESIÓN DE TRADING ADAPTATIVO - BOT HÍBRIDO")
        print("="*70)
        print(f"📧 Cuenta: {EMAIL}")
        print(f"💼 Modo: PRACTICE (simulación realista)")
        print(f"💰 Capital por trade: ${CAPITAL_PER_TRADE}")
        print(f"📊 Trades a ejecutar: {num_trades}")
        print("="*70 + "\n")
        
        assets = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD']
        trades_executed = 0
        
        while trades_executed < num_trades and self.check_risk_limits():
            # Seleccionar estrategia
            strategy = self.strategy_manager.select_best_strategy()
            
            # Analizar mercado
            asset = random.choice(assets)
            direction = random.choice(['CALL', 'PUT'])
            signals = self.analyzer.analyze_entry(asset, direction)
            
            # Ejecutar trade
            self.execute_trade(asset, direction, strategy, signals)
            
            trades_executed += 1
            
            # Descanso
            if trades_executed < num_trades:
                time.sleep(0.5)
        
        self._print_session_report()
    
    def _print_session_report(self):
        """Imprime reporte de sesión"""
        
        if not self.trades:
            print("❌ No hay trades para reportar")
            return
        
        total = len(self.trades)
        win_rate = (self.session_wins / total * 100) if total > 0 else 0
        
        # Profit factor
        total_wins = sum(t['pnl'] for t in self.trades if t['outcome'] == 'WIN')
        total_losses = abs(sum(t['pnl'] for t in self.trades if t['outcome'] == 'LOSS'))
        pf = total_wins / total_losses if total_losses > 0 else (float('inf') if total_wins > 0 else 0)
        
        # Drawdown
        running_pnl = 0
        peak = 0
        max_dd = 0
        for trade in self.trades:
            running_pnl += trade['pnl']
            if running_pnl > peak:
                peak = running_pnl
            else:
                dd = peak - running_pnl
                max_dd = max(max_dd, dd)
        
        elapsed = datetime.now() - self.session_start
        roi = (self.session_pnl / (CAPITAL_PER_TRADE * total) * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print("📊 REPORTE DE SESIÓN")
        print("="*70)
        print(f"  Duración:............................. {elapsed}")
        print(f"  Total trades:......................... {total}")
        print(f"  Ganadas:.............................. {self.session_wins}")
        print(f"  Perdidas:............................ {self.session_losses}")
        print(f"  Win Rate:............................ {win_rate:.1f}%")
        print(f"  PnL Total:........................... ${self.session_pnl:+.2f}")
        print(f"  Profit Factor:...................... {pf:.2f}")
        print(f"  Max Drawdown:....................... -${max_dd:.2f}")
        print(f"  Max Consecutive Losses:............ {self.max_consecutive_losses}")
        print(f"  ROI:................................ {roi:.2f}%")
        print("="*70)
        
        # Evaluación
        print(f"\n🎯 EVALUACIÓN:")
        if win_rate >= 65 and roi > 40:
            print("  ✅ EXCELENTE: Altamente rentable y consistente")
        elif win_rate >= 60 and roi > 25:
            print("  ✅ MUY BUENO: Consistentemente rentable")
        elif win_rate >= 55 and roi > 15:
            print("  ✅ BUENO: Rentable con margen de mejora")
        else:
            print("  ⚠️  REQUIERE MEJORA: Rentabilidad insuficiente")
        
        # Mostrar estrategias
        self.strategy_manager.print_status()
        
        # Guardar performance
        perf = {
            'timestamp': datetime.now().isoformat(),
            'duration': str(elapsed),
            'total_trades': total,
            'wins': self.session_wins,
            'losses': self.session_losses,
            'win_rate': f"{win_rate:.1f}%",
            'pnl': f"${self.session_pnl:+.2f}",
            'roi': f"{roi:.2f}%",
            'profit_factor': f"{pf:.2f}",
            'max_drawdown': f"-${max_dd:.2f}",
            'max_consecutive_losses': self.max_consecutive_losses,
        }
        
        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(perf, f, indent=2)
        
        print(f"\n✅ Datos guardados:")
        print(f"  • Trades: {TRADES_FILE}")
        print(f"  • Performance: {PERFORMANCE_FILE}")
        print(f"  • Estrategias: {STRATEGY_FILE}")


def main():
    try:
        bot = HybridTradingBot()
        bot.run_session(num_trades=20)
        print("\n✅ ¡Sesión completada!\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Sesión interrumpida\n")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
