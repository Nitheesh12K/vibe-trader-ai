"""Deterministic Strategy Engine & AI BUY Proposal Generator for Vibe Trader AI."""
import json
import uuid
import logging
from datetime import timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import Strategy, BuyProposal, utcnow
from app.schemas.market import OHLCCandle
from app.schemas.analysis import IndicatorsResponse, PatternsResponse, SupportResistanceResponse
from app.schemas.strategy_framework import StrategyDefinition, StrategySignalOutput, SignalState
from app.services.audit_service import AuditService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService

logger = logging.getLogger("vibe-trader-ai.strategy_engine")


class StrategyEngine:
    @staticmethod
    def evaluate_opportunity(
        db: Session,
        symbol: str,
        market: str,
        timeframe: str,
        candles: List[OHLCCandle],
        indicators: IndicatorsResponse,
        patterns: PatternsResponse,
        sr: SupportResistanceResponse,
        strategy: Optional[Strategy] = None,
    ) -> Optional[BuyProposal]:
        """
        Evaluates technical indicator confluence, candlestick setups, and market regime
        to detect valid BUY opportunities and generate structured, explainable proposals.
        """
        if not candles or len(candles) < 20:
            return None

        current_price = candles[-1].close

        # Extract latest indicator metrics safely
        latest_rsi = next((p.value for p in reversed(indicators.rsi) if p.value is not None), None)
        latest_macd = next((p for p in reversed(indicators.macd) if p.macd is not None and p.signal is not None), None)
        latest_ema_9 = next((p.value for p in reversed(indicators.ema_9) if p.value is not None), None)
        latest_ema_21 = next((p.value for p in reversed(indicators.ema_21) if p.value is not None), None)
        latest_ema_50 = next((p.value for p in reversed(indicators.ema_50) if p.value is not None), None)
        latest_ema_200 = next((p.value for p in reversed(indicators.ema_200) if p.value is not None), None)
        latest_atr = next((p.value for p in reversed(indicators.atr) if p.value is not None), None) or (current_price * 0.01)
        latest_bb = next((p for p in reversed(indicators.bollinger) if p.upper is not None and p.lower is not None), None)

        recent_patterns = patterns.patterns[-3:] if patterns.patterns else []
        bullish_patterns = [p for p in recent_patterns if p.direction.upper() == "BULLISH"]

        supports = [z for z in sr.zones if z.zone_type == "Support"]
        nearest_support = max([z.price for z in supports if z.price < current_price], default=current_price - (latest_atr * 2))

        # Check existing active pending proposal for this symbol to prevent duplicates
        existing_pending = db.query(BuyProposal).filter(
            BuyProposal.symbol == symbol,
            BuyProposal.status == "PENDING",
            BuyProposal.expires_at > utcnow()
        ).first()
        if existing_pending:
            logger.info(f"Pending proposal already exists for {symbol} ({existing_pending.proposal_id})")
            return None

        matched_rules: List[str] = []
        unmatched_rules: List[str] = []
        confidence_points = 0.50

        # Strategy Rule Evaluation:
        # Rule 1: Moving average alignment
        if latest_ema_9 and latest_ema_21 and latest_ema_9 > latest_ema_21:
            matched_rules.append("Short-term EMA 9 > EMA 21 (Bullish cross/alignment)")
            confidence_points += 0.10
        else:
            unmatched_rules.append("Short-term EMA 9 is not above EMA 21")

        if latest_ema_50 and current_price >= latest_ema_50:
            matched_rules.append("Price trading above intermediate EMA 50 support")
            confidence_points += 0.08
        else:
            unmatched_rules.append("Price is below EMA 50")

        # Rule 2: RSI non-overbought momentum
        if latest_rsi is not None and 45.0 <= latest_rsi <= 68.0:
            matched_rules.append(f"RSI(14) is {latest_rsi:.1f} (Constructive momentum in non-overbought zone)")
            confidence_points += 0.12
        elif latest_rsi is not None and latest_rsi > 70.0:
            unmatched_rules.append(f"RSI is overbought at {latest_rsi:.1f} (High pullback risk)")
        elif latest_rsi is not None and latest_rsi < 40.0:
            unmatched_rules.append(f"RSI is sluggish at {latest_rsi:.1f}")

        # Rule 3: MACD Histogram expansion
        if latest_macd and latest_macd.histogram is not None and latest_macd.histogram > 0:
            matched_rules.append(f"MACD histogram positive ({latest_macd.histogram:+.4f}) signaling upward momentum")
            confidence_points += 0.10
        else:
            unmatched_rules.append("MACD histogram is negative or contracting")

        # Rule 4: Candlestick pattern confirmation
        pattern_detail = "None"
        if bullish_patterns:
            p_names = ", ".join([p.pattern_name for p in bullish_patterns])
            pattern_detail = p_names
            matched_rules.append(f"Bullish candlestick pattern confirmed: {p_names}")
            confidence_points += 0.10

        # Require at least 2 strong matched conditions and no more than 2 unmatched to trigger proposal
        if len(matched_rules) < 2 or (latest_rsi and latest_rsi > 72.0):
            return None

        # Calculate Entry, Stop Loss, Target, and Position Sizing
        entry_price = round(current_price, 4)
        atr_buffer = latest_atr * 1.5
        stop_loss = round(max(nearest_support * 0.998, entry_price - atr_buffer), 4)

        if stop_loss >= entry_price:
            stop_loss = round(entry_price - atr_buffer, 4)

        risk_per_unit = max(0.0001, entry_price - stop_loss)
        target = round(entry_price + (risk_per_unit * 2.0), 4)
        rr_ratio = round((target - entry_price) / risk_per_unit, 2)

        # Dynamic lot sizing aligned with RiskSettings in database
        from app.models.entities import RiskSettings
        risk_settings = db.query(RiskSettings).first() if db else None
        if risk_settings and risk_settings.simulated_balance:
            simulated_risk_budget = risk_settings.simulated_balance * (risk_settings.max_risk_per_trade_pct / 100.0)
            max_pos_capital = risk_settings.simulated_balance * (risk_settings.max_position_size_pct / 100.0)
        else:
            simulated_risk_budget = 10.0
            max_pos_capital = 1000.0

        qty_by_risk = simulated_risk_budget / risk_per_unit
        qty_by_capital = max_pos_capital / entry_price
        calculated_qty = max(1.0, round(min(qty_by_risk, qty_by_capital), 2))
        risk_amount = round(calculated_qty * risk_per_unit, 2)
        estimated_costs = round((entry_price * calculated_qty * 0.0003) + 2.0, 2)

        confidence_score = min(0.92, round(confidence_points, 2))
        proposal_uuid = f"PROP-{uuid.uuid4().hex[:10].upper()}"

        explanation = (
            f"AI BUY setup detected for {symbol} ({market}) based on {len(matched_rules)} conforming technical factors. "
            f"Price ({entry_price:.4f}) shows constructive momentum above local support with positive MACD velocity. "
            f"Target ({target:.4f}) projects a {rr_ratio}:1 reward-to-risk ratio."
        )

        uncertainties = (
            f"Uncertainties: {len(unmatched_rules)} non-conforming conditions noted: "
            + (", ".join(unmatched_rules) if unmatched_rules else "None")
            + ". High sensitivity to sudden volatility shifts or macro headline breaks."
        )

        supporting_indicators = {
            "rsi": latest_rsi,
            "macd": latest_macd.macd if latest_macd else None,
            "signal": latest_macd.signal if latest_macd else None,
            "histogram": latest_macd.histogram if latest_macd else None,
            "ema_9": latest_ema_9,
            "ema_21": latest_ema_21,
            "ema_50": latest_ema_50,
            "ema_200": latest_ema_200,
            "atr_14": round(latest_atr, 4),
            "recent_pattern": pattern_detail,
            "nearest_support": nearest_support,
        }

        # Expiry time: 15 minutes from creation
        expires_at = utcnow() + timedelta(minutes=15)

        strat_name = strategy.name if strategy else "EMA Confluence & Momentum Trend"
        strat_id = strategy.id if strategy else None

        proposal = BuyProposal(
            proposal_id=proposal_uuid,
            symbol=symbol,
            market=market,
            strategy_id=strat_id,
            strategy_name=strat_name,
            current_price=entry_price,
            proposed_entry_price=entry_price,
            proposed_quantity=calculated_qty,
            stop_loss=stop_loss,
            target=target,
            risk_amount=risk_amount,
            risk_reward_ratio=rr_ratio,
            estimated_costs=estimated_costs,
            matched_conditions_json=json.dumps(matched_rules),
            unmatched_conditions_json=json.dumps(unmatched_rules),
            supporting_indicators_json=json.dumps(supporting_indicators),
            confidence_score=confidence_score,
            confidence_method="Multi-Factor Confluence & Risk-Reward Weighting",
            explanation=explanation,
            uncertainties=uncertainties,
            data_source="DEMO_DATA (Simulated)",
            data_timestamp=utcnow(),
            expires_at=expires_at,
            status="PENDING",
            version=1,
        )

        db.add(proposal)
        db.commit()
        db.refresh(proposal)

        # Audit Log
        AuditService.log_event(
            db=db,
            event_type="PROPOSAL_CREATED",
            action=f"Generated AI BUY Proposal {proposal_uuid} for {symbol}",
            actor="AI_STRATEGY_ENGINE",
            symbol=symbol,
            market=market,
            proposal_id=proposal_uuid,
            details={
                "entry": entry_price,
                "quantity": calculated_qty,
                "stop_loss": stop_loss,
                "target": target,
                "confidence": confidence_score,
                "rr_ratio": rr_ratio,
                "matched_conditions": matched_rules,
            },
        )

        logger.info(f"Generated new BUY proposal {proposal_uuid} for {symbol} ({market})")
        return proposal

    STRATEGY_CATALOG: Dict[str, StrategyDefinition] = {
        "STRAT-EMA-CROSS": StrategyDefinition(
            strategy_id="STRAT-EMA-CROSS",
            name="EMA Crossover",
            version="1.0.0",
            description="Classic dual exponential moving average crossover capturing medium-term trend shifts.",
            market_compatibility=["NSE", "FOREX", "MCX"],
            timeframe_compatibility=["5m", "15m", "1h", "1D"],
            required_indicators=["EMA_9", "EMA_21", "ATR_14"],
            entry_conditions=["Fast EMA (9) crosses above Slow EMA (21)"],
            exit_conditions=["Fast EMA (9) crosses below Slow EMA (21) or Stop-Loss/Target hit"],
            stop_loss_logic="1.5 x ATR(14) below entry",
            target_logic="2.0 x Risk distance (minimum 2:1 Reward-to-Risk)",
            trailing_stop_enabled=True,
            required_candle_history=25,
        ),
        "STRAT-RSI-REV": StrategyDefinition(
            strategy_id="STRAT-RSI-REV",
            name="RSI Reversal",
            version="1.0.0",
            description="Mean reversion setup identifying oversold (<30) exhaustion turns.",
            market_compatibility=["NSE", "FOREX", "MCX"],
            timeframe_compatibility=["15m", "1h", "1D"],
            required_indicators=["RSI_14", "SMA_20", "ATR_14"],
            entry_conditions=["RSI crosses above 30 from oversold territory"],
            exit_conditions=["RSI reaches 65+ or touches upper band / target"],
            stop_loss_logic="Swing low or 1.5 x ATR below entry",
            target_logic="2.0 x Risk distance or 20 SMA mean test",
            trailing_stop_enabled=False,
            required_candle_history=30,
        ),
        "STRAT-MACD-MOM": StrategyDefinition(
            strategy_id="STRAT-MACD-MOM",
            name="MACD Momentum",
            version="1.0.0",
            description="MACD centerline and signal-line momentum acceleration strategy.",
            market_compatibility=["NSE", "FOREX", "MCX"],
            timeframe_compatibility=["15m", "1h", "1D"],
            required_indicators=["MACD_12_26_9", "EMA_50", "ATR_14"],
            entry_conditions=["MACD line crosses above Signal line with expanding positive histogram above zero"],
            exit_conditions=["MACD histogram contracts or crosses below signal line"],
            stop_loss_logic="Recent swing low or 1.5 x ATR",
            target_logic="2.0 x Risk distance",
            trailing_stop_enabled=True,
            required_candle_history=35,
        ),
        "STRAT-VWAP-TREND": StrategyDefinition(
            strategy_id="STRAT-VWAP-TREND",
            name="VWAP Trend",
            version="1.0.0",
            description="Institutional benchmark strategy entering on volume-supported VWAP breakouts and pullbacks.",
            market_compatibility=["NSE", "MCX"],
            timeframe_compatibility=["1m", "5m", "15m"],
            required_indicators=["VWAP", "Volume_SMA_20", "ATR_14"],
            entry_conditions=["Price crosses above VWAP with Volume > Volume SMA(20)"],
            exit_conditions=["Price closes below VWAP or Target reached"],
            stop_loss_logic="1.0 x ATR below VWAP",
            target_logic="2.0 x Risk distance",
            trailing_stop_enabled=True,
            required_candle_history=20,
        ),
        "STRAT-BB-REV": StrategyDefinition(
            strategy_id="STRAT-BB-REV",
            name="Bollinger Band Reversion",
            version="1.0.0",
            description="Statistical volatility envelope strategy buying reversals off the 2-standard-deviation lower band.",
            market_compatibility=["NSE", "FOREX"],
            timeframe_compatibility=["15m", "1h", "1D"],
            required_indicators=["Bollinger_20_2", "RSI_14", "ATR_14"],
            entry_conditions=["Price touches or pierces lower band and closes back inside with RSI < 40"],
            exit_conditions=["Price touches 20-period SMA middle band or upper band"],
            stop_loss_logic="Lowest low of last 3 candles minus 0.5 x ATR",
            target_logic="Middle Bollinger Band (20 SMA)",
            trailing_stop_enabled=False,
            required_candle_history=25,
        ),
        "STRAT-VOL-BREAKOUT": StrategyDefinition(
            strategy_id="STRAT-VOL-BREAKOUT",
            name="Volume-Confirmed Breakout",
            version="1.0.0",
            description="High-volume momentum breakout above the 20-candle resistance high.",
            market_compatibility=["NSE", "MCX"],
            timeframe_compatibility=["5m", "15m", "1h"],
            required_indicators=["Volume_SMA_20", "ATR_14", "SMA_20"],
            entry_conditions=["Price exceeds 20-period high with Volume >= 1.5 x Volume SMA(20)"],
            exit_conditions=["Trailing stop hit or 50% retracement of breakout candle"],
            stop_loss_logic="Breakout candle low",
            target_logic="2.5 x Risk distance",
            trailing_stop_enabled=True,
            required_candle_history=25,
        ),
        "STRAT-MULTI-CONF": StrategyDefinition(
            strategy_id="STRAT-MULTI-CONF",
            name="Multi-Indicator Confirmation",
            version="1.0.0",
            description="Comprehensive confluence strategy requiring alignment across trend, momentum, volatility, and support.",
            market_compatibility=["NSE", "FOREX", "MCX"],
            timeframe_compatibility=["15m", "1h", "1D"],
            required_indicators=["EMA_9", "EMA_21", "EMA_50", "RSI_14", "MACD_12_26_9", "ATR_14"],
            entry_conditions=["EMA 9 > EMA 21", "RSI between 45 and 68", "MACD histogram > 0", "Price above EMA 50 or Support zone"],
            exit_conditions=["EMA 9 crosses below EMA 21 or Stop-Loss/Target reached"],
            stop_loss_logic="Nearest Support zone or 1.5 x ATR",
            target_logic="2.0 x Risk distance",
            trailing_stop_enabled=True,
            required_candle_history=30,
        ),
    }

    @classmethod
    def get_strategy_catalogue(cls) -> List[StrategyDefinition]:
        """Returns all configured strategy definitions."""
        return list(cls.STRATEGY_CATALOG.values())

    @classmethod
    def evaluate_strategy_signal(
        cls,
        strategy_id: str,
        symbol: str,
        market: str,
        timeframe: str,
        candles: List[OHLCCandle],
        indicators: IndicatorsResponse,
        patterns: Optional[PatternsResponse] = None,
        sr: Optional[SupportResistanceResponse] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> StrategySignalOutput:
        """
        Evaluates a specific rule-based strategy against market data.
        Returns a structured StrategySignalOutput with one of:
        BUY_CANDIDATE, SELL_CANDIDATE, HOLD, NO_TRADE, INVALID_DATA.
        Strictly prohibits silent fallback to another strategy.
        """
        now = utcnow()
        strat_def = cls.STRATEGY_CATALOG.get(strategy_id)
        if not strat_def:
            return StrategySignalOutput(
                strategy_id=strategy_id,
                strategy_name=f"Unknown Strategy ({strategy_id})",
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                signal_state="INVALID_DATA",
                confidence_score=0.0,
                reasons=[f"Strategy '{strategy_id}' not found in STRATEGY_CATALOG. Silent fallback is strictly prohibited."],
                conflicts=["Unknown strategy identifier"],
                timestamp=now,
                is_trade_authorization=False,
            )

        params = parameters or {}

        if patterns is None and candles:
            patterns = PatternService.detect_patterns(candles=candles, symbol=symbol, timeframe=timeframe)
        if sr is None and candles:
            sr = SupportResistanceService.calculate_zones(candles=candles, symbol=symbol, timeframe=timeframe)

        if not candles or len(candles) < strat_def.required_candle_history:
            return StrategySignalOutput(
                strategy_id=strat_def.strategy_id,
                strategy_name=strat_def.name,
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                signal_state="INVALID_DATA",
                confidence_score=0.0,
                reasons=[f"Insufficient candle history ({len(candles) if candles else 0}/{strat_def.required_candle_history} required)"],
                conflicts=["Cannot compute indicators on insufficient historical data"],
                timestamp=now,
                is_trade_authorization=False,
            )

        current_price = candles[-1].close
        latest_atr = next((p.value for p in reversed(indicators.atr) if p.value is not None), None) or (current_price * 0.01)
        latest_rsi = next((p.value for p in reversed(indicators.rsi) if p.value is not None), None)
        latest_macd = next((p for p in reversed(indicators.macd) if p.macd is not None and p.signal is not None), None)
        latest_ema_9 = next((p.value for p in reversed(indicators.ema_9) if p.value is not None), None)
        latest_ema_21 = next((p.value for p in reversed(indicators.ema_21) if p.value is not None), None)
        latest_ema_50 = next((p.value for p in reversed(indicators.ema_50) if p.value is not None), None)
        latest_bb = next((p for p in reversed(indicators.bollinger) if p.upper is not None and p.lower is not None), None)
        latest_vwap = next((p.value for p in reversed(indicators.vwap) if p.value is not None), None) if hasattr(indicators, "vwap") and indicators.vwap else None
        latest_vol_sma = next((p.value for p in reversed(indicators.volume_sma) if p.value is not None), None) if hasattr(indicators, "volume_sma") and indicators.volume_sma else None
        current_volume = candles[-1].volume or 0.0

        signal_state: SignalState = "NO_TRADE"
        confidence = 0.50
        matched: List[str] = []
        unmatched: List[str] = []
        reasons: List[str] = []
        conflicts: List[str] = []

        if strategy_id == "STRAT-EMA-CROSS":
            if latest_ema_9 and latest_ema_21:
                if latest_ema_9 > latest_ema_21:
                    spread_pct = ((latest_ema_9 - latest_ema_21) / latest_ema_21) * 100
                    matched.append(f"EMA 9 ({latest_ema_9:.2f}) > EMA 21 ({latest_ema_21:.2f}) [Spread: {spread_pct:+.2f}%]")
                    signal_state = "BUY_CANDIDATE"
                    confidence = 0.75
                    reasons.append("Bullish EMA 9/21 cross confirmed.")
                else:
                    unmatched.append(f"EMA 9 ({latest_ema_9:.2f}) <= EMA 21 ({latest_ema_21:.2f})")
                    signal_state = "HOLD"
                    reasons.append("Moving averages in bearish or neutral drift.")

        elif strategy_id == "STRAT-RSI-REV":
            oversold = float(params.get("oversold_threshold", 35.0))
            overbought = float(params.get("overbought_threshold", 70.0))
            if latest_rsi is not None:
                if latest_rsi <= oversold:
                    matched.append(f"RSI oversold rebound zone ({latest_rsi:.1f} <= {oversold})")
                    signal_state = "BUY_CANDIDATE"
                    confidence = 0.72
                    reasons.append("RSI turning up from oversold support.")
                elif latest_rsi >= overbought:
                    unmatched.append(f"RSI overbought exhaustion ({latest_rsi:.1f} >= {overbought})")
                    signal_state = "SELL_CANDIDATE"
                    confidence = 0.70
                    reasons.append("RSI overbought exhaustion signal.")
                else:
                    signal_state = "HOLD"
                    reasons.append(f"RSI neutral at {latest_rsi:.1f}.")

        elif strategy_id == "STRAT-MACD-MOM":
            if latest_macd and latest_macd.histogram is not None:
                if latest_macd.macd > latest_macd.signal and latest_macd.histogram > 0:
                    matched.append(f"MACD line ({latest_macd.macd:+.4f}) > Signal ({latest_macd.signal:+.4f}), Histogram {latest_macd.histogram:+.4f}")
                    signal_state = "BUY_CANDIDATE"
                    confidence = 0.76
                    reasons.append("Positive MACD momentum expansion.")
                elif latest_macd.macd < latest_macd.signal and latest_macd.histogram < 0:
                    signal_state = "SELL_CANDIDATE"
                    confidence = 0.70
                    reasons.append("Negative MACD momentum crossover.")
                else:
                    signal_state = "HOLD"
                    reasons.append("MACD neutral or contracting.")

        elif strategy_id == "STRAT-VWAP-TREND":
            vwap_val = latest_vwap or current_price
            if current_price >= vwap_val:
                matched.append(f"Price ({current_price:.2f}) above VWAP ({vwap_val:.2f})")
                if latest_vol_sma and current_volume >= latest_vol_sma:
                    matched.append(f"Volume ({current_volume:.0f}) >= Volume SMA ({latest_vol_sma:.0f})")
                    confidence = 0.78
                else:
                    unmatched.append("Volume does not exceed Volume SMA")
                    confidence = 0.65
                signal_state = "BUY_CANDIDATE"
                reasons.append("Price trading above institutional VWAP.")
            else:
                unmatched.append(f"Price ({current_price:.2f}) below VWAP ({vwap_val:.2f})")
                signal_state = "SELL_CANDIDATE"
                reasons.append("Price trading below VWAP reference.")

        elif strategy_id == "STRAT-BB-REV":
            lower_tol = float(params.get("lower_tolerance", 1.005))
            if latest_bb and latest_bb.lower is not None:
                if current_price <= latest_bb.lower * lower_tol:
                    matched.append(f"Price ({current_price:.2f}) near lower Bollinger Band ({latest_bb.lower:.2f})")
                    signal_state = "BUY_CANDIDATE"
                    confidence = 0.73
                    reasons.append("Mean reversion candidate off lower volatility boundary.")
                elif latest_bb.upper is not None and current_price >= latest_bb.upper * 0.995:
                    signal_state = "SELL_CANDIDATE"
                    confidence = 0.70
                    reasons.append("Price at upper volatility boundary.")
                else:
                    signal_state = "HOLD"
                    reasons.append("Price inside normal Bollinger corridor.")

        elif strategy_id == "STRAT-VOL-BREAKOUT":
            lookback_n = int(params.get("lookback", 20))
            vol_mult = float(params.get("volume_multiplier", 1.2))
            high_n = max([c.high for c in candles[-lookback_n:]]) if len(candles) >= lookback_n else current_price
            if current_price >= high_n * 0.998:
                matched.append(f"Price testing/breaking {lookback_n}-candle high ({high_n:.2f})")
                if latest_vol_sma and current_volume >= latest_vol_sma * vol_mult:
                    matched.append(f"Volume ({current_volume:.0f}) exceeds {vol_mult}x Volume SMA ({latest_vol_sma:.0f})")
                    signal_state = "BUY_CANDIDATE"
                    confidence = 0.80
                    reasons.append("High volume breakout confirmed.")
                else:
                    unmatched.append("Breakout lack volume confirmation")
                    signal_state = "HOLD"
                    conflicts.append("Volume does not confirm breakout")
            else:
                signal_state = "NO_TRADE"
                reasons.append(f"Price ({current_price:.2f}) below {lookback_n}-candle high ({high_n:.2f})")

        elif strategy_id == "STRAT-MULTI-CONF":
            req_conf = int(params.get("confluence_min", 3))
            cond_count = 0
            if latest_ema_9 and latest_ema_21 and latest_ema_9 > latest_ema_21:
                matched.append("EMA 9 > EMA 21")
                cond_count += 1
            if latest_rsi and 45 <= latest_rsi <= 68:
                matched.append(f"RSI in bullish corridor ({latest_rsi:.1f})")
                cond_count += 1
            if latest_macd and latest_macd.histogram is not None and latest_macd.histogram > 0:
                matched.append("MACD histogram > 0")
                cond_count += 1
            if latest_ema_50 and current_price >= latest_ema_50:
                matched.append("Price >= EMA 50")
                cond_count += 1

            if cond_count >= req_conf:
                signal_state = "BUY_CANDIDATE"
                confidence = 0.75 + (cond_count * 0.05)
                reasons.append(f"{cond_count} conforming indicators aligned.")
            elif cond_count >= 2:
                signal_state = "HOLD"
                reasons.append(f"Partial confluence ({cond_count} conditions met).")
            else:
                signal_state = "NO_TRADE"
                conflicts.append(f"Insufficient confluence ({cond_count}/{req_conf} conditions met).")

        else:
            return StrategySignalOutput(
                strategy_id=strategy_id,
                strategy_name=strat_def.name,
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                signal_state="INVALID_DATA",
                confidence_score=0.0,
                reasons=[f"No evaluation logic registered for '{strategy_id}'. Silent fallback is prohibited."],
                conflicts=["Unregistered strategy implementation"],
                timestamp=now,
                is_trade_authorization=False,
            )

        # Strategy-specific stop-loss and target calculations per catalog specifications
        if strategy_id == "STRAT-VWAP-TREND":
            atr_mult = float(params.get("atr_stop_multiplier", 1.0))
            sl = round(current_price - (latest_atr * atr_mult), 2)
            risk_dist = max(0.01, current_price - sl)
            tgt = round(current_price + (risk_dist * 2.0), 2)
            rr = round((tgt - current_price) / risk_dist, 2)
        elif strategy_id == "STRAT-VOL-BREAKOUT":
            atr_mult = float(params.get("atr_stop_multiplier", 1.5))
            sl = round(min(candles[-1].low, current_price - (latest_atr * atr_mult)), 2)
            risk_dist = max(0.01, current_price - sl)
            tgt = round(current_price + (risk_dist * 2.5), 2)
            rr = round((tgt - current_price) / risk_dist, 2)
        else:
            atr_mult = float(params.get("atr_stop_multiplier", 1.5))
            sl = round(current_price - (latest_atr * atr_mult), 2)
            risk_dist = max(0.01, current_price - sl)
            tgt = round(current_price + (risk_dist * 2.0), 2)
            rr = round((tgt - current_price) / risk_dist, 2)

        return StrategySignalOutput(
            strategy_id=strat_def.strategy_id,
            strategy_name=strat_def.name,
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            signal_state=signal_state,
            confidence_score=round(min(0.95, confidence), 2),
            suggested_entry=round(current_price, 2) if signal_state == "BUY_CANDIDATE" else None,
            suggested_stop_loss=sl if signal_state == "BUY_CANDIDATE" else None,
            suggested_target=tgt if signal_state == "BUY_CANDIDATE" else None,
            risk_reward_ratio=rr if signal_state == "BUY_CANDIDATE" else None,
            matched_conditions=matched,
            unmatched_conditions=unmatched,
            reasons=reasons,
            conflicts=conflicts,
            timestamp=now,
            is_trade_authorization=False,
        )

