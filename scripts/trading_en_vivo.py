"""
Script de trading en tiempo real para Exnova - Modo PRACTICE
Analiza cada operación para mejorar el modelo
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

# Tiempo máximo de operación (en segundos) - evitar comprar al final del minuto
TIEMPO_MAX_COMPRA = 30

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
        
    def conectar(self):
        """Conectar a Exnova"""
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
        """Cargar modelo PPO entrenado"""
        try:
            self.model = load_trained_model(self.model_path)
            print("[PPO] ✓ Modelo cargado")
            return True
        except:
            print("[PPO] ✗ Modelo no encontrado, usando decisiones aleatorias")
            return False
    
    def obtener_datos(self, activo, cantidad=50):
        """Obtener velas recientes para análisis"""
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
    
    def obtener_features(self, df):
        """Obtener características para el modelo"""
        if df is None or len(df) < 20:
            return np.zeros((20,), dtype=np.float32)
        
        try:
            return self.feature_engineer.engineer_features(df)
        except Exception as e:
            print(f"[ERROR] Features: {e}")
            return np.zeros((20,), dtype=np.float32)
    
    def analizar_mercado(self, activo):
        """Analizar mercado y tomar decisión"""
        df = self.obtener_datos(activo, cantidad=100)
        if df is None or len(df) < 50:
            return None, None, "Sin datos suficientes"
        
        features = self.obtener_features(df)
        
        # Análisis técnico
        fe = FeatureEngineer()
        df_con_indicadores = fe.prepare_for_rl(df)
        
        ultimo = df_con_indicadores.iloc[-1] if len(df_con_indicadores) > 0 else None
        
        señal = None
        razon = []
        
        if ultimo is not None:
            # RSI
            rsi = ultimo.get('rsi', 50)
            if rsi < 30:
                señal = "CALL"
                razon.append(f"RSI sobrevendido: {rsi:.1f}")
            elif rsi > 70:
                señal = "PUT"
                razon.append(f"RSI sobrecomprado: {rsi:.1f}")
            
            # MACD
            macd = ultimo.get('macd', 0)
            macd_signal = ultimo.get('macd_signal', 0)
            if macd > macd_signal and macd > 0:
                señal = "CALL"
                razon.append("MACD alcista")
            elif macd < macd_signal and macd < 0:
                señal = "PUT"
                razon.append("MACD bajista")
            
            # Precio vs SMA
            close = ultimo.get('close', 0)
            sma_20 = ultimo.get('sma_20', close)
            if close < sma_20 * 0.998:
                señal = "CALL"
                razon.append(f"Precio bajo SMA20")
            elif close > sma_20 * 1.002:
                señal = "PUT"
                razon.append(f"Precio sobre SMA20")
            
            # Patrones
            if ultimo.get('pattern_hammer', 0) == 1:
                señal = "CALL"
                razon.append("Patrón Martillo")
            if ultimo.get('pattern_bullish_engulfing', 0) == 1:
                señal = "CALL"
                razon.append("Patrón Engulfing Alcista")
        
        # Si modelo PPO disponible, usarlo
        if self.model is not None and señal is None:
            try:
                action, _ = self.model.predict(features, deterministic=True)
                if action == 1:
                    señal = "CALL"
                    razon.append("Modelo PPO: CALL")
                elif action == 2:
                    señal = "PUT"
                    razon.append("Modelo PPO: PUT")
            except Exception as e:
                print(f"[WARN] PPO: {e}")
        
        return señal, razon, df
    
    def ejecutar_operacion(self, activo, direccion):
        """Ejecutar una operación"""
        # Verificar que hay tiempo suficiente para comprar
        timestamp = self.bot.get_server_timestamp()
        segundos_en_minuto = int(timestamp) % 60
        
        if segundos_en_minuto > TIEMPO_MAX_COMPRA:
            print(f"[INFO] Esperar siguiente minuto (segundo {segundos_en_minuto})")
            time.sleep(60 - segundos_en_minuto + 5)
        
        max_intentos = 3
        for intento in range(max_intentos):
            try:
                # Determinar acción (call/put en string)
                action = "call" if direccion == "CALL" else "put"
                
                print(f"[OPERACION] {activo} - {direccion} - ${MONTO_OPERACION} - Duración: {EXPIRACION}min (intento {intento+1})")
                
                # Usar formato simple: buy(monto, activo, direccion, duracion)
                buy_status, order_id = self.bot.buy(MONTO_OPERACION, activo, action, EXPIRACION)
                
                if buy_status:
                    print(f"[OPERACION] ✓ Ejecutada! ID: {order_id}")
                    return {'id': order_id, 'activo': activo, 'direccion': direccion}
                else:
                    print(f"[WARN] Intento {intento+1}: {order_id}")
                    if "Time for purchasing" in str(order_id):
                        time.sleep(3)
                        continue
                        
            except Exception as e:
                print(f"[ERROR] Intento {intento+1}: {e}")
                if intento < max_intentos - 1:
                    time.sleep(3)
                    continue
        
        return None
    
    def esperar_resultado(self, id_operacion, timeout=90):
        """Esperar resultado de operación usando check_win_v4"""
        print(f"[ESPERANDO] Verificando resultado de orden {id_operacion}...")
        
        try:
            # Usar check_win_v4 que tiene timeout integrado
            resultado, ganancia = self.bot.check_win_v4(id_operacion, timeout=timeout)
            
            if resultado is not None:
                return {
                    'estado': resultado,
                    'ganancia': ganancia
                }
            else:
                return {'estado': 'unknown', 'ganancia': 0}
                
        except Exception as e:
            print(f"[ERROR] Verificando resultado: {e}")
            return {'estado': 'error', 'ganancia': 0}
    
    def analizar_resultado(self, operacion, resultado, razon_decision):
        """Analizar por qué se ganó o perdió"""
        estado = resultado.get('estado', 'unknown')
        ganancia = resultado.get('ganancia', 0)
        
        if estado == 'won':
            self.wins += 1
            resultado_texto = "GANADA"
        elif estado == 'loss':
            self.losses += 1
            resultado_texto = "PERDIDA"
        else:
            resultado_texto = f"ESTADO: {estado}"
        
        analisis = {
            'timestamp': datetime.now().isoformat(),
            'activo': operacion['activo'],
            'direccion': operacion['direccion'],
            'razon': operacion['razon'],
            'resultado': resultado_texto,
            'ganancia': ganancia,
            'balance_actual': self.bot.get_balance()
        }
        
        self.operations_history.append(analisis)
        
        print("\n" + "="*60)
        print(f"  ANÁLISIS DE OPERACIÓN")
        print("="*60)
        print(f"Activo: {operacion['activo']}")
        print(f"Dirección: {operacion['direccion']}")
        print(f"Razón: {', '.join(operacion['razon'])}")
        print(f"Resultado: {resultado_texto}")
        print(f"Ganancia: ${ganancia}")
        
        return analisis
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas del bot"""
        total = self.wins + self.losses
        winrate = (self.wins / total * 100) if total > 0 else 0
        
        print("\n" + "="*60)
        print("  ESTADÍSTICAS DEL BOT")
        print("="*60)
        print(f"Operaciones totales: {total}")
        print(f"Ganadas: {self.wins}")
        print(f"Perdidas: {self.losses}")
        print(f"Win rate: {winrate:.1f}%")
        print(f"Balance actual: ${self.bot.get_balance()}")
        print(f"Balance inicial: ${self.balance_inicial}")
        print("="*60)
    
    def operativa(self, duracion_minutos=5):
        """Ejecutar operativa"""
        print(f"\n[INICIO] Operativa por {duracion_minutos} minutos...")
        print(f"[INFO] Activos: {ACTIVOS}")
        
        inicio = time.time()
        duracion = duracion_minutos * 60
        operacion_idx = 0
        
        while time.time() - inicio < duracion:
            operacion_idx += 1
            print(f"\n--- Operacion #{operacion_idx} ---")
            
            # Seleccionar activo
            activo = ACTIVOS[operacion_idx % len(ACTIVOS)]
            
            # Analizar mercado
            señal, razon, df = self.analizar_mercado(activo)
            
            if señal is None:
                print(f"[ESPERA] Sin señal clara para {activo}")
                time.sleep(30)
                continue
            
            print(f"[SEÑAL] {señal} - Razón: {razon}")
            
            # Ejecutar operación
            resultado_op = self.ejecutar_operacion(activo, señal)
            
            if not resultado_op or 'id' not in resultado_op:
                print("[ERROR] No se pudo ejecutar operación")
                time.sleep(30)
                continue
            
            # Esperar resultado
            resultado = self.esperar_resultado(resultado_op['id'], timeout=90)
            
            # Analizar resultado
            operacion = {'activo': activo, 'direccion': señal, 'razon': razon}
            self.analizar_resultado(operacion, resultado, razon)
            
            # Mostrar estadísticas
            self.mostrar_estadisticas()
            
            # Cooldown entre operaciones
            print("\n[ESPERA] 30 segundos antes de siguiente operación...")
            time.sleep(30)
        
        # Fin de operativa
        print("\n[FIN] Tiempo completado!")
        self.mostrar_estadisticas()
        
        # Guardar historial
        self.guardar_historial()
    
    def guardar_historial(self):
        """Guardar historial de operaciones"""
        if self.operations_history:
            archivo = f"historial_operaciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(archivo, 'w') as f:
                json.dump(self.operations_history, f, indent=2)
            print(f"[GUARDADO] Historial en {archivo}")

def main():
    print("="*60)
    print("  BOT TRADING EXNOVA - ANÁLISIS EN VIVO")
    print("="*60)
    
    bot = TradingBot()
    
    # Conectar
    if not bot.conectar():
        return
    
    # Cargar modelo
    bot.cargar_modelo()
    
    # Ejecutar operativa
    # Duración en minutos (entre 1-5 según preferencia)
    bot.operativa(duracion_minutos=5)

if __name__ == "__main__":
    main()
