#!/usr/bin/env python3
"""
🚀 BOT INTELIGENTE - Análisis Técnico + Comportamiento Humano
Estrategia: Reversión con RSI + Confirmación de tendencia
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

# Configuración
EMAIL = os.getenv('EXNOVA_EMAIL')
PASSWORD = os.getenv('EXNOVA_PASSWORD')
CAPITAL = float(os.getenv('CAPITAL_PER_TRADE', 1.0))

DATA_DIR = Path(__file__).parent / "data" / "operaciones_inteligente"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = DATA_DIR / f"inteligente_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
TRADES_FILE = DATA_DIR / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

def get_candles_data(api, asset, interval=60, count=30):
    """Obtener datos de velas para análisis técnico"""
    try:
        end_time = int(api.get_server_timestamp())
        data = api.get_candles(asset, interval, count, end_time)
        
        if data and len(data) > 0:
            candles = []
            for c in data:
                candles.append({
                    'open': c.get('open', 0),
                    'close': c.get('close', 0),
                    'high': c.get('max', 0),
                    'low': c.get('min', 0),
                })
            return candles
        return []
    except Exception as e:
        return []

def calculate_rsi(closes, period=14):
    """Calcular RSI (Relative Strength Index)"""
    if len(closes) < period + 1:
        return 50
    
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 70
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ema(closes, period=10):
    """Calcular EMA (Exponential Moving Average)"""
    if len(closes) < period:
        return sum(closes) / len(closes) if closes else 0
    
    multiplier = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    
    for close in closes[period:]:
        ema = (close - ema) * multiplier + ema
    
    return ema

def analyze_market(candles):
    """Analizar mercado y retornar señal"""
    if len(candles) < 15:
        return None, 0
    
    closes = [c['close'] for c in candles]
    current_price = closes[-1]
    
    # RSI
    rsi = calculate_rsi(closes)
    
    # EMA
    ema_10 = calculate_ema(closes, 10)
    ema_20 = calculate_ema(closes, 20) if len(closes) >= 20 else ema_10
    
    # Tendencia
    trend = 'UP' if ema_10 > ema_20 else 'DOWN'
    
    # Señal de trading
    signal = None
    confidence = 0
    
    # Estrategia: Reversión en extremos con confirmación
    if rsi < 25:  # Sobreventa fuerte
        signal = 'call'
        confidence = 70 + (25 - rsi)  # Mayor confianza cuanto más bajo
    elif rsi > 75:  # Sobrecompra fuerte
        signal = 'put'
        confidence = 70 + (rsi - 75)
    elif rsi < 35 and trend == 'DOWN':  # Sobreventa + tendencia bajista
        signal = 'call'
        confidence = 60
    elif rsi > 65 and trend == 'UP':  # Sobrecompra + tendencia alcista
        signal = 'put'
        confidence = 60
    
    return signal, min(confidence, 95)

print("\n" + "="*70)
print("   🧠 BOT INTELIGENTE - Análisis Técnico + Humano")
print("="*70 + "\n")

log("\n" + "="*70)
log(f"🧠 BOT INTELIGENTE INICIADO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log("Estrategia: RSI + EMA + Reversión en extremos")
log("="*70)

try:
    from exnovaapi.stable_api import Exnova
    
    # Conectar
    log("🔗 Conectando a Exnova...")
    api = Exnova(EMAIL, PASSWORD)
    api.connect()
    
    log("⏳ Esperando conexión...")
    time.sleep(20)
    
    timestamp = api.get_server_timestamp()
    if timestamp and timestamp > 0:
        log(f"✅ Conectado - Timestamp: {timestamp}")
    
    balance = api.get_balance()
    log(f"💰 Balance: ${balance:.2f}")
    
    # Activos
    assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'EURJPY-OTC']
    log(f"✅ {len(assets)} activos disponibles")
    
    # Stats
    trades = 0
    wins = 0
    losses = 0
    pnl = 0
    ops_since_break = 0
    
    log("\n" + "="*70)
    log("🎯 INICIANDO SESIÓN INTELIGENTE")
    log("="*70)
    
    trade_num = 0
    skipped = 0
    session_start = time.time()
    
    while True:
        trade_num += 1
        
        try:
            # 1. Analizar mercado antes de operar
            log(f"\n📊 #{trade_num}: Analizando mercado...")
            
            # Seleccionar activo
            asset = random.choice(assets)
            
            # Obtener datos de velas
            candles = get_candles_data(api, asset, interval=60, count=30)
            
            if len(candles) < 15:
                log(f"   ⚠️  Datos insuficientes, esperando...")
                time.sleep(30)
                continue
            
            # Analizar
            signal, confidence = analyze_market(candles)
            
            if signal is None:
                skipped += 1
                log(f"   ⏸️  Sin señal clara (RSI neutro) - Esperando...")
                
                if skipped % 3 == 0:
                    wait = random.randint(60, 180)
                    log(f"   😴 Pausa de mercado... ({wait}s)")
                    time.sleep(wait)
                else:
                    time.sleep(random.randint(20, 45))
                continue
            
            # 2. Tener señal - decidir operar
            log(f"   🎯 Señal detectada: {signal.upper()}")
            log(f"   📈 Confianza: {confidence:.0f}%")
            
            # Solo operar si confianza > 55%
            if confidence < 55:
                log(f"   ⏸️  Confianza baja, esperando mejor señal...")
                time.sleep(random.randint(15, 30))
                continue
            
            # 3. Comportamiento humano - a veces dudar
            if random.random() < 0.15:
                log(f"   🤔 Dudando decisión...")
                time.sleep(random.randint(5, 15))
            
            # 4. Ejecutar operación
            log(f"\n📊 EJECUTANDO: {asset} {signal.upper()} (${CAPITAL})")
            
            status, order_id = api.buy(CAPITAL, asset, signal, 1)
            
            if status and order_id:
                log(f"   ✅ Ejecutada - ID: {order_id}")
                
                # Esperar resultado
                wait_time = random.randint(62, 70)
                log(f"   ⏳ Esperando resultado... ({wait_time}s)")
                time.sleep(wait_time)
                
                # Verificar resultado
                try:
                    result_status, profit = api.check_win_v4(order_id)
                    
                    if result_status == "win":
                        wins += 1
                        pnl += profit
                        log(f"   ✅ GANADA: +${profit:.2f}")
                    else:
                        losses += 1
                        pnl -= CAPITAL
                        log(f"   ❌ PERDIDA: -${CAPITAL:.2f}")
                    
                    trades += 1
                    ops_since_break += 1
                    
                    # Guardar
                    with open(TRADES_FILE, 'a') as f:
                        f.write(json.dumps({
                            'id': trade_num,
                            'timestamp': datetime.now().isoformat(),
                            'asset': asset,
                            'direction': signal,
                            'confidence': confidence,
                            'outcome': result_status,
                            'pnl': profit if result_status == "win" else -CAPITAL,
                        }) + '\n')
                
                except Exception as e:
                    log(f"   ⚠️  Error verificando: {str(e)[:50]}")
            else:
                log(f"   ❌ No se ejecutó")
            
            # 5. Stats cada 3 ops
            if trades > 0 and trades % 3 == 0:
                wr = (wins / trades * 100)
                elapsed = (time.time() - session_start) / 60
                log(f"\n📈 STATS: {trades} ops | {wins}W-{losses}L | {wr:.1f}% WR | ${pnl:.2f} | {elapsed:.1f}min")
                log(f"   Señales saltadas: {skipped}\n")
            
            # 6. Pausa humana
            if random.random() < 0.3:
                pause = random.randint(20, 60)
                log(f"   😴 Pausa... ({pause}s)")
                time.sleep(pause)
            
            # 7. Descanso largo cada 6-10 ops
            if ops_since_break >= random.randint(6, 10):
                break_time = random.randint(180, 480)
                log(f"\n☕ DESCANSO ({break_time}s = {break_time/60:.1f}min)...")
                time.sleep(break_time)
                ops_since_break = 0
                log("   🔄 Regresando...\n")
            
            # 8. Tiempo entre operaciones
            gap = random.randint(10, 30)
            log(f"   ⏱️  Siguiente en... ({gap}s)")
            time.sleep(gap)
        
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log(f"❌ Error: {e}")
            time.sleep(30)

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
