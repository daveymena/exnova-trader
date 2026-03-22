"""
Script para conectar a Exnova en modo PRACTICE y entrenar el bot PPO
"""
import os
import sys
import time
import pandas as pd
import numpy as np

sys.path.insert(0, '/bot-reversiones-iq')

from exnovaapi.stable_api import Exnova
from core.learning.ppo_trainer import train_ppo_on_dataframe, demo_run
from core.feature_engineer import FeatureEngineerWrapper

EMAIL = "daveymena16@gmail.com"
PASSWORD = "6715320Dvd."
ACTIVOS = ["EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC"]
INTERVALO = 60
CANTIDAD_VELAS = 200

def conectar_exnova():
    """Conectar a Exnova en modo PRACTICE"""
    print("[EXNOVA] Conectando en modo PRACTICE...")
    bot = Exnova(EMAIL, PASSWORD, active_account_type="PRACTICE")
    
    check, reason = bot.connect()
    
    if check:
        print("[EXNOVA] Conectado exitosamente!")
        return bot
    else:
        print(f"[EXNOVA] Error al conectar: {reason}")
        return None

def obtener_velas(bot, activo, intervalo=60, cantidad=200):
    """Obtener velas históricas de un activo"""
    print(f"[EXNOVA] Obteniendo {cantidad} velas de {activo}...")
    
    try:
        candles = bot.get_candles(activo, intervalo, cantidad, time.time())
        
        if candles and len(candles) > 0:
            # Las velas vienen como diccionarios
            print(f"[EXNOVA] Primera vela: {candles[0]}")
            
            # Convertir a DataFrame con formato estándar
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
            print(f"[EXNOVA] Obtenidas {len(df)} velas para {activo}")
            return df
        else:
            print(f"[EXNOVA] No se obtuvieron velas para {activo}")
            return None
    except Exception as e:
        print(f"[EXNOVA] Error obteniendo velas: {e}")
        import traceback
        traceback.print_exc()
        return None

def obtener_balance(bot):
    """Obtener el balance de la cuenta"""
    try:
        balance = bot.get_balance()
        print(f"[EXNOVA] Balance actual: ${balance}")
        return balance
    except Exception as e:
        print(f"[EXNOVA] Error obteniendo balance: {e}")
        return None

def main():
    print("="*60)
    print("  BOT TRADING EXNOVA - MODO PRACTICE")
    print("="*60)
    
    # Conectar a Exnova
    bot = conectar_exnova()
    if not bot:
        print("[ERROR] No se pudo conectar a Exnova")
        return
    
    # Obtener balance
    obtener_balance(bot)
    
    # Recolectar datos de entrenamiento
    todos_datos = []
    for activo in ACTIVOS:
        df = obtener_velas(bot, activo, INTERVALO, CANTIDAD_VELAS)
        if df is not None and len(df) > 50:
            df['activo'] = activo
            todos_datos.append(df)
        time.sleep(1)  # Esperar entre solicitudes
    
    if not todos_datos:
        print("[ERROR] No se pudieron obtener datos para entrenar")
        return
    
    # Combinar todos los datos
    datos_entrenamiento = pd.concat(todos_datos, ignore_index=True)
    print(f"[DATOS] Total de velas para entrenamiento: {len(datos_entrenamiento)}")
    
    # Entrenar PPO
    print("\n[PPO] Iniciando entrenamiento...")
    model_path = "exnova_ppo_model"
    model = train_ppo_on_dataframe(
        datos_entrenamiento, 
        timesteps=2000,  # Reducido para prueba rápida
        model_path=model_path, 
        verbose=0
    )
    print("[PPO] Entrenamiento completado!")
    
    # Evaluar con datos
    print("\n[EVALUACION] Ejecutando evaluación...")
    datos_eval = todos_datos[0]  # Usar primer activo para evaluación
    recompensa = demo_run(model, datos_eval, max_steps=min(100, len(datos_eval)-1))
    print(f"[EVALUACION] Recompensa total: {recompensa:.2f}")
    
    # Obtener balance final
    print("\n" + "="*60)
    obtener_balance(bot)
    print("="*60)
    
    # Cerrar conexión
    try:
        bot.api.close()
        print("[EXNOVA] Conexión cerrada")
    except:
        pass
    
    print("\n[OK] Proceso completado!")

if __name__ == "__main__":
    main()
