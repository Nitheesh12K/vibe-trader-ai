"""Technical Indicators Calculation Service using Pandas and NumPy."""
from typing import List, Optional, Any
import numpy as np
import pandas as pd
from app.schemas.market import OHLCCandle
from app.schemas.analysis import (
    IndicatorValuePoint,
    MACDPoint,
    BollingerBandPoint,
    IndicatorsResponse,
)


class IndicatorsService:
    """Computes technical indicators on candlestick sequences."""

    @staticmethod
    def _candles_to_df(candles: List[OHLCCandle]) -> pd.DataFrame:
        if not candles:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        data = [
            {
                "time": c.time,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume) if c.volume is not None else 0.0,
            }
            for c in candles
        ]
        df = pd.DataFrame(data).sort_values("time").reset_index(drop=True)
        return df

    @classmethod
    def calculate_rsi(cls, df: pd.DataFrame, period: int = 14) -> List[IndicatorValuePoint]:
        """Calculate Relative Strength Index (RSI) using Wilder's smoothing."""
        if len(df) < period + 1:
            return [IndicatorValuePoint(time=int(t), value=None) for t in df["time"]]

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # Wilder's smoothing uses alpha = 1 / period
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        # Handle zero loss case (pure upward momentum)
        rsi = rsi.fillna(100.0).where(avg_loss == 0, rsi)

        points = []
        for t, val in zip(df["time"], rsi):
            clean_val = round(float(val), 2) if pd.notna(val) else None
            points.append(IndicatorValuePoint(time=int(t), value=clean_val))
        return points

    @classmethod
    def calculate_macd(
        cls, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> List[MACDPoint]:
        """Calculate Moving Average Convergence Divergence (MACD)."""
        if len(df) < slow:
            return [MACDPoint(time=int(t), macd=None, signal=None, histogram=None) for t in df["time"]]

        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        points = []
        for t, m, s, h in zip(df["time"], macd_line, signal_line, histogram):
            m_val = round(float(m), 4) if pd.notna(m) else None
            s_val = round(float(s), 4) if pd.notna(s) else None
            h_val = round(float(h), 4) if pd.notna(h) else None
            points.append(MACDPoint(time=int(t), macd=m_val, signal=s_val, histogram=h_val))
        return points

    @classmethod
    def calculate_ema(cls, df: pd.DataFrame, period: int) -> List[IndicatorValuePoint]:
        """Calculate Exponential Moving Average."""
        if len(df) < period:
            return [IndicatorValuePoint(time=int(t), value=None) for t in df["time"]]

        ema = df["close"].ewm(span=period, adjust=False).mean()
        points = []
        for t, val in zip(df["time"], ema):
            clean_val = round(float(val), 2) if pd.notna(val) else None
            points.append(IndicatorValuePoint(time=int(t), value=clean_val))
        return points

    @classmethod
    def calculate_sma(cls, df: pd.DataFrame, period: int) -> List[IndicatorValuePoint]:
        """Calculate Simple Moving Average."""
        if len(df) < period:
            return [IndicatorValuePoint(time=int(t), value=None) for t in df["time"]]

        sma = df["close"].rolling(window=period, min_periods=period).mean()
        points = []
        for t, val in zip(df["time"], sma):
            clean_val = round(float(val), 2) if pd.notna(val) else None
            points.append(IndicatorValuePoint(time=int(t), value=clean_val))
        return points

    @classmethod
    def calculate_atr(cls, df: pd.DataFrame, period: int = 14) -> List[IndicatorValuePoint]:
        """Calculate Average True Range (ATR)."""
        if len(df) < period + 1:
            return [IndicatorValuePoint(time=int(t), value=None) for t in df["time"]]

        prev_close = df["close"].shift(1)
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - prev_close).abs()
        tr3 = (df["low"] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        points = []
        for t, val in zip(df["time"], atr):
            clean_val = round(float(val), 2) if pd.notna(val) else None
            points.append(IndicatorValuePoint(time=int(t), value=clean_val))
        return points

    @classmethod
    def calculate_bollinger_bands(
        cls, df: pd.DataFrame, period: int = 20, num_std: float = 2.0
    ) -> List[BollingerBandPoint]:
        """Calculate Bollinger Bands (Middle, Upper, Lower, Bandwidth)."""
        if len(df) < period:
            return [
                BollingerBandPoint(time=int(t), upper=None, middle=None, lower=None, bandwidth=None)
                for t in df["time"]
            ]

        middle = df["close"].rolling(window=period, min_periods=period).mean()
        std = df["close"].rolling(window=period, min_periods=period).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        bandwidth = (upper - lower) / middle.replace(0, np.nan)

        points = []
        for t, u, m, l, bw in zip(df["time"], upper, middle, lower, bandwidth):
            u_val = round(float(u), 2) if pd.notna(u) else None
            m_val = round(float(m), 2) if pd.notna(m) else None
            l_val = round(float(l), 2) if pd.notna(l) else None
            bw_val = round(float(bw), 4) if pd.notna(bw) else None
            points.append(
                BollingerBandPoint(time=int(t), upper=u_val, middle=m_val, lower=l_val, bandwidth=bw_val)
            )
        return points

    @classmethod
    def calculate_vwap(cls, df: pd.DataFrame) -> List[IndicatorValuePoint]:
        """Calculate Volume-Weighted Average Price (VWAP)."""
        if len(df) == 0:
            return []

        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        pv = typical_price * df["volume"]
        cum_pv = pv.cumsum()
        cum_vol = df["volume"].cumsum()
        vwap = cum_pv / cum_vol.replace(0, np.nan)
        vwap = vwap.fillna(df["close"])

        points = []
        for t, val in zip(df["time"], vwap):
            clean_val = round(float(val), 2) if pd.notna(val) else None
            points.append(IndicatorValuePoint(time=int(t), value=clean_val))
        return points

    @classmethod
    def calculate_volume_sma(cls, df: pd.DataFrame, period: int = 20) -> List[IndicatorValuePoint]:
        """Calculate Simple Moving Average of Volume."""
        if len(df) < period:
            return [IndicatorValuePoint(time=int(t), value=None) for t in df["time"]]

        vol_sma = df["volume"].rolling(window=period, min_periods=period).mean()
        points = []
        for t, val in zip(df["time"], vol_sma):
            clean_val = round(float(val), 2) if pd.notna(val) else None
            points.append(IndicatorValuePoint(time=int(t), value=clean_val))
        return points

    @classmethod
    def compute_selected_indicators(cls, candles, symbol, timeframe, message):
        """Reuse indicator formulas, computing only the explicitly requested groups."""
        import re
        q = message.lower()
        names = {name for name in ["rsi", "macd", "ema", "sma", "atr", "vwap", "bollinger"] if re.search(r"\b" + name + r"\b", q)}
        if not names:
            return cls.compute_all_indicators(candles, symbol, timeframe)
        if "trend" in q:
            names.add("ema")
        df = cls._candles_to_df(candles)
        values = {field: [] for field in IndicatorsResponse.model_fields if field not in ["symbol", "timeframe", "is_mock"]}
        for name in names:
            if name in ["ema", "sma"]:
                for period in ([9, 21, 50, 200] if name == "ema" else [20, 50, 200]):
                    values[f"{name}_{period}"] = getattr(cls, f"calculate_{name}")(df, period)
            else:
                fn = "calculate_bollinger_bands" if name == "bollinger" else f"calculate_{name}"
                values[name] = getattr(cls, fn)(df)
        return IndicatorsResponse(symbol=symbol, timeframe=timeframe, **values)

    @classmethod
    def compute_all_indicators(
        cls,
        candles: List[OHLCCandle],
        symbol: str,
        timeframe: str = "1D",
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ) -> IndicatorsResponse:
        """Compute all requested indicators on candle series."""
        df = cls._candles_to_df(candles)

        return IndicatorsResponse(
            symbol=symbol,
            timeframe=timeframe,
            is_mock=True,
            rsi=cls.calculate_rsi(df, period=rsi_period),
            macd=cls.calculate_macd(df, fast=macd_fast, slow=macd_slow, signal=macd_signal),
            ema_9=cls.calculate_ema(df, period=9),
            ema_21=cls.calculate_ema(df, period=21),
            ema_50=cls.calculate_ema(df, period=50),
            ema_200=cls.calculate_ema(df, period=200),
            sma_20=cls.calculate_sma(df, period=20),
            sma_50=cls.calculate_sma(df, period=50),
            sma_200=cls.calculate_sma(df, period=200),
            atr=cls.calculate_atr(df, period=14),
            bollinger=cls.calculate_bollinger_bands(df, period=20, num_std=2.0),
            vwap=cls.calculate_vwap(df),
            volume_sma=cls.calculate_volume_sma(df, period=20),
        )


def calculate_indicators(candles: List[Any], symbol: str = "TEST", timeframe: str = "1D") -> IndicatorsResponse:
    """Convenience helper to compute indicators from candle dicts or objects."""
    ohlc_candles: List[OHLCCandle] = []
    for c in candles:
        if isinstance(c, dict):
            ohlc_candles.append(OHLCCandle(
                time=int(c.get("time", 0)),
                open=float(c.get("open", 0.0)),
                high=float(c.get("high", 0.0)),
                low=float(c.get("low", 0.0)),
                close=float(c.get("close", 0.0)),
                volume=float(c.get("volume", 0.0)) if c.get("volume") is not None else None,
            ))
        elif isinstance(c, OHLCCandle):
            ohlc_candles.append(c)
        else:
            ohlc_candles.append(OHLCCandle(
                time=int(getattr(c, "time", 0)),
                open=float(getattr(c, "open", 0.0)),
                high=float(getattr(c, "high", 0.0)),
                low=float(getattr(c, "low", 0.0)),
                close=float(getattr(c, "close", 0.0)),
                volume=float(getattr(c, "volume", 0.0)) if getattr(c, "volume", None) is not None else None,
            ))
    return IndicatorsService.compute_all_indicators(ohlc_candles, symbol, timeframe)

