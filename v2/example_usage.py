"""
Ejemplo de uso del Trading Bot v2
Demuestra cómo usar los componentes principales
"""

from config.settings import Settings
from core.risk_manager import RiskManager
from core.orchestrator import TradingOrchestrator, TradeSignal
from strategies.technical_analyzer import TechnicalAnalyzer
from strategies.volatility_analyzer import VolatilityRegimeAnalyzer
from utils.logger import get_logger
import numpy as np


def generate_sample_data(length: int = 100) -> tuple:
    """Genera datos de ejemplo para demostración"""
    prices = [100]
    for _ in range(length - 1):
        change = np.random.randn() * 0.5
        prices.append(prices[-1] * (1 + change / 100))
    
    prices = np.array(prices)
    highs = prices * (1 + np.abs(np.random.randn(length) * 0.01))
    lows = prices * (1 - np.abs(np.random.randn(length) * 0.01))
    
    return list(prices), list(highs), list(lows), list(prices)


def main():
    """Función principal de ejemplo"""
    
    # 1. Cargar configuración
    print("\n" + "="*60)
    print("TRADING BOT v2 - EJEMPLO DE USO")
    print("="*60 + "\n")
    
    try:
        settings = Settings.from_env()
        logger = get_logger()
        
        logger.info("Configuración cargada correctamente")
        print(f"✓ Broker: {settings.broker.account_type.value}")
        print(f"✓ Capital por trade: ${settings.trading.capital_per_trade}")
        print(f"✓ Martingala: {'Habilitada' if settings.trading.use_martingale else 'Deshabilitada'}")
        
    except Exception as e:
        print(f"✗ Error cargando configuración: {e}")
        return
    
    # 2. Inicializar componentes
    print("\n" + "-"*60)
    print("INICIALIZANDO COMPONENTES")
    print("-"*60 + "\n")
    
    risk_manager = RiskManager(settings.trading)
    orchestrator = TradingOrchestrator(settings.strategy)
    technical = TechnicalAnalyzer(
        rsi_period=settings.trading.rsi_period,
        macd_fast=settings.trading.macd_fast,
        macd_slow=settings.trading.macd_slow,
        bb_period=settings.trading.bb_period,
    )
    volatility = VolatilityRegimeAnalyzer()
    
    print("✓ Risk Manager inicializado")
    print("✓ Trading Orchestrator inicializado")
    print("✓ Technical Analyzer inicializado")
    print("✓ Volatility Analyzer inicializado")
    
    # 3. Verificar precondiciones
    print("\n" + "-"*60)
    print("VERIFICANDO PRECONDICIONES DE RIESGO")
    print("-"*60 + "\n")
    
    can_trade, reason = risk_manager.check_all_preconditions()
    if can_trade:
        print("✓ Precondiciones cumplidas - Sistema listo para operar")
    else:
        print(f"✗ No se puede operar: {reason}")
        return
    
    risk_status = risk_manager.get_status()
    print("\nEstado del Risk Manager:")
    for key, value in risk_status.items():
        print(f"  • {key}: {value}")
    
    # 4. Análisis de ejemplo
    print("\n" + "-"*60)
    print("ANÁLISIS DE MERCADO DE EJEMPLO")
    print("-"*60 + "\n")
    
    # Generar datos de prueba
    prices, highs, lows, closes = generate_sample_data(100)
    
    print(f"✓ Datos generados: {len(prices)} velas")
    print(f"  • Precio actual: ${prices[-1]:.2f}")
    print(f"  • Precio mínimo: ${min(prices):.2f}")
    print(f"  • Precio máximo: ${max(prices):.2f}")
    
    # Análisis técnico
    print("\n[ANÁLISIS TÉCNICO]")
    technical_result = technical.analyze_technical(prices, highs, lows, closes)
    
    print(f"Signal: {technical_result.signal.value}")
    print(f"Confidence: {technical_result.confidence:.1%}")
    print(f"Reasoning: {technical_result.reasoning}")
    print("\nIndicadores:")
    for indicator, value in technical_result.indicators.items():
        print(f"  • {indicator}: {value:.2f}" if isinstance(value, (int, float)) else f"  • {indicator}: {value}")
    
    # Análisis de volatilidad
    print("\n[ANÁLISIS DE VOLATILIDAD Y RÉGIMEN]")
    vol_analysis = volatility.get_analysis(prices, highs, lows, closes)
    
    print(f"Volatilidad: {vol_analysis['volatility']:.6f}")
    print(f"Volatilidad Percentil: {vol_analysis['volatility_percentile']:.1f}%")
    print(f"Nivel: {vol_analysis['volatility_level']}")
    print(f"Régimen: {vol_analysis['regime']}")
    print(f"¿Es breakout? {vol_analysis['is_breakout']}")
    print(f"¿Es tendencia? {vol_analysis['is_trending']}")
    print(f"Soporte: ${vol_analysis['support']:.2f}")
    print(f"Resistencia: ${vol_analysis['resistance']:.2f}")
    
    # 5. Decisión del Orquestador
    print("\n" + "-"*60)
    print("DECISIÓN DEL ORQUESTADOR")
    print("-"*60 + "\n")
    
    decision = orchestrator.make_decision(
        asset="EURUSD-OTC",
        technical_analysis=technical_result,
    )
    
    print(f"Asset: {decision.asset}")
    print(f"Signal: {decision.signal.value}")
    print(f"Direction: {decision.direction}")
    print(f"Confluencia Score: {decision.confluencia_score:.1%}")
    print(f"Confidence: {decision.final_confidence:.1%}")
    print(f"Can Trade: {decision.can_trade}")
    print(f"\nReasoning: {decision.reasoning}")
    
    # 6. Simulación de operación
    if decision.can_trade and decision.signal != TradeSignal.NO_SIGNAL:
        print("\n" + "-"*60)
        print("SIMULACIÓN DE OPERACIÓN")
        print("-"*60 + "\n")
        
        amount = risk_manager.calculate_trade_amount(
            consecutive_losses=risk_manager.daily_stats.consecutive_losses
        )
        
        print(f"Monto calculado: ${amount:.2f}")
        
        # Abrir posición
        position = risk_manager.open_position(
            asset="EURUSD-OTC",
            direction=decision.direction,
            amount=amount,
            entry_price=prices[-1],
            expiration_seconds=300,
        )
        
        print(f"✓ Posición abierta:")
        print(f"  • Asset: {position.asset}")
        print(f"  • Direction: {position.direction}")
        print(f"  • Entry Price: ${position.entry_price:.2f}")
        print(f"  • Amount: ${position.amount:.2f}")
        print(f"  • Expiration: {position.expiration_time}")
        
        # Simular resultado
        print(f"\n✓ Esperando {position.expiration_time} para resultado...")
        
        # Simular ganancia o pérdida
        exit_price = prices[-1] * (1 + np.random.randn() * 0.005)
        pnl = (exit_price - prices[-1]) * amount / prices[-1]
        result = "WIN" if pnl > 0 else "LOSS"
        
        # Cerrar posición
        risk_manager.close_position(
            position=position,
            exit_price=exit_price,
            result=result,
            pnl=pnl,
        )
        
        print(f"✓ Posición cerrada: {result}")
        print(f"  • Exit Price: ${exit_price:.2f}")
        print(f"  • PnL: ${pnl:.2f}")
        
        # Mostrar stats actualizadas
        print("\nEstadísticas actualizadas:")
        risk_status = risk_manager.get_status()
        for key, value in risk_status.items():
            print(f"  • {key}: {value}")
    
    # 7. Estadísticas del orquestador
    print("\n" + "-"*60)
    print("ESTADÍSTICAS DEL ORQUESTADOR")
    print("-"*60 + "\n")
    
    stats = orchestrator.get_statistics()
    print(f"Total de decisiones: {stats['total_decisions']}")
    print(f"Confluencia promedio: {stats['avg_confluencia']:.1%}")
    print(f"Confianza promedio: {stats['avg_confidence']:.1%}")
    print(f"Distribución de señales: {stats['signal_distribution']}")
    
    print("\n" + "="*60)
    print("EJEMPLO COMPLETADO")
    print("="*60)


if __name__ == "__main__":
    main()
