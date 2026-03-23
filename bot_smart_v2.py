#!/usr/bin/env python3
"""
🚀 BOT SMART MONEY V2 - Mejorado con:
- Filtro de volatilidad
- Confirmación de volumen
- Mejor timing entre entradas
"""

import os
import sys
import time
import json
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

EMAIL = os.getenv('EXNOVA_EMAIL')
PASSWORD = os.getenv('EXNOVA_PASSWORD')
CAPITAL = float(os.getenv('CAPITAL_PER_TRADE', 1.0))

DATA_DIR = Path(__file__).parent / "data" / "operaciones_smart_v2"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = DATA_DIR / f"smart_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
TRADES_FILE = DATA_DIR / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

# ═══════════════════════════════════════════════════════════════
# MEJORAS V2 - ANÁLISIS MEJORADO
# ═══════════════════════════════════════════════════════════════

def get_candles(api, asset, interval=60, count=100):
    """Obtener datos de velas"""
    try:
        end_time = int(api.get_server_timestamp())
        data = api.get_candles(asset, interval, count, end_time)
        if data and len(data) > 0:
            return [{
                'open': c.get('open', 0),
                'close': c.get('close', 0),
                'high': c.get('max', 0),
                'low': c.get('min', 0),
            } for c in data]
        return []
    except:
        return []

def calculate_volatility(candles, period=10):
    """Calcular volatilidad - NUEVO V2"""
    if len(candles) < period:
        return 0
    closes = [c['close'] for c in candles[-period:]]
    changes = [abs(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes))]
    return sum(changes) / len(changes) if changes else 0

def calculate_volume_ratio(candles, period=10):
    """Calcular ratio de volumen - NUEVO V2 (usando range de precio como proxy)"""
    if len(candles) < period + 5:
        return 1.0
    recent_range = sum(c['high'] - c['low'] for c in candles[-5:])
    avg_range = sum(c['high'] - c['low'] for c in candles[-period:-5]) / period if period > 5 else 1
    return recent_range / (avg_range * 5) if avg_range > 0 else 1.0

def find_support_resistance(candles, lookback=50):
    """Encontrar soportes y resistencias"""
    if len(candles) < lookback:
        return [], []
    
    highs = [c['high'] for c in candles[-lookback:]]
    lows = [c['low'] for c in candles[-lookback:]]
    
    resistances = []
    for i in range(5, len(highs) - 5):
        if highs[i] == max(highs[i-5:i+6]):
            resistances.append(highs[i])
    
    supports = []
    for i in range(5, len(lows) - 5):
        if lows[i] == min(lows[i-5:i+6]):
            supports.append(lows[i])
    
    def cluster_levels(levels, threshold=0.001):
        if not levels:
            return []
        levels = sorted(levels)
        clustered = [levels[0]]
        for l in levels[1:]:
            if abs(l - clustered[-1]) > threshold:
                clustered.append(l)
        return clustered
    
    return cluster_levels(supports), cluster_levels(resistances)

def detect_liquidity_sweep(candles, supports, resistances):
    """Detectar toma de liquidez"""
    if len(candles) < 10:
        return None, None
    
    recent = candles[-10:]
    
    for r in resistances:
        broke_above = any(c['high'] > r * 1.001 for c in recent[-5:])
        if broke_above:
            return 'SELL_LIQUIDITY', r
    
    for s in supports:
        broke_below = any(c['low'] < s * 0.999 for c in recent[-5:])
        if broke_below:
            return 'BUY_LIQUIDITY', s
    
    closes = [c['close'] for c in recent]
    if closes[-1] > closes[0] * 1.002:
        return 'BUY_MOMENTUM', closes[0]
    elif closes[-1] < closes[0] * 0.998:
        return 'SELL_MOMENTUM', closes[0]
    
    return None, None

def confirm_retest(candles, level, direction, lookback=5):
    """Confirmar reteste de nivel"""
    if len(candles) < lookback + 1:
        return False
    
    recent = candles[-(lookback+1):]
    current = candles[-1]
    
    tolerance = abs(level) * 0.001
    
    if direction == 'call':
        near_support = any(abs(c['low'] - level) < tolerance or c['close'] > level * 0.999 for c in recent[-3:])
        closing_up = current['close'] > recent[-2]['close']
        return near_support and closing_up
    else:
        near_resistance = any(abs(c['high'] - level) < tolerance or c['close'] < level * 1.001 for c in recent[-3:])
        closing_down = current['close'] < recent[-2]['close']
        return near_resistance and closing_down

def check_momentum(candles, period=3):
    """Verificar momentum"""
    if len(candles) < period + 1:
        return None
    closes = [c['close'] for c in candles[-(period+1):]]
    change = closes[-1] - closes[0]
    if change > 0:
        return 'UP'
    elif change < 0:
        return 'DOWN'
    return None

def analyze_smart_money_v2(candles):
    """Análisis mejorado V2 - Con filtro de volatilidad"""
    if len(candles) < 50:
        return None, 0, "Datos insuficientes"
    
    # 1. Calcular volatilidad - NUEVO
    volatility = calculate_volatility(candles)
    
    # Rechazar si volatilidad muy alta (>0.1%)
    if volatility > 0.1:
        return None, 0, f"Volatilidad alta ({volatility:.3f}%)"
    
    # 2. Calcular ratio de volumen - NUEVO
    volume_ratio = calculate_volume_ratio(candles)
    
    # 3. Encontrar S/R
    supports, resistances = find_support_resistance(candles, lookback=50)
    
    if not supports or not resistances:
        return None, 0, "No hay niveles claros"
    
    # 4. Detectar liquidez
    sweep_type, sweep_level = detect_liquidity_sweep(candles, supports, resistances)
    
    if sweep_type is None:
        return None, 0, "Sin toma de liquidez"
    
    # 5. Determinar dirección
    if sweep_type in ['BUY_LIQUIDITY', 'BUY_MOMENTUM']:
        direction = 'call'
        target_level = min([s for s in supports if s < sweep_level], default=sweep_level)
    else:
        direction = 'put'
        target_level = max([r for r in resistances if r > sweep_level], default=sweep_level)
    
    # 6. Confirmar reteste
    if not confirm_retest(candles, target_level, direction):
        return None, 0, "Sin reteste confirmado"
    
    # 7. Verificar momentum
    momentum = check_momentum(candles)
    
    if direction == 'call' and momentum != 'UP':
        return None, 0, f"Momentum no confirma {direction}"
    if direction == 'put' and momentum != 'DOWN':
        return None, 0, f"Momentum no confirma {direction}"
    
    # 8. Calcular confianza - MEJORADO
    confidence = 65
    
    # Bonus por volatilidad baja
    if volatility < 0.05:
        confidence += 10
    
    # Bonus por volumen confirmando
    if volume_ratio > 1.0:
        confidence += 5
    
    # Bonus por múltiples toques
    touches = sum(1 for c in candles[-20:] if abs(c['close'] - target_level) < abs(target_level) * 0.001)
    confidence += min(touches * 3, 10)
    
    return direction, min(confidence, 95), f"Sweep:{sweep_type} | Vol:{volatility:.3f}% | Mom:{momentum}"

# ═══════════════════════════════════════════════════════════════
# BOT PRINCIPAL V2
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("   🎯 BOT SMART MONEY V2 - Mejorado con Volatilidad")
print("="*70 + "\n")

log("\n" + "="*70)
log(f"🎯 BOT SMART MONEY V2 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log("Mejoras: Filtro volatilidad + Volumen + Timing optimizado")
log("="*70)

try:
    from exnovaapi.stable_api import Exnova
    
    log("🔗 Conectando a Exnova...")
    api = Exnova(EMAIL, PASSWORD)
    api.connect()
    
    time.sleep(15)
    
    balance = api.get_balance()
    log(f"💰 Balance: ${balance:.2f}")
    
    assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'EURJPY-OTC']
    log(f"✅ {len(assets)} activos")
    
    trades = 0
    wins = 0
    losses = 0
    pnl = 0
    ops_since_break = 0
    
    log("\n" + "="*70)
    log("🎯 BUSCANDO SETUP VÁLIDO V2")
    log("="*70)
    
    trade_num = 0
    session_start = time.time()
    
    while True:
        log(f"\n{'='*60}")
        log(f"🔍 BUSCANDO SETUP #{trade_num + 1}")
        log(f"{'='*60}")
        
        for asset in assets:
            log(f"\n📊 Analizando {asset}...")
            
            candles = get_candles(api, asset, interval=60, count=80)
            
            if len(candles) < 50:
                log(f"   ⚠️  Datos insuficientes")
                time.sleep(5)
                continue
            
            direction, confidence, reason = analyze_smart_money_v2(candles)
            
            if direction is None:
                log(f"   ⏸️  {reason}")
                continue
            
            log(f"   🎯 SETUP ENCONTRADO!")
            log(f"   📈 Dirección: {direction.upper()}")
            log(f"   📊 Confianza: {confidence}%")
            log(f"   📝 {reason}")
            
            if confidence < 65:
                log(f"   ⏸️  Confianza baja ({confidence}% < 65%)")
                continue
            
            # ENTRADA 1
            log(f"\n   🎯 ENTRADA 1: Retroceso inicial")
            
            status1, order_id1 = api.buy(CAPITAL, asset, direction, 1)
            
            if status1 and order_id1:
                log(f"   ✅ Ejecutada - ID: {order_id1}")
                log(f"   ⏳ Esperando resultado (65s)...")
                
                time.sleep(65)
                
                try:
                    result1, profit1 = api.check_win_v4(order_id1)
                    
                    if result1 == "win":
                        wins += 1
                        pnl += profit1
                        log(f"   ✅ Entrada 1: GANADA +${profit1:.2f}")
                        
                        # ESPERAR ANTES DE ENTRADA 2
                        wait_before_2 = random.randint(25, 45)
                        log(f"\n   😴 Esperando antes de Entrada 2... ({wait_before_2}s)")
                        time.sleep(wait_before_2)
                        
                        # Verificar momentum nuevamente
                        candles_new = get_candles(api, asset, interval=60, count=30)
                        momentum = check_momentum(candles_new)
                        
                        if (direction == 'call' and momentum == 'UP') or (direction == 'put' and momentum == 'DOWN'):
                            log(f"   ✅ Momentum aún confirmado: {momentum}")
                            
                            status2, order_id2 = api.buy(CAPITAL, asset, direction, 1)
                            
                            if status2 and order_id2:
                                log(f"   ✅ Entrada 2 ejecutada - ID: {order_id2}")
                                time.sleep(65)
                                
                                try:
                                    result2, profit2 = api.check_win_v4(order_id2)
                                    
                                    if result2 == "win":
                                        wins += 1
                                        pnl += profit2
                                        log(f"   ✅ Entrada 2: GANADA +${profit2:.2f}")
                                    else:
                                        losses += 1
                                        pnl -= CAPITAL
                                        log(f"   ❌ Entrada 2: PERDIDA -${CAPITAL:.2f}")
                                    
                                    trades += 1
                                except Exception as e:
                                    log(f"   ⚠️  Error verificando E2: {str(e)[:40]}")
                        else:
                            log(f"   ⏸️  Momentum cambió, saltando Entrada 2")
                    
                    else:
                        log(f"   ❌ Entrada 1: PERDIDA -${CAPITAL:.2f}")
                        losses += 1
                        pnl -= CAPITAL
                        trades += 1
                        log(f"   ⏸️  Setup falló, buscando nuevo...")
                
                except Exception as e:
                    log(f"   ⚠️  Error: {str(e)[:50]}")
            else:
                log(f"   ❌ No se pudo ejecutar")
            
            # Stats
            if trades > 0:
                wr = (wins / trades * 100)
                elapsed = (time.time() - session_start) / 60
                log(f"\n📈 STATS: {trades} ops | {wins}W-{losses}L | {wr:.1f}% WR | ${pnl:.2f} | {elapsed:.1f}min")
            
            # DESCANSO
            ops_since_break += 1
            if ops_since_break >= 3:
                break_time = random.randint(300, 540)
                log(f"\n☕ DESCANSO ({break_time/60:.1f}min)...")
                time.sleep(break_time)
                ops_since_break = 0
            else:
                wait = random.randint(60, 180)
                log(f"\n⏳ Esperando próximo setup... ({wait}s)")
                time.sleep(wait)
            
            break
        
        else:
            wait = random.randint(30, 60)
            time.sleep(wait)

except KeyboardInterrupt:
    log(f"\n⏹️  DETENIDO")
    if trades > 0:
        wr = (wins/trades*100)
        log(f"📊 {trades} ops | {wins}W-{losses}L | {wr:.1f}% WR | ${pnl:.2f}")

except Exception as e:
    log(f"❌ FATAL: {e}")
    import traceback
    log(traceback.format_exc())

finally:
    log(f"✅ Log: {LOG_FILE}")
    log(f"✅ Trades: {TRADES_FILE}")
