"""Rule-based Factual Technical Analysis Summary Service for Vibe Trader AI."""
from datetime import datetime, timezone
from typing import List, Optional
from app.schemas.market import OHLCCandle
from app.schemas.analysis import (
    IndicatorsResponse,
    PatternsResponse,
    SupportResistanceResponse,
    AnalysisSummaryResponse
)


class AnalysisSummaryService:
    @staticmethod
    def generate_summary(
        symbol: str,
        market: str,
        timeframe: str,
        candles: List[OHLCCandle],
        indicators: IndicatorsResponse,
        patterns: PatternsResponse,
        sr: SupportResistanceResponse
    ) -> AnalysisSummaryResponse:
        current_price = candles[-1].close if candles else 0.0
        now_iso = datetime.now(timezone.utc).isoformat()

        # Extract latest indicator points
        latest_rsi: Optional[float] = None
        for pt in reversed(indicators.rsi):
            if pt.value is not None:
                latest_rsi = pt.value
                break

        latest_macd = None
        for pt in reversed(indicators.macd):
            if pt.macd is not None and pt.signal is not None:
                latest_macd = pt
                break

        latest_ema_9 = next((p.value for p in reversed(indicators.ema_9) if p.value is not None), None)
        latest_ema_21 = next((p.value for p in reversed(indicators.ema_21) if p.value is not None), None)
        latest_ema_50 = next((p.value for p in reversed(indicators.ema_50) if p.value is not None), None)
        latest_ema_200 = next((p.value for p in reversed(indicators.ema_200) if p.value is not None), None)
        latest_sma_50 = next((p.value for p in reversed(indicators.sma_50) if p.value is not None), None)
        latest_sma_200 = next((p.value for p in reversed(indicators.sma_200) if p.value is not None), None)
        latest_atr = next((p.value for p in reversed(indicators.atr) if p.value is not None), None)
        latest_bb = next((p for p in reversed(indicators.bollinger) if p.upper is not None and p.lower is not None), None)

        # 1. Determine Market Regime
        regime = "Neutral / Transitional"
        bullish_score = 0
        bearish_score = 0

        if latest_ema_50 and current_price > latest_ema_50:
            bullish_score += 1
        elif latest_ema_50 and current_price < latest_ema_50:
            bearish_score += 1

        if latest_ema_200 and current_price > latest_ema_200:
            bullish_score += 2
        elif latest_ema_200 and current_price < latest_ema_200:
            bearish_score += 2

        if latest_macd and latest_macd.histogram is not None:
            if latest_macd.histogram > 0:
                bullish_score += 1
            else:
                bearish_score += 1

        if latest_rsi:
            if latest_rsi >= 55:
                bullish_score += 1
            elif latest_rsi <= 45:
                bearish_score += 1

        if latest_bb and latest_bb.bandwidth is not None and latest_bb.bandwidth < 0.015:
            regime = "Consolidation / Volatility Squeeze"
        elif bullish_score >= 4:
            regime = "Bullish Momentum"
        elif bearish_score >= 4:
            regime = "Bearish Trend"
        elif bullish_score > bearish_score:
            regime = "Moderate Bullish Bias"
        elif bearish_score > bullish_score:
            regime = "Moderate Bearish Bias"
        else:
            regime = "Range-Bound Equilibrium"

        # 2. RSI Summary
        if latest_rsi is not None:
            if latest_rsi >= 70:
                rsi_summary = f"RSI(14) is at {latest_rsi:.1f} (Overbought territory). Momentum is strong but susceptible to pullback or cooling consolidation."
            elif latest_rsi <= 30:
                rsi_summary = f"RSI(14) is at {latest_rsi:.1f} (Oversold territory). Downside momentum is heavily stretched with potential for mean reversion."
            elif latest_rsi >= 50:
                rsi_summary = f"RSI(14) stands at {latest_rsi:.1f} above midline (50.0), indicating healthy bullish momentum without extreme exhaustion."
            else:
                rsi_summary = f"RSI(14) stands at {latest_rsi:.1f} below midline (50.0), showing prevailing bearish pressure and weak buying interest."
        else:
            rsi_summary = "RSI data insufficient for complete calculation period."

        # 3. MACD Summary
        if latest_macd is not None:
            hist = latest_macd.histogram or 0.0
            macd_val = latest_macd.macd or 0.0
            sig_val = latest_macd.signal or 0.0
            if hist > 0 and macd_val > sig_val:
                macd_summary = f"MACD line ({macd_val:.4f}) is above Signal line ({sig_val:.4f}) with positive histogram ({hist:+.4f}), signaling upward impulse."
            elif hist < 0 and macd_val < sig_val:
                macd_summary = f"MACD line ({macd_val:.4f}) is below Signal line ({sig_val:.4f}) with negative histogram ({hist:+.4f}), reflecting downward impulse."
            else:
                macd_summary = f"MACD histogram is converging ({hist:+.4f}) with MACD at {macd_val:.4f} and Signal at {sig_val:.4f}."
        else:
            macd_summary = "MACD data insufficient for calculation."

        # 4. Moving Average Summary
        ma_details = []
        if latest_ema_9 and latest_ema_21:
            if latest_ema_9 > latest_ema_21:
                ma_details.append(f"Short-term EMA 9 ({latest_ema_9:.2f}) is above EMA 21 ({latest_ema_21:.2f})")
            else:
                ma_details.append(f"Short-term EMA 9 ({latest_ema_9:.2f}) is below EMA 21 ({latest_ema_21:.2f})")

        if latest_ema_200:
            if current_price >= latest_ema_200:
                ma_details.append(f"Price is trading above long-term EMA 200 ({latest_ema_200:.2f})")
            else:
                ma_details.append(f"Price is trading below long-term EMA 200 ({latest_ema_200:.2f})")

        ma_summary = ". ".join(ma_details) if ma_details else "Moving average data calculated."

        # 5. Volatility Summary
        vol_details = []
        if latest_atr is not None and current_price > 0:
            atr_pct = (latest_atr / current_price) * 100
            vol_details.append(f"ATR(14) is {latest_atr:.4f} ({atr_pct:.2f}% of price), representing average candle dispersion")

        if latest_bb is not None:
            bw_pct = (latest_bb.bandwidth or 0.0) * 100
            if bw_pct < 2.0:
                vol_details.append(f"Bollinger Bands bandwidth is tight at {bw_pct:.2f}% indicating a volatility squeeze")
            else:
                vol_details.append(f"Bollinger Bands upper at {latest_bb.upper:.2f} and lower at {latest_bb.lower:.2f} (bandwidth: {bw_pct:.2f}%)")

        volatility_summary = ". ".join(vol_details) if vol_details else "Volatility calculations updated."

        # 6. Candlestick Patterns Summary
        recent_patterns = patterns.patterns[-5:] if patterns.patterns else []
        if recent_patterns:
            names = [f"{p.pattern_name} ({p.direction})" for p in recent_patterns]
            patterns_summary = f"{len(patterns.patterns)} pattern(s) identified in series. Recent setups: " + ", ".join(names) + "."
        else:
            patterns_summary = "No prominent classic candlestick reversal patterns identified in the examined candle window."

        # 7. Support & Resistance Summary
        supports = [z for z in sr.zones if z.zone_type == "Support"]
        resistances = [z for z in sr.zones if z.zone_type == "Resistance"]

        sr_details = []
        if resistances:
            nearest_res = min(resistances, key=lambda z: abs(z.price - current_price))
            pct_res = ((nearest_res.price - current_price) / current_price) * 100
            sr_details.append(f"Nearest resistance at {nearest_res.price:.2f} (+{pct_res:.2f}%, {nearest_res.strength} with {nearest_res.touches} touches)")

        if supports:
            nearest_sup = min(supports, key=lambda z: abs(z.price - current_price))
            pct_sup = ((current_price - nearest_sup.price) / current_price) * 100
            sr_details.append(f"Nearest support at {nearest_sup.price:.2f} (-{pct_sup:.2f}%, {nearest_sup.strength} with {nearest_sup.touches} touches)")

        sr_summary = ". ".join(sr_details) if sr_details else "Support and resistance clusters mapped across swing points."

        # 8. Detect Conflicting Signals
        conflicts: List[str] = []
        if latest_rsi is not None and latest_rsi >= 70 and latest_macd and latest_macd.histogram is not None and latest_macd.histogram > 0:
            conflicts.append("Oscillator Divergence: RSI indicates overbought extreme (>70), while MACD histogram remains expanding positively.")

        if latest_ema_200 and current_price > latest_ema_200:
            # Check for recent bearish reversal patterns
            recent_bearish = [p for p in recent_patterns if p.direction == "Bearish"]
            if recent_bearish:
                conflicts.append(f"Trend vs Pattern Conflict: Macro trend is above EMA 200, but recent bearish formation '{recent_bearish[-1].pattern_name}' suggests near-term friction.")

        if latest_ema_200 and current_price < latest_ema_200:
            recent_bullish = [p for p in recent_patterns if p.direction == "Bullish"]
            if recent_bullish:
                conflicts.append(f"Counter-Trend Warning: Bullish pattern '{recent_bullish[-1].pattern_name}' is developing beneath macro EMA 200 resistance.")

        if latest_rsi is not None and latest_rsi <= 35 and latest_ema_9 and latest_ema_21 and latest_ema_9 < latest_ema_21:
            conflicts.append("Oversold vs Trend: RSI approaches oversold bounce territory while short-term EMAs (9 & 21) maintain strict downward trajectory.")

        if not conflicts:
            conflicts.append("No critical indicator contradictions detected; oscillator direction aligns with short-term moving average structure.")

        # 9. Key Takeaways
        atr_display = f"{latest_atr:.4f}" if latest_atr is not None else "0.0000"
        key_takeaways: List[str] = [
            f"Overall technical regime evaluated as '{regime}' based on multi-timeframe moving averages and momentum oscillators.",
            f"Current market price ({current_price:.2f}) is positioned within the calculated Support & Resistance corridor.",
            f"Volatility measured by ATR(14) is {atr_display}, giving expected per-candle range."
        ]
        if recent_patterns:
            key_takeaways.append(f"Latest price action exhibits '{recent_patterns[-1].pattern_name}' ({recent_patterns[-1].direction}) signal.")

        return AnalysisSummaryResponse(
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            timestamp=now_iso,
            data_source="DEMO DATA (Simulated)",
            current_price=round(current_price, 4),
            regime=regime,
            rsi_summary=rsi_summary,
            macd_summary=macd_summary,
            ma_summary=ma_summary,
            volatility_summary=volatility_summary,
            patterns_summary=patterns_summary,
            sr_summary=sr_summary,
            key_takeaways=key_takeaways,
            conflicts=conflicts,
            disclaimer=(
                "FACTUAL TECHNICAL SUMMARY: Generated from rule-based calculations on simulated demo candles. "
                "Does not constitute financial advice, buy/sell recommendations, or guaranteed market performance."
            )
        )
