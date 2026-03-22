"""
Simple PPO trainer for the binary options trading bot using the trading_gym environment.
"""
from typing import Optional
import gymnasium as gym
import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from gymnasium.wrappers import TimeLimit
from trading_gym import BinaryOptionsEnv
from core.feature_engineer import FeatureEngineerWrapper

def _make_env(data: pd.DataFrame, time_limit_steps: Optional[int] = None) -> gym.Env:
    """Construct a Gymnasium environment for the PPO agent."""
    fe = FeatureEngineerWrapper()
    env = BinaryOptionsEnv(data, fe)
    if time_limit_steps is not None:
        env = TimeLimit(env, max_episode_steps=time_limit_steps)
    return env

def train_ppo_on_dataframe(data: pd.DataFrame,
                           timesteps: int = 10000,
                           time_limit_steps: Optional[int] = None,
                           verbose: int = 1,
                           model_path: str = "ppo_trading_exnova"):
    """
    Train a PPO agent on the provided DataFrame of historical data.
    - data: DataFrame with historical OHLCV data. Must include 'close','open','high','low'.
    - timesteps: total number of environment steps for training.
    - time_limit_steps: optional per-episode step limit.
    - model_path: where to save the trained model.
    """
    env = _make_env(data, time_limit_steps)
    # Basic env check
    try:
        check_env(env, warn=True)
    except Exception:
        pass
    # Wrap with vectorized env
    from stable_baselines3.common.vec_env import DummyVecEnv
    vec_env = DummyVecEnv([lambda: env])
    model = PPO("MlpPolicy", vec_env, verbose=verbose)
    model.learn(total_timesteps=timesteps)
    model.save(model_path)
    return model

def load_trained_model(model_path: str = "ppo_trading_exnova"):
    """Load a previously saved PPO model."""
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    # Reconstruct a minimal env; user should supply data when running a real eval
    dummy_df = pd.DataFrame(columns=['open','high','low','close'])
    env = BinaryOptionsEnv(dummy_df, FeatureEngineerWrapper())
    vec_env = DummyVecEnv([lambda: env])
    model = PPO.load(model_path, env=vec_env)
    return model

def demo_run(model, data: pd.DataFrame, max_steps: int = 100):
    """Run a quick evaluation run with the given model on the data."""
    from stable_baselines3.common.vec_env import DummyVecEnv
    fe = FeatureEngineerWrapper()
    env = BinaryOptionsEnv(data, fe)
    vec_env = DummyVecEnv([lambda: env])
    obs, _ = env.reset()
    total_reward = 0.0
    for _ in range(min(max_steps, len(data) - 1)):
        action, _states = model.predict(obs, deterministic=True)
        action_val = int(np.asarray(action).flatten()[0])
        obs, reward, done, trunc, info = env.step(action_val)
        total_reward += float(reward)
        if done:
            break
    return total_reward
