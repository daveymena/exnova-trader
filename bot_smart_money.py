#!/usr/bin/env python3
"""
🚀 BOT SMART MONEY - Soporte/Resistencia + Liquidez + Confirmación
Estrategia: Liquidity Sweep → Retest → Confirmación → Entrada
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

DATA_DIR = Path(__file__).parent / "data" / "operaciones_smart"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = DATA_DIR / f"smart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
TRADES_FILE = DATA_DIR / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

# ═══════════════════════════════════════════════════════════════
# ANÁLISIS DE MERCADO - SMART MONEY CONCEPTS
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

def find_support_resistance(candles, lookback=50):
    """Encontrar soportes y resistencias válidos"""
    if len(candles) < lookback:
        return [], []
    
    highs = [c['high'] for c in candles[-lookback:]]
    lows = [c['low'] for c in candles[-lookback:]]
    
    # Resistencias - máximos locales
    resistances = []
    for i in range(5, len(highs) - 5):
        if highs[i] == max(highs[i-5:i+6]):
            resistances.append(highs[i])
    
    # Soportes - mínimos locales
    supports = []
    for i in range(5, len(lows) - 5):
        if lows[i] == min(lows[i-5:i+6]):
            supports.append(lows[i])
    
    # Eliminar duplicados cercanos (within 0.001)
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
    """Detectar toma de liquidez (sweep) - VERSIÓN RELAJADA"""
    if len(candles) < 10:
        return None, None
    
    recent = candles[-10:]
    current = candles[-1]
    
    # Buscar rompimiento de resistencia reciente
    for r in resistances:
        # Precio rompió R y cerró cerca o abajo
        broke_above = any(c['high'] > r * 1.001 for c in recent[-5:])
        if broke_above:
            return 'SELL_LIQUIDITY', r
    
    # Buscar rompimiento de soporte reciente
    for s in supports:
        # Precio rompió S y cerró cerca o arriba
        broke_below = any(c['low'] < s * 0.999 for c in recent[-5:])
        if broke_below:
            return 'BUY_LIQUIDITY', s
    
    # Si no hay sweep claro, usar tendencia simple
    closes = [c['close'] for c in recent]
    if closes[-1] > closes[0] * 1.002:
        return 'BUY_MOMENTUM', closes[0]
    elif closes[-1] < closes[0] * 0.998:
        return 'SELL_MOMENTUM', closes[0]
    
    return None, None

def confirm_retest(candles, level, direction, lookback=5):
    """Confirmar reteste de nivel - VERSIÓN RELAJADA"""
    if len(candles) < lookback + 1:
        return False
    
    recent = candles[-(lookback+1):]
    current = candles[-1]
    
    tolerance = abs(level) * 0.001  # 0.1% tolerancia (más amplio)
    
    if direction == 'call':
        # Para CALL: precio cerca del soporte y subiendo
        near_support = any(abs(c['low'] - level) < tolerance or c['close'] > level * 0.999 for c in recent[-3:])
        closing_up = current['close'] > recent[-2]['close']
        return near_support and closing_up
    else:
        # Para PUT: precio cerca de resistencia y bajando
        near_resistance = any(abs(c['high'] - level) < tolerance or c['close'] < level * 1.001 for c in recent[-3:])
        closing_down = current['close'] < recent[-2]['close']
        return near_resistance and closing_down

def check_momentum(candles, period=3):
    """Verificar momentum a favor"""
    if len(candles) < period + 1:
        return None
    
    closes = [c['close'] for c in candles[-(period+1):]]
    
    # Calcular cambio de precio
    change = closes[-1] - closes[0]
    
    if change > 0:
        return 'UP'
    elif change < 0:
        return 'DOWN'
    return None

def analyze_smart_money(candles):
    """Análisis principal Smart Money"""
    if len(candles) < 50:
        return None, 0, "Datos insuficientes"
    
    # 1. Encontrar S/R
    supports, resistances = find_support_resistance(candles, lookback=50)
    
    if not supports or not resistances:
        return None, 0, "No hay niveles claros"
    
    # 2. Detectar toma de liquidez
    sweep_type, sweep_level = detect_liquidity_sweep(candles, supports, resistances)
    
    if sweep_type is None:
        return None, 0, "Sin toma de liquidez"
    
    # 3. Determinar dirección basada en sweep
    if sweep_type == 'BUY_LIQUIDITY':
        direction = 'call'
        target_level = min([s for s in supports if s < sweep_level], default=sweep_level)
    else:
        direction = 'put'
        target_level = max([r for r in resistances if r > sweep_level], default=sweep_level)
    
    # 4. Confirmar reteste
    if not confirm_retest(candles, target_level, direction):
        return None, 0, "Sin reteste confirmado"
    
    # 5. Verificar momentum
    momentum = check_momentum(candles)
    
    if direction == 'call' and momentum != 'UP':
        return None, 0, f"Momentum no confirma {direction}"
    if direction == 'put' and momentum != 'DOWN':
        return None, 0, f"Momentum no confirma {direction}"
    
    # 6. Calcular confianza
    confidence = 65
    
    # Bonus por múltiples toques del nivel
    touches = sum(1 for c in candles[-20:] if abs(c['close'] - target_level) < abs(target_level) * 0.001)
    confidence += min(touches * 3, 15)
    
    # Bonus por sweep claro
    confidence += 10
    
    return direction, min(confidence, 90), f"Sweep:{sweep_type} → Retest → {direction.upper()}"

# ═══════════════════════════════════════════════════════════════
# BOT PRINCIPAL
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("   🎯 BOT SMART MONEY - Liquidez + Retest + Confirmación")
print("="*70 + "\n")

log("\n" + "="*70)
log(f"🎯 BOT SMART MONEY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log("Estrategia: Liquidity Sweep → Retest → Confirmación → 1 Entrada")
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
    log("🎯 BUSCANDO SETUP VÁLIDO (1 operación a la vez)")
    log("="*70)
    
    trade_num = 0
    skipped = 0
    session_start = time.time()
    
    while True:
        # SOLO 1 OPERACIÓN A LA VEZ
        log(f"\n{'='*60}")
        log(f"🔍 BUSCANDO SETUP #{trade_num + 1}")
        log(f"{'='*60}")
        
        # Analizar cada activo
        for asset in assets:
            log(f"\n📊 Analizando {asset}...")
            
            # Obtener datos
            candles = get_candles(api, asset, interval=60, count=80)
            
            if len(candles) < 50:
                log(f"   ⚠️  Datos insuficientes ({len(candles)} velas)")
                time.sleep(5)
                continue
            
            # Análisis Smart Money
            direction, confidence, reason = analyze_smart_money(candles)
            
            if direction is None:
                log(f"   ⏸️  {reason}")
                continue
            
            log(f"   🎯 SETUP ENCONTRADO!")
            log(f"   📈 Dirección: {direction.upper()}")
            log(f"   📊 Confianza: {confidence}%")
            log(f"   📝 Razón: {reason}")
            
            # Solo operar si confianza > 60%
            if confidence < 60:
                log(f"   ⏸️  Confianza baja ({confidence}% < 60%)")
                continue
            
            # ─────────────────────────────────────────────
            # ENTRADA 1: Retroceso (mínimo $1)
            # ─────────────────────────────────────────────
            log(f"\n   🎯 ENTRADA 1: Retroceso inicial")
            
            capital_1 = max(CAPITAL, 1.0)  # Mínimo $1
            
            status1, order_id1 = api.buy(capital_1, asset, direction, 1)
            
            log(f"   📤 Resultado: status={status1}, order={order_id1}")
            
            if status1 and order_id1:
                log(f"   ✅ Entrada 1 ejecutada - ID: {order_id1}")
                log(f"   💰 Capital: ${capital_1:.2f}")
                log(f"   ⏳ Esperando confirmación (45s)...")
                
                time.sleep(45)
                
                # Verificar resultado entrada 1
                try:
                    result1, profit1 = api.check_win_v4(order_id1)
                    
                    if result1 == "win":
                        log(f"   ✅ Entrada 1: GANADA +${profit1:.2f}")
                        wins += 1
                        pnl += profit1
                        
                        # ─────────────────────────────────────────────
                        # ENTRADA 2: Confirmación (tamaño normal)
                        # ─────────────────────────────────────────────
                        log(f"\n   🎯 ENTRADA 2: Confirmación con momentum")
                        
                        # Esperar confirmación adicional
                        log(f"   ⏳ Esperando confirmación extra (15s)...")
                        time.sleep(15)
                        
                        # Nueva análisis rápida
                        candles_new = get_candles(api, asset, interval=60, count=30)
                        momentum = check_momentum(candles_new)
                        
                        if (direction == 'call' and momentum == 'UP') or (direction == 'put' and momentum == 'DOWN'):
                            log(f"   ✅ Momentum confirmado: {momentum}")
                            
                            status2, order_id2 = api.buy(CAPITAL, asset, direction, 1)
                            
                            if status2 and order_id2:
                                log(f"   ✅ Entrada 2 ejecutada - ID: {order_id2}")
                                log(f"   💰 Capital: ${CAPITAL:.2f}")
                                log(f"   ⏳ Esperando resultado (65s)...")
                                
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
                            log(f"   ⏸️  Momentum no confirmado, saltando Entrada 2")
                    
                    else:
                        log(f"   ❌ Entrada 1: PERDIDA -${capital_1:.2f}")
                        losses += 1
                        pnl -= capital_1
                        
                        # Si pierde la primera, NO entrar a la segunda
                        log(f"   ⏸️  Setup falló, buscando nuevo setup...")
                        trades += 1
                
                except Exception as e:
                    log(f"   ⚠️  Error: {str(e)[:50]}")
            else:
                log(f"   ❌ No se pudo ejecutar Entrada 1")
            
            # Guardar trade
            with open(TRADES_FILE, 'a') as f:
                f.write(json.dumps({
                    'asset': asset,
                    'direction': direction,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat(),
                    'pnl': pnl,
                }) + '\n')
            
            # Stats
            if trades > 0:
                wr = (wins / trades * 100)
                elapsed = (time.time() - session_start) / 60
                log(f"\n📈 STATS: {trades} ops | {wins}W-{losses}L | {wr:.1f}% WR | ${pnl:.2f} | {elapsed:.1f}min")
            
            # DESCANSO después de cada trade completo
            ops_since_break += 1
            if ops_since_break >= 3:
                break_time = random.randint(180, 360)
                log(f"\n☕ DESCANSO ({break_time/60:.1f}min)...")
                time.sleep(break_time)
                ops_since_break = 0
            else:
                wait = random.randint(60, 180)
                log(f"\n⏳ Esperando próximo setup... ({wait}s)")
                time.sleep(wait)
            
            # Romper loop para buscar nuevo setup
            break
        
        # Si no encontró setup en ningún activo
        else:
            skipped += 1
            if skipped % 5 == 0:
                log(f"\n⏸️  No se encontró setup válido ({skipped} intentos)")
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
