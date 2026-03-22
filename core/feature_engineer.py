import numpy as np
import pandas as pd
from strategies.technical import FeatureEngineer

class FeatureEngineerWrapper:
    """
    Compatibility wrapper to expose engineer_features(data) method
    compatible with BinaryOptionsEnv observation pipeline.
    """
    def __init__(self):
        self._fe = FeatureEngineer()

    def engineer_features(self, df: pd.DataFrame):
        """
        Produce a 1D numpy array of 20 features for the RL agent.
        This is a compatibility shim around prepare_for_rl() in strategies.
        """
        try:
            df_with_features = self._fe.prepare_for_rl(df)
            if df_with_features is None or df_with_features.empty:
                return np.zeros((20,), dtype=np.float32)

            # Try to collect a fixed set of indicators if present
            cols = [
                'rsi', 'macd', 'macd_signal', 'macd_diff', 'bb_high', 'bb_low',
                'bb_width', 'sma_20', 'sma_50', 'atr',
                'pattern_hammer', 'pattern_bullish_engulfing'
            ]
            last = df_with_features.tail(1)
            values = []
            for c in cols:
                if c in last.columns:
                    v = float(last.iloc[0][c])
                    if np.isnan(v) or np.isinf(v):
                        v = 0.0
                else:
                    v = 0.0
                values.append(v)
            obs = np.array(values, dtype=np.float32)
            if obs.shape[0] < 20:
                obs = np.pad(obs, (0, 20 - obs.shape[0]))
            elif obs.shape[0] > 20:
                obs = obs[:20]
            return obs
        except Exception as e:
            # Fallback safe vector
            return np.zeros((20,), dtype=np.float32)
