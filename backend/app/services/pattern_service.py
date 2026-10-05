"""Rule-based Candlestick Pattern Detection Service for Vibe Trader AI."""
from typing import List
from app.schemas.market import OHLCCandle
from app.schemas.analysis import PatternItem, PatternsResponse


class PatternService:
    @staticmethod
    def detect_patterns(candles: List[OHLCCandle], symbol: str = "UNKNOWN", timeframe: str = "1h") -> PatternsResponse:
        """
        Scans a sequence of OHLC candles for classic candlestick patterns:
        - Doji
        - Hammer
        - Inverted Hammer
        - Bullish Engulfing
        - Bearish Engulfing
        - Morning Star
        - Evening Star
        - Shooting Star
        """
        detected: List[PatternItem] = []
        n = len(candles)
        if n == 0:
            return PatternsResponse(symbol=symbol, timeframe=timeframe, total_detected=0, patterns=[])

        for i in range(n):
            curr = candles[i]
            body = abs(curr.close - curr.open)
            candle_range = curr.high - curr.low
            upper_shadow = curr.high - max(curr.open, curr.close)
            lower_shadow = min(curr.open, curr.close) - curr.low
            is_bullish = curr.close > curr.open
            is_bearish = curr.close < curr.open

            # Avoid zero range divisions
            if candle_range <= 0.000001:
                continue

            # 1. Doji (Indecision)
            if body <= (candle_range * 0.10):
                detected.append(PatternItem(
                    pattern_name="Doji",
                    time=curr.time,
                    candle_index=i,
                    direction="Neutral",
                    reliability="Medium",
                    explanation="Doji candle where open and close prices are nearly identical, indicating buyer-seller equilibrium and indecision."
                ))

            # 2. Hammer & Inverted Hammer & Shooting Star
            if 0 < body <= (candle_range * 0.35):
                # Hammer: small body at top, lower shadow >= 1.9x body, upper shadow <= 0.35x body
                if lower_shadow >= (1.9 * body) and upper_shadow <= (0.35 * body):
                    detected.append(PatternItem(
                        pattern_name="Hammer",
                        time=curr.time,
                        candle_index=i,
                        direction="Bullish",
                        reliability="High",
                        explanation="Hammer pattern with a long lower shadow rejecting downside prices and a small body closing near the candle high."
                    ))

                # Upper shadow >= 1.9x body and lower shadow <= 0.35x body
                elif upper_shadow >= (1.9 * body) and lower_shadow <= (0.35 * body):
                    # Check context: if preceded by an upward push -> Shooting Star; else Inverted Hammer
                    prior_trend = 0.0
                    if i >= 2:
                        prior_trend = candles[i-1].close - candles[max(0, i-3)].open

                    if prior_trend >= 0 or (i >= 1 and curr.open >= candles[i-1].close and is_bearish):
                        detected.append(PatternItem(
                            pattern_name="Shooting Star",
                            time=curr.time,
                            candle_index=i,
                            direction="Bearish",
                            reliability="High",
                            explanation="Shooting Star pattern with an extended upper wick reflecting sharp seller rejection after an upward price test."
                        ))
                    else:
                        detected.append(PatternItem(
                            pattern_name="Inverted Hammer",
                            time=curr.time,
                            candle_index=i,
                            direction="Bullish",
                            reliability="Medium",
                            explanation="Inverted Hammer pattern showing strong buyer test upwards during the session before consolidating near the low."
                        ))

            # 3. Two-candle patterns: Engulfing
            if i >= 1:
                prev = candles[i-1]
                prev_body = abs(prev.close - prev.open)
                prev_bullish = prev.close > prev.open
                prev_bearish = prev.close < prev.open

                # Bullish Engulfing: prev is red, curr is green, curr body wraps prev body
                if prev_bearish and is_bullish and prev_body > 0.000001:
                    if curr.open <= prev.close and curr.close >= prev.open and (curr.close - curr.open) > prev_body:
                        detected.append(PatternItem(
                            pattern_name="Bullish Engulfing",
                            time=curr.time,
                            candle_index=i,
                            direction="Bullish",
                            reliability="High",
                            explanation="Bullish Engulfing formation: large green candle completely engulfs the preceding red body, signaling buyer takeover."
                        ))

                # Bearish Engulfing: prev is green, curr is red, curr body wraps prev body
                if prev_bullish and is_bearish and prev_body > 0.000001:
                    if curr.open >= prev.close and curr.close <= prev.open and (curr.open - curr.close) > prev_body:
                        detected.append(PatternItem(
                            pattern_name="Bearish Engulfing",
                            time=curr.time,
                            candle_index=i,
                            direction="Bearish",
                            reliability="High",
                            explanation="Bearish Engulfing formation: large red candle completely engulfs the preceding green body, signaling aggressive selling pressure."
                        ))

            # 4. Three-candle patterns: Morning Star & Evening Star
            if i >= 2:
                c1 = candles[i-2]
                c2 = candles[i-1]
                c3 = curr

                c1_body = abs(c1.close - c1.open)
                c2_body = abs(c2.close - c2.open)
                c3_body = abs(c3.close - c3.open)

                # Morning Star:
                if c1.close < c1.open and c1_body > 0.000001:
                    if c2_body <= (c1_body * 0.5) and min(c2.open, c2.close) <= c1.close:
                        if c3.close > c3.open and c3.close >= (c1.close + c1_body * 0.5):
                            detected.append(PatternItem(
                                pattern_name="Morning Star",
                                time=c3.time,
                                candle_index=i,
                                direction="Bullish",
                                reliability="High",
                                explanation="Morning Star 3-candle reversal: long red candle, small indecisive bottom candle, and strong green candle penetrating past 50% of the first candle."
                            ))

                # Evening Star:
                if c1.close > c1.open and c1_body > 0.000001:
                    if c2_body <= (c1_body * 0.5) and max(c2.open, c2.close) >= c1.close:
                        if c3.close < c3.open and c3.close <= (c1.open + c1_body * 0.5):
                            detected.append(PatternItem(
                                pattern_name="Evening Star",
                                time=c3.time,
                                candle_index=i,
                                direction="Bearish",
                                reliability="High",
                                explanation="Evening Star 3-candle reversal: extended green candle, small indecisive top star, and decisive red candle retracing over 50% of the initial rally."
                            ))

        return PatternsResponse(
            symbol=symbol,
            timeframe=timeframe,
            total_detected=len(detected),
            patterns=detected
        )
