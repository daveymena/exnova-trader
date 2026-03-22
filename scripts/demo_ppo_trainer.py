"""
Demo script: train a PPO agent on synthetic OHLCV data and run a quick evaluation.
This is a self-contained Python script to validate the Python-based PPO training flow
without requiring live trading credentials.
"""
import numpy as np
import pandas as pd
from pathlib import Path

from core.learning.ppo_trainer import train_ppo_on_dataframe, demo_run
from core.feature_engineer import FeatureEngineerWrapper
from trading_gym import BinaryOptionsEnv


def _synthetic_ohlcv(n_steps: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    price = 100.0
    rows = []
    for _ in range(n_steps):
        open_p = price
        # small random walk
        delta = rng.normal(0, 0.8)
        close_p = max(0.1, open_p + delta)
        high_p = max(open_p, close_p) + rng.uniform(0.0, 0.6)
        low_p = min(open_p, close_p) - rng.uniform(0.0, 0.6)
        rows.append({"open": open_p, "high": high_p, "low": low_p, "close": close_p})
        price = close_p
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    return df


def main():
    # Paso 1: crear datos sintéticos
    data = _synthetic_ohlcv(n_steps=600, seed=123)
    print("[demo] Datos sintéticos creados:", data.shape)

    # Paso 2: entrenar PPO en los datos sintéticos
    model_path = "demo_ppo_trading_exnova"
    print("[demo] Iniciando entrenamiento PPO (datos sintéticos)...")
    model = train_ppo_on_dataframe(data, timesteps=2000, model_path=model_path, verbose=0)
    print("[demo] Entrenamiento PPO completado. Modelo guardado en:", model_path)

    # Paso 3: evaluación rápida
    print("[demo] Ejecutando evaluación rápida...")
    total_reward = demo_run(model, data, max_steps=min(200, len(data) - 1))
    print(f"[demo] Recompensa total de la prueba: {total_reward:.2f}")

if __name__ == "__main__":
    main()
