"""Reasoning Agent: Evaluates multi-factor evidence, detects conflicts, and quantifies uncertainty."""
import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import utcnow
from app.schemas.intelligence import ReasoningOutput, PerceptionOutput, AgentMetadata


class ReasoningAgent:
    """Logical agent combining indicators, isolating conflicting signals, and assessing trade viability."""

    NAME = "Reasoning Agent"
    VERSION = "1.0.0"

    @classmethod
    def evaluate(
        cls,
        perception: PerceptionOutput,
        ai_consolidated: Optional[dict] = None,
    ) -> ReasoningOutput:
        start_time = time.perf_counter()
        now = utcnow()

        if perception.missing_data_detected:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            meta = AgentMetadata(
                name=cls.NAME,
                version=cls.VERSION,
                status="BLOCKED",
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=now,
                error_detail="Perception data missing or stale; reasoning halted.",
            )
            return ReasoningOutput(
                agent=meta,
                symbol=perception.symbol,
                conforming_evidence=[],
                conflicting_signals=["Data feed incomplete or missing"],
                regime=perception.regime,
                uncertainty_score=1.0,
                uncertainty_factors=["Insufficient historical observations (< 20 candles)"],
                rationale="No-trade assessment: Insufficient candle observations to form a probabilistic thesis.",
                is_trade_viable=False,
                timestamp=now,
            )

        ind = perception.indicators
        rsi = ind.get("rsi_14")
        macd = ind.get("macd")
        signal = ind.get("signal")
        hist = ind.get("histogram")
        ema9 = ind.get("ema_9")
        ema21 = ind.get("ema_21")
        ema50 = ind.get("ema_50")
        price = perception.current_price

        conforming = []
        conflicting = []
        uncertainties = []

        # 1. EMA Trend alignment
        if ema9 and ema21 and ema50:
            if ema9 > ema21 > ema50:
                conforming.append(f"Bullish Moving Average Stack: EMA 9 ({ema9:.4f}) > EMA 21 ({ema21:.4f}) > EMA 50 ({ema50:.4f})")
            elif ema9 < ema21 < ema50:
                conflicting.append(f"Bearish Moving Average Stack: Short-term EMAs sloping downward below intermediate 50 EMA")
            elif ema9 > ema21:
                conforming.append("Short-term EMA 9 is above EMA 21")
            else:
                conflicting.append("Short-term EMA 9 is below EMA 21")

        # 2. RSI Momentum corridor check
        if rsi is not None:
            if 45.0 <= rsi <= 68.0:
                conforming.append(f"RSI(14) is {rsi:.1f} — Constructive momentum in non-overbought corridor")
            elif rsi > 70.0:
                conflicting.append(f"Overbought Risk: RSI(14) is {rsi:.1f} (> 70.0) — High risk of mean-reversion exhaustion")
                uncertainties.append("Overbought RSI indicates potential buyer exhaustion near highs")
            elif rsi < 30.0:
                conflicting.append(f"Severe Downtrend / Oversold: RSI(14) is {rsi:.1f} (< 30.0)")
                uncertainties.append("Oversold conditions may reflect strong downside momentum rather than immediate support")
            else:
                conforming.append(f"RSI(14) is {rsi:.1f} in neutral territory")

        # 3. MACD Momentum velocity
        if macd is not None and signal is not None:
            if macd > signal and (hist is not None and hist > 0):
                conforming.append(f"MACD line ({macd:.4f}) exceeds signal ({signal:.4f}) with positive histogram expansion")
            elif macd < signal:
                conflicting.append(f"MACD line ({macd:.4f}) below signal line ({signal:.4f}) — Negative momentum velocity")
                uncertainties.append("MACD bearish crossover signals downward acceleration")

        # 4. Candlestick patterns
        bullish_patterns = {"Hammer", "Inverted Hammer", "Bullish Engulfing", "Morning Star"}
        bearish_patterns = {"Shooting Star", "Bearish Engulfing", "Evening Star"}

        for p in perception.detected_patterns:
            if p in bullish_patterns:
                conforming.append(f"Bullish Candlestick Pattern detected: {p}")
            elif p in bearish_patterns:
                conflicting.append(f"Bearish Candlestick Reversal detected: {p}")
                uncertainties.append(f"Bearish candlestick ({p}) conflicts with prospective long entries")

        # 5. Resistance proximity friction
        if perception.resistance_zones:
            nearest_res = min(perception.resistance_zones)
            if nearest_res > price:
                buffer_pct = ((nearest_res - price) / price) * 100
                if buffer_pct < 0.5:
                    conflicting.append(f"Friction: Overhead resistance zone at ${nearest_res:.4f} is within {buffer_pct:.2f}% of current price")
                    uncertainties.append("Compressed upside ceiling before immediate major resistance zone")

        # Calculate uncertainty score (0.0 to 1.0)
        total_signals = max(1, len(conforming) + len(conflicting))
        conflict_ratio = len(conflicting) / total_signals
        uncertainty_score = min(1.0, max(0.0, conflict_ratio + (0.2 if len(uncertainties) > 0 else 0.0)))

        # Determine trade viability (Requires >= 2 conforming rules and uncertainty <= 0.40)
        is_viable = len(conforming) >= 2 and len(conflicting) <= 1 and uncertainty_score <= 0.40

        # Enrich uncertainties and rationale with consolidated AI synthesis if provided
        if ai_consolidated:
            for u in ai_consolidated.get("uncertainty_factors", []):
                if u not in uncertainties:
                    uncertainties.append(u)

        if is_viable:
            ai_note = f" (AI Synthesis: {ai_consolidated.get('ai_interpretation')})" if (ai_consolidated and ai_consolidated.get('ai_interpretation')) else ""
            rationale = (
                f"Multi-factor evidence confluence verified for {perception.symbol}. "
                f"{len(conforming)} conforming signals align in a {perception.regime} regime with low signal conflict "
                f"({len(conflicting)} minor contradiction). Asymmetric reward-to-risk profile supported.{ai_note}"
            )
        else:
            reasons_summary = ", ".join(conflicting[:2]) if conflicting else "Insufficient confluence strength"
            ai_note = f" (AI Synthesis: {ai_consolidated.get('ai_interpretation')})" if (ai_consolidated and ai_consolidated.get('ai_interpretation')) else ""
            rationale = (
                f"No-Trade Assessment: Evidence criteria not met for {perception.symbol}. "
                f"Signal friction detected ({reasons_summary}). "
                f"Uncertainty score is {uncertainty_score:.2f} — Capital preservation prioritized.{ai_note}"
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
        )

        return ReasoningOutput(
            agent=meta,
            symbol=perception.symbol,
            conforming_evidence=conforming,
            conflicting_signals=conflicting,
            regime=perception.regime,
            uncertainty_score=round(uncertainty_score, 2),
            uncertainty_factors=uncertainties,
            rationale=rationale,
            is_trade_viable=is_viable,
            timestamp=now,
        )
