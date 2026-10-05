"""XGBoost Causal Feature Engineering and Target Formulation Pipeline.
Strictly causal: All features at candle t use data available at or before t.
Target at t represents next-bar price direction: Y_t = 1 if Close[t+1] > Close[t] else 0.
Zero lookahead bias and target-boundary purge safeguards.
"""
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from app.schemas.market import OHLCCandle

logger = logging.getLogger("vibe-trader-ai.xgboost_pipeline")

FEATURE_SCHEMA_VERSION = "2.0.0-causal"

FEATURE_NAMES = [
    "rsi_14",
    "macd_hist_norm",
    "ema_spread_9_21",
    "ema_trend_50",
    "atr_norm_14",
    "volume_ratio_20",
    "bb_pct_b",
    "return_1bar",
    "return_5bar",
]


@dataclass
class FeaturePipelineResult:
    features_df: pd.DataFrame
    targets: pd.Series
    timestamps: pd.Series
    feature_names: List[str]
    total_candles: int
    usable_rows: int
    dropped_warmup_rows: int
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    feature_schema_version: str = FEATURE_SCHEMA_VERSION


class XGBoostFeaturePipeline:
    """Constructs causal features and next-bar targets from chronological OHLCV candle feeds."""

    FEATURE_SCHEMA_VERSION: str = FEATURE_SCHEMA_VERSION

    @staticmethod
    def validate_and_clean_candles(candles: List[OHLCCandle]) -> pd.DataFrame:
        """Validates OHLCV integrity, deduplicates timestamps, and ensures chronological sorting."""
        if not candles:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        rows = []
        for c in candles:
            t = int(getattr(c, "time", 0))
            o = float(getattr(c, "open", 0.0))
            h = float(getattr(c, "high", 0.0))
            l = float(getattr(c, "low", 0.0))
            cl = float(getattr(c, "close", 0.0))
            vol = float(getattr(c, "volume", 0.0)) if getattr(c, "volume", None) is not None else 0.0

            # Reject non-sensical prices
            if h >= l and o >= 0.0 and cl >= 0.0 and h >= 0.0 and l >= 0.0 and not math.isnan(cl):
                rows.append({"time": t, "open": o, "high": h, "low": l, "close": cl, "volume": vol})

        if not rows:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(rows)
        # Deduplicate on time (keep last update) and sort strictly ascending
        df = df.drop_duplicates(subset=["time"], keep="last").sort_values("time").reset_index(drop=True)
        return df

    @classmethod
    def extract_features_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Computes the 9 strictly causal features for every bar in df."""
        if len(df) < 55:
            # Need at least 50 bars for 50-EMA + 5 bars return
            raise ValueError(f"Insufficient historical candles ({len(df)}). Minimum required for causal warmup is 55.")

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]
        close_safe = close.replace(0.0, np.nan)

        # 1. RSI-14 (Wilder's smoothing)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1.0 / 14.0, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / 14.0, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi_14 = 100.0 - (100.0 / (1.0 + rs))
        rsi_14 = rsi_14.fillna(50.0).where(avg_loss != 0, 100.0)

        # 2. MACD Histogram Normalized: (MACD_12_26 - Signal_9) / Close
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - macd_signal
        macd_hist_norm = (macd_hist / close_safe).fillna(0.0)

        # 3. EMA Spread (9 vs 21): (EMA_9 - EMA_21) / Close
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_spread_9_21 = ((ema_9 - ema_21) / close_safe).fillna(0.0)

        # 4. EMA Trend (50): (Close - EMA_50) / Close
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_trend_50 = ((close - ema_50) / close_safe).fillna(0.0)

        # 5. ATR Normalized (14): ATR_14 / Close
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.ewm(alpha=1.0 / 14.0, min_periods=14, adjust=False).mean()
        atr_norm_14 = (atr_14 / close_safe).fillna(0.01)

        # 6. Volume Ratio (20): Volume / SMA_20(Volume)
        vol_sma_20 = volume.rolling(window=20, min_periods=5).mean().replace(0.0, np.nan)
        volume_ratio_20 = (volume / vol_sma_20).fillna(1.0).clip(0.0, 10.0)

        # 7. Bollinger Band %B: (Close - Lower) / (Upper - Lower)
        sma_20 = close.rolling(window=20, min_periods=20).mean()
        rolling_std = close.rolling(window=20, min_periods=20).std()
        upper_bb = sma_20 + (rolling_std * 2.0)
        lower_bb = sma_20 - (rolling_std * 2.0)
        bb_width = (upper_bb - lower_bb).replace(0.0, np.nan)
        bb_pct_b = ((close - lower_bb) / bb_width).fillna(0.5).clip(-0.5, 1.5)

        # 8. Return 1-bar: Close[t] / Close[t-1] - 1
        return_1bar = (close / close.shift(1) - 1.0).fillna(0.0)

        # 9. Return 5-bar: Close[t] / Close[t-5] - 1
        return_5bar = (close / close.shift(5) - 1.0).fillna(0.0)

        features_df = pd.DataFrame({
            "rsi_14": rsi_14,
            "macd_hist_norm": macd_hist_norm,
            "ema_spread_9_21": ema_spread_9_21,
            "ema_trend_50": ema_trend_50,
            "atr_norm_14": atr_norm_14,
            "volume_ratio_20": volume_ratio_20,
            "bb_pct_b": bb_pct_b,
            "return_1bar": return_1bar,
            "return_5bar": return_5bar,
        })

        return features_df

    @classmethod
    def build_training_dataset(
        cls,
        candles: List[OHLCCandle],
        warmup_bars: int = 50,
    ) -> FeaturePipelineResult:
        """Constructs aligned training (X_t, Y_t) pairs where Y_t is next-bar direction.
        The last candle is dropped from training because its target Close[t+1] is in the future.
        """
        df = cls.validate_and_clean_candles(candles)
        total_candles = len(df)
        if total_candles < (warmup_bars + 10):
            raise ValueError(
                f"Insufficient historical data: {total_candles} candles provided. "
                f"Need at least {warmup_bars + 10} candles to generate valid causal features and targets."
            )

        features_full = cls.extract_features_df(df)

        # Target Formulation: Y_t = 1 if Close[t+1] > Close[t] else 0
        future_close = df["close"].shift(-1)
        targets_full = (future_close > df["close"]).astype(int)

        # Drop warmup rows (where 50-EMA and rolling indicators were initializing)
        # Also drop the final row (since future_close is NaN for the latest bar)
        valid_indices = df.index[warmup_bars:-1]

        X = features_full.loc[valid_indices].reset_index(drop=True)
        y = targets_full.loc[valid_indices].reset_index(drop=True)
        timestamps = df["time"].loc[valid_indices].reset_index(drop=True)

        class_1_count = int(y.sum())
        class_0_count = int(len(y) - class_1_count)
        diagnostics = {
            "total_candles": total_candles,
            "usable_pairs": len(X),
            "dropped_warmup": warmup_bars,
            "target_distribution": {
                "UP (1)": class_1_count,
                "DOWN/FLAT (0)": class_0_count,
                "bullish_ratio": round(class_1_count / max(1, len(y)), 4),
            },
            "start_timestamp": int(timestamps.iloc[0]) if len(timestamps) > 0 else 0,
            "end_timestamp": int(timestamps.iloc[-1]) if len(timestamps) > 0 else 0,
            "columns": FEATURE_NAMES,
        }

        return FeaturePipelineResult(
            features_df=X,
            targets=y,
            timestamps=timestamps,
            feature_names=FEATURE_NAMES,
            total_candles=total_candles,
            usable_rows=len(X),
            dropped_warmup_rows=warmup_bars,
            diagnostics=diagnostics,
        )

    @classmethod
    def extract_single_inference_vector(
        cls,
        candles: List[OHLCCandle],
        max_lookback: int = 120,
    ) -> Tuple[Dict[str, float], int]:
        """Extracts the single feature vector at the latest completed candle for real-time advisory inference.
        Uses historical candles ending at index -1 without future target requirement.
        """
        df = cls.validate_and_clean_candles(candles)
        if len(df) < 55:
            raise ValueError(f"Need at least 55 completed candles for causal indicator calculation. Got {len(df)}.")

        # Take tail lookback for fast computation while ensuring 50-EMA warmup
        df_slice = df.tail(max_lookback).reset_index(drop=True)
        features_df = cls.extract_features_df(df_slice)

        latest_features = features_df.iloc[-1].to_dict()
        latest_timestamp = int(df_slice["time"].iloc[-1])
        return latest_features, latest_timestamp

    @classmethod
    def validate_feature_schema(cls, model_schema_version: str) -> bool:
        """Validates that a model artifact's feature schema version matches the active pipeline.
        Rejects mismatched versions to prevent data leakage and distributional shifts.
        """
        if not model_schema_version:
            raise ValueError("Model feature schema version is missing or empty.")
        if model_schema_version != FEATURE_SCHEMA_VERSION:
            raise ValueError(
                f"Feature schema version mismatch: model expects '{model_schema_version}', "
                f"but feature pipeline version is '{FEATURE_SCHEMA_VERSION}'."
            )
        return True

    @staticmethod
    def classify_market_regime(
        ema_spread: float,
        ema_trend: float,
        atr_norm: float,
        bb_pct_b: float,
        atr_threshold_high: float = 0.025,
    ) -> str:
        """
        Causal regime classifier strictly using features available at or before candle t:
        - HIGH_VOLATILITY_EXPANSION: Normalized ATR exceeds volatility threshold (> 2.5% of price).
        - TRENDING_BULLISH: 50-EMA trend is positive and 9/21 EMA spread is bullish.
        - TRENDING_BEARISH: 50-EMA trend is negative and 9/21 EMA spread is bearish.
        - RANGING_LOW_VOLATILITY: Moderate ATR with intertwined or flat moving averages.
        """
        if atr_norm > atr_threshold_high:
            return "HIGH_VOLATILITY_EXPANSION"
        if ema_trend > 0.005 and ema_spread > 0.002:
            return "TRENDING_BULLISH"
        if ema_trend < -0.005 and ema_spread < -0.002:
            return "TRENDING_BEARISH"
        return "RANGING_LOW_VOLATILITY"

    @classmethod
    def classify_regimes_for_dataframe(
        cls,
        features_df: pd.DataFrame,
    ) -> pd.Series:
        """Classifies each row of a feature dataframe into a market regime strictly causally."""
        regimes = []
        for _, row in features_df.iterrows():
            regime = cls.classify_market_regime(
                ema_spread=float(row.get("ema_spread_9_21", 0.0)),
                ema_trend=float(row.get("ema_trend_50", 0.0)),
                atr_norm=float(row.get("atr_norm_14", 0.015)),
                bb_pct_b=float(row.get("bb_pct_b", 0.5)),
            )
            regimes.append(regime)
        return pd.Series(regimes, index=features_df.index, name="regime")
