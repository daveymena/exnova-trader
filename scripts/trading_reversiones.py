"""
Script de trading en tiempo real para Exnova - Modo PRACTICE
Estrategia: Una operación a la vez, analizar resultado, aprovechar reversiones
"""
import os
import sys
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/bot-reversiones-iq')

from exnovaapi.stable_api import Exnova
from core.learning.ppo_trainer import load_trained_model
from core.feature_engineer import FeatureEngineerWrapper
from strategies.technical import FeatureEngineer

EMAIL = "daveymena16@gmail.com"
PASSWORD = "6715320Dvd."

ACTIVOS = ["EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC"]
MONTO_OPERACION = 1
EXPIRACION = 1  # 1 minuto
TIEMPO_MAX_COMPRA = 25

class TradingBot:
    def __init__(self):
        self.bot = None
        self.model = None
        self.feature_engineer = FeatureEngineerWrapper()
        self.operations_history = []
        self.wins = 0
        self.losses = 0
        self.balance_inicial = 0
        self.model_path = "exnova_ppo_model"
        self.ultima_direccion = None
        self.ultimo_activo = None
        self.racha_perdidas = 0
        
    def conectar(self):
        print("[EXNOVA] Conectando...")
        self.bot = Exnova(EMAIL, PASSWORD, active_account_type="PRACTICE")
        check, reason = self.bot.connect()
        
        if check:
            print("[EXNOVA] ✓ Conectado!")
            self.balance_inicial = self.bot.get_balance()
            print(f"[EXNOVA] Balance: ${self.balance_inicial}")
            return True
        else:
            print(f"[EXNOVA] Error: {reason}")
            return False
    
    def cargar_modelo(self):
        try:
            self.model = load_trained_model(self.model_path)
            print("[PPO] ✓ Modelo cargado")
            return True
        except:
            print("[PPO] ✗ Sin modelo, usando análisis técnico")
            return False
    
    def obtener_datos(self, activo, cantidad=100):
        try:
            candles = self.bot.get_candles(activo, 60, cantidad, time.time())
            if not candles:
                return None
            
            datos = []
            for c in candles:
                datos.append({
                    'timestamp': c.get('from', 0),
                    'open': c.get('open', 0),
                    'high': c.get('max', 0),
                    'low': c.get('min', 0),
                    'close': c.get('close', 0)
                })
            
            df = pd.DataFrame(datos)
            df = df.sort_values('timestamp')
            return df
        except Exception as e:
            print(f"[ERROR] Obteniendo datos: {e}")
            return None
    
    def analizar_mercado(self, activo, usar_reversion=False):
        """Analizar mercado y tomar decisión"""
        df = self.obtener_datos(activo, cantidad=100)
        if df is None or len(df) < 50:
            return None, None, "Sin datos suficientes"
        
        fe = FeatureEngineer()
        df_con_indicadores = fe.prepare_for_rl(df)
        
        ultimo = df_con_indicadores.iloc[-1] if len(df_con_indicadores) > 0 else None
        anterior = df_con_indicadores.iloc[-2] if len(df_con_indicadores) > 1 else None
        
        señales_call = []
        señales_put = []
        
        if ultimo is not None and anterior is not None:
            rsi = ultimo.get('rsi', 50)
            rsi_anterior = anterior.get('rsi', 50)
            
            # RSI Reversión
            if rsi_anterior < 30 and rsi > rsi_anterior + 3:
                señales_call.append(f"RSI rev: {rsi_anterior:.0f}→{rsi:.0f}")
            elif rsi_anterior > 70 and rsi < rsi_anterior - 3:
                señales_put.append(f"RSI rev: {rsi_anterior:.0f}→{rsi:.0f}")
            elif rsi < 25:
                señales_call.append(f"RSI oversold: {rsi:.0f}")
            elif rsi > 75:
                señales_put.append(f"RSI overbought: {rsi:.0f}")
            
            # MACD
            macd = ultimo.get('macd', 0)
            macd_sig = ultimo.get('macd_signal', 0)
            macd_ant = anterior.get('macd', 0)
            macd_sig_ant = anterior.get('macd_signal', 0)
            
            if macd_ant < macd_sig_ant and macd > macd_sig:
                señales_call.append("MACD cross up")
            elif macd_ant > macd_sig_ant and macd < macd_sig:
                señales_put.append("MACD cross down")
            
            # BB
            close = ultimo.get('close', 0)
            bb_low = ultimo.get('bb_low', close)
            bb_high = ultimo.get('bb_high', close)
            
            if close <= bb_low * 1.002:
                señales_call.append("BB lower")
            elif close >= bb_high * 0.998:
                señales_put.append("BB upper")
            
            # SMA
            sma_20 = ultimo.get('sma_20', close)
            if close < sma_20 * 0.999:
                señales_call.append("Below SMA20")
            elif close > sma_20 * 1.001:
                señales_put.append("Above SMA20")
            
            # Patrones
            if ultimo.get('pattern_hammer', 0) == 1:
                señales_call.append("Hammer")
            if ultimo.get('pattern_bullish_engulfing', 0) == 1:
                señales_call.append("Engulfing")
            
            # REVERSIÓN forzada
            if usar_reversion and self.racha_perdidas >= 2:
                if señales_put and not señales_call:
                    señales_call.append(f"REVERSE x{self.racha_perdidas}")
                elif señales_call and not señales_put:
                    señales_put.append(f"REVERSE x{self.racha_perdidas}")
            
            # DECISIÓN: 1+ señal clara
            if len(señales_call) >= 1 and len(señales_put) == 0:
                return "CALL", señales_call, df
            elif len(señales_put) >= 1 and len(señales_call) == 0:
                return "PUT", señales_put, df
        
        return None, ["Sin señal"], df
    
    def ejecutar_operacion(self, activo, direccion):
        # Esperar momento adecuado del minuto
        try:
            timestamp = self.bot.get_server_timestamp()
            segundos = int(timestamp) % 60
            if segundos > TIEMPO_MAX_COMPRA:
                print(f"[INFO] Esperar inicio de minuto (seg {segundos})...")
                time.sleep(65 - segundos)
        except:
            pass
        
        action = "call" if direccion == "CALL" else "put"
        
        for intento in range(3):
            try:
                buy_status, order_id = self.bot.buy(MONTO_OPERACION, activo, action, EXPIRACION)
                
                if buy_status:
                    print(f"[OPERACION] ✓ {activo} - {direccion} - ID: {order_id}")
                    return {'id': order_id, 'activo': activo, 'direccion': direccion}
                else:
                    print(f"[WARN] Intento {intento+1}: {order_id}")
                    time.sleep(2)
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(2)
        
        return None
    
    def esperar_y_verificar(self, id_operacion, timeout=90):
        print(f"[ESPERANDO] Resultado (≈{timeout}s)...")
        
        try:
            resultado, ganancia = self.bot.check_win_v4(id_operacion, timeout=timeout)
            return {'estado': resultado, 'ganancia': ganancia}
        except Exception as e:
            print(f"[ERROR] Verificación: {e}")
            return {'estado': 'error', 'ganancia': 0}
    
    def analizar_resultado(self, operacion, resultado):
        """Analizar por qué se ganó o perdió"""
        estado = resultado.get('estado', 'unknown')
        ganancia = resultado.get('ganancia', 0)
        
        if estado == 'win':
            self.wins += 1
            self.racha_perdidas = 0
            resultado_texto = "✓ GANADA"
        elif estado == 'loss':
            self.losses += 1
            self.racha_perdidas += 1
            resultado_texto = "✗ PERDIDA"
        else:
            resultado_texto = f"? {estado}"
        
        analisis = {
            'timestamp': datetime.now().isoformat(),
            'activo': operacion['activo'],
            'direccion': operacion['direccion'],
            'razon': operacion['razon'],
            'resultado': resultado_texto,
            'ganancia': ganancia,
            'balance': self.bot.get_balance()
        }
        
        self.operations_history.append(analisis)
        
        print("\n" + "="*60)
        print(f"  RESULTADO: {resultado_texto}")
        print("="*60)
        print(f"Activo: {operacion['activo']}")
        print(f"Dirección: {operacion['direccion']}")
        print(f"Señal: {', '.join(operacion['razon'])}")
        print(f"Ganancia: ${ganancia}")
        print(f"Balance: ${analisis['balance']}")
        print(f"Racha pérdidas: {self.racha_perdidas}")
        print("="*60)
        
        return analisis
    
    def mostrar_estadisticas(self):
        total = self.wins + self.losses
        winrate = (self.wins / total * 100) if total > 0 else 0
        
        print("\n" + "="*60)
        print("  ESTADÍSTICAS")
        print("="*60)
        print(f"Total: {total} | Ganadas: {self.wins} | Perdidas: {self.losses}")
        print(f"Win rate: {winrate:.1f}%")
        print(f"Balance: ${self.bot.get_balance()} (inicial: ${self.balance_inicial})")
        print("="*60)
    
    def operativa(self, num_operaciones=5):
        print(f"\n[INICIO] {num_operaciones} operaciones una a la vez...")
        
        for i in range(num_operaciones):
            print(f"\n{'='*60}")
            print(f"  OPERACIÓN #{i+1}")
            print("="*60)
            
            # Seleccionar activo
            activo = ACTIVOS[i % len(ACTIVOS)]
            print(f"[INFO] Analizando {activo}...")
            
            # Analizar mercado (sin reversión primero)
            señal, razon, df = self.analizar_mercado(activo, usar_reversion=False)
            
            if señal is None:
                print("[INFO] Sin señal clara, probando con reversión...")
                señal, razon, df = self.analizar_mercado(activo, usar_reversion=True)
            
            if señal is None:
                print("[INFO] Sin señal, esperando 30s...")
                time.sleep(30)
                continue
            
            print(f"[SEÑAL] {señal}")
            print(f"[RAZÓN] {razon}")
            
            # Ejecutar operación
            operacion = self.ejecutar_operacion(activo, señal)
            
            if not operacion:
                print("[ERROR] Operación fallida")
                continue
            
            # Agregar razón a la operación
            operacion['razon'] = razon
            
            # Esperar resultado
            resultado = self.esperar_y_verificar(operacion['id'], timeout=80)
            
            # Analizar resultado
            self.analizar_resultado(operacion, resultado)
            
            # Mostrar estadísticas
            self.mostrar_estadisticas()
            
            # Cooldown entre operaciones
            if i < num_operaciones - 1:
                print("\n[INFO] Esperando 20s...")
                time.sleep(20)
        
        print("\n[FIN] Operaciones completadas!")
        self.guardar_historial()
    
    def guardar_historial(self):
        if self.operations_history:
            archivo = f"historial_operaciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(archivo, 'w') as f:
                json.dump(self.operations_history, f, indent=2)
            print(f"[GUARDADO] {archivo}")

def main():
    print("="*60)
    print("  BOT TRADING EXNOVA - REVERSIONES")
    print("="*60)
    
    bot = TradingBot()
    
    if not bot.conectar():
        return
    
    bot.cargar_modelo()
    
    # Ejecutar 5 operaciones (ajustar según necesidad)
    bot.operativa(num_operaciones=5)

if __name__ == "__main__":
    main()
