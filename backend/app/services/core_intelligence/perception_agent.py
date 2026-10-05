"""Perception Agent: Collects, validates, and normalizes market observations."""
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.entities import utcnow
from app.schemas.intelligence import PerceptionOutput, AgentMetadata
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService


class PerceptionAgent:
    """Logical agent collecting and normalizing market data without fabrication."""

    NAME = "Perception Agent"
    VERSION = "1.0.0"

    @classmethod
    def perceive(
        cls,
        db: Session,
        symbol: str = "EUR/USD",
        market: str = "FOREX",
        timeframe: str = "1D",
    ) -> PerceptionOutput:
        start_time = time.perf_counter()
        now = utcnow()

        market_service = MarketDataService(db=db)
        ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
        candles = ohlc.candles or []

        missing_data = False
        if len(candles) < 20:
            missing_data = True

        current_price = candles[-1].close if candles else 100.0

        # Calculate data freshness
        if candles:
            last_candle_epoch = candles[-1].time
            current_epoch = int(now.timestamp())
            freshness_seconds = max(0.0, float(current_epoch - last_candle_epoch))
        else:
            freshness_seconds = 999999.0

        # Technical computations
        indicators_data = {}
        patterns_list = []
        supports = []
        resistances = []
        regime = "Range-Bound"

        if len(candles) >= 5:
            indicators_res = IndicatorsService.compute_all_indicators(candles=candles, symbol=symbol, timeframe=timeframe)
            patterns_res = PatternService.detect_patterns(candles=candles, symbol=symbol, timeframe=timeframe)
            sr_res = SupportResistanceService.calculate_zones(candles=candles, symbol=symbol, timeframe=timeframe)

            last_rsi = indicators_res.rsi[-1].value if indicators_res.rsi else None
            last_macd = indicators_res.macd[-1].macd if indicators_res.macd else None
            last_signal = indicators_res.macd[-1].signal if indicators_res.macd else None
            last_hist = indicators_res.macd[-1].histogram if indicators_res.macd else None
            last_ema9 = indicators_res.ema_9[-1].value if indicators_res.ema_9 else None
            last_ema21 = indicators_res.ema_21[-1].value if indicators_res.ema_21 else None
            last_ema50 = indicators_res.ema_50[-1].value if indicators_res.ema_50 else None
            last_atr = indicators_res.atr[-1].value if indicators_res.atr else None

            indicators_data = {
                "rsi_14": last_rsi,
                "macd": last_macd,
                "signal": last_signal,
                "histogram": last_hist,
                "ema_9": last_ema9,
                "ema_21": last_ema21,
                "ema_50": last_ema50,
                "atr_14": last_atr,
            }

            patterns_list = [p.pattern_name for p in patterns_res.patterns]
            supports = [z.price for z in sr_res.zones if z.zone_type == "Support"]
            resistances = [z.price for z in sr_res.zones if z.zone_type == "Resistance"]

            # Classify regime deterministically
            if last_ema9 and last_ema21 and last_ema50:
                if last_ema9 > last_ema21 > last_ema50 and (last_rsi and last_rsi > 50):
                    regime = "Bullish Momentum Trend"
                elif last_ema9 < last_ema21 < last_ema50 and (last_rsi and last_rsi < 50):
                    regime = "Bearish Downtrend"
                elif last_rsi and 45 <= last_rsi <= 55:
                    regime = "Consolidation / Low Volatility Squeeze"
                else:
                    regime = "Range-Bound Mean Reversion"

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED" if not missing_data else "BLOCKED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
            error_detail="Insufficient candle count (< 20 candles)" if missing_data else None,
        )

        return PerceptionOutput(
            agent=meta,
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            current_price=round(current_price, 4),
            candle_count=len(candles),
            indicators=indicators_data,
            detected_patterns=patterns_list,
            support_zones=supports[:5],
            resistance_zones=resistances[:5],
            regime=regime,
            data_freshness_seconds=round(freshness_seconds, 1),
            missing_data_detected=missing_data,
            data_source=f"DEMO_FEED ({market})",
            timestamp=now,
        )
