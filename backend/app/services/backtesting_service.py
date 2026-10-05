"""Quantitative Strategy Backtesting Engine for Vibe Trader AI.
Features dynamic strategy dispatch across STRATEGY_CATALOG, strict chronological
candle evaluation to prevent look-ahead bias, realistic slippage, broker transaction fees,
in-sample/out-of-sample data splitting, market regime breakdown, and overtrading analytics.
"""
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status

from app.schemas.workflow import (
    BacktestRequest,
    BacktestTradeResult,
    BacktestSummaryResponse,
)
from app.schemas.analysis import IndicatorsResponse
from app.schemas.market import OHLCCandle
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService
from app.services.strategy_engine import StrategyEngine
from app.services.csv_data_provider import CSVDataProvider

logger = logging.getLogger("vibe-trader-ai.backtesting")

# Alias map for strategy lookup by common names or IDs
STRATEGY_ALIAS_MAP: Dict[str, str] = {
    "STRAT-EMA-CROSS": "STRAT-EMA-CROSS",
    "EMA CROSSOVER": "STRAT-EMA-CROSS",
    "EMA MOMENTUM TREND FOLLOWING": "STRAT-EMA-CROSS",
    "EMA MOMENTUM TREND": "STRAT-EMA-CROSS",
    "STRAT-RSI-REV": "STRAT-RSI-REV",
    "RSI REVERSAL": "STRAT-RSI-REV",
    "RSI SUPPORT CONFLUENCE": "STRAT-RSI-REV",
    "STRAT-MACD-MOM": "STRAT-MACD-MOM",
    "MACD MOMENTUM": "STRAT-MACD-MOM",
    "STRAT-VWAP-TREND": "STRAT-VWAP-TREND",
    "VWAP TREND": "STRAT-VWAP-TREND",
    "STRAT-BB-REV": "STRAT-BB-REV",
    "BOLLINGER BAND REVERSION": "STRAT-BB-REV",
    "BOLLINGER BANDS REVERSION": "STRAT-BB-REV",
    "STRAT-VOL-BREAKOUT": "STRAT-VOL-BREAKOUT",
    "VOLUME-CONFIRMED BREAKOUT": "STRAT-VOL-BREAKOUT",
    "VOLUME BREAKOUT": "STRAT-VOL-BREAKOUT",
    "STRAT-MULTI-CONF": "STRAT-MULTI-CONF",
    "MULTI-INDICATOR CONFIRMATION": "STRAT-MULTI-CONF",
    "MULTI-FACTOR CONFLUENCE": "STRAT-MULTI-CONF",
}


class BacktestingService:
    @staticmethod
    def resolve_strategy_id(strategy_name_or_id: str) -> str:
        """Resolves strategy input to a valid STRATEGY_CATALOG key or raises HTTPException."""
        normalized = strategy_name_or_id.strip().upper()
        if normalized in STRATEGY_ALIAS_MAP:
            return STRATEGY_ALIAS_MAP[normalized]

        # Partial match against catalog keys and names
        for cat_id, cat_def in StrategyEngine.STRATEGY_CATALOG.items():
            if cat_id.upper() == normalized or cat_def.name.upper() == normalized:
                return cat_id

        available = list(StrategyEngine.STRATEGY_CATALOG.keys()) + [
            d.name for d in StrategyEngine.STRATEGY_CATALOG.values()
        ]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported strategy '{strategy_name_or_id}'. "
                f"Compatible catalog strategies: {', '.join(sorted(set(available)))}."
            ),
        )

    @classmethod
    def run_backtest(cls, db, req: BacktestRequest) -> BacktestSummaryResponse:
        # 1. Resolve strategy definition from catalog
        strat_id = cls.resolve_strategy_id(req.strategy_name)
        strat_def = StrategyEngine.STRATEGY_CATALOG[strat_id]
        strat_version = getattr(strat_def, "version", "1.0.0")

        # 2. Ingest candle data from persistent CSV or live/demo MarketDataService
        raw_candles: List[OHLCCandle] = []
        data_source = "MARKET_FEED"
        dataset_identity = req.symbol

        if req.dataset_id:
            custom_candles = CSVDataProvider.get_dataset(symbol_or_id=req.dataset_id, db=db)
            if custom_candles:
                raw_candles = custom_candles
                data_source = "CUSTOM_CSV"
                dataset_identity = req.dataset_id

        if not raw_candles:
            # Check if symbol corresponds to a custom uploaded CSV
            custom_candles = CSVDataProvider.get_dataset(symbol_or_id=req.symbol, db=db)
            if custom_candles:
                raw_candles = custom_candles
                data_source = "CUSTOM_CSV"
                dataset_identity = req.symbol
            else:
                market_service = MarketDataService(db=db)
                ohlc = market_service.get_ohlc(symbol=req.symbol, timeframe=req.timeframe)
                raw_candles = ohlc.candles or []
                data_source = "MARKET_FEED"
                dataset_identity = req.symbol

        # 3. Clean and sort candles chronologically; deduplicate timestamps and reject invalid OHLC
        clean_candles: List[OHLCCandle] = []
        seen_timestamps = set()
        for c in raw_candles:
            if c.time not in seen_timestamps:
                # Sanity: high must be >= low and open/close must be >= 0
                if c.high >= c.low and c.open >= 0 and c.close >= 0:
                    seen_timestamps.add(c.time)
                    clean_candles.append(c)

        clean_candles.sort(key=lambda x: x.time)

        # 4. In-Sample vs Validation vs Out-of-Sample Slicing
        split_mode = (req.data_split or "FULL").upper().strip()
        in_ratio = req.in_sample_ratio if req.in_sample_ratio is not None else 0.70
        val_ratio = req.validation_ratio if req.validation_ratio is not None else 0.15

        in_ratio = max(0.1, min(0.9, in_ratio))
        val_ratio = max(0.0, min(0.5, val_ratio))

        n_total = len(clean_candles)
        idx_in = int(n_total * in_ratio)
        idx_val = int(n_total * (in_ratio + val_ratio))

        if split_mode == "IN_SAMPLE":
            active_candles = clean_candles[:idx_in]
        elif split_mode == "VALIDATION":
            active_candles = clean_candles[idx_in:idx_val]
        elif split_mode == "OUT_OF_SAMPLE":
            active_candles = clean_candles[idx_val:]
        else:
            split_mode = "FULL"
            active_candles = clean_candles[:]

        min_history = max(strat_def.required_candle_history, 25)

        start_time = active_candles[0].time if active_candles else None
        end_time = active_candles[-1].time if active_candles else None
        date_range_meta = {
            "start_time": start_time,
            "end_time": end_time,
            "candle_count": len(active_candles),
            "total_dataset_candles": n_total,
        }

        execution_assumptions = {
            "initial_capital": req.initial_capital,
            "risk_per_trade_pct": req.risk_per_trade_pct,
            "slippage_pct": req.slippage_pct,
            "commission_per_trade": req.commission_per_trade,
            "single_position_enforced": True,
            "look_ahead_protection": "STRICT_CHRONOLOGICAL",
        }

        # 5. Handle insufficient data gracefully
        if not active_candles or len(active_candles) < min_history:
            return BacktestSummaryResponse(
                strategy_name=strat_def.name,
                symbol=req.symbol,
                timeframe=req.timeframe,
                market=req.market,
                initial_capital=req.initial_capital,
                final_capital=req.initial_capital,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                expectancy=0.0,
                max_drawdown_pct=0.0,
                net_pnl=0.0,
                net_roi_pct=0.0,
                trades=[],
                disclaimer=(
                    f"BACKTEST INSUFFICIENT DATA: Requires at least {min_history} candles. "
                    f"Data split '{split_mode}' provided {len(active_candles)} candles."
                ),
                strategy_id=strat_id,
                strategy_version=strat_version,
                data_split=split_mode,
                dataset_identity=dataset_identity,
                date_range=date_range_meta,
                parameters=req.parameters or {},
                execution_assumptions=execution_assumptions,
                gross_pnl=0.0,
                total_commission=0.0,
                total_slippage=0.0,
                average_holding_time_seconds=0.0,
                sharpe_ratio=None,
                regime_breakdown={
                    "status": "INSUFFICIENT_DATA",
                    "details": f"Fewer than {min_history} candles available in split '{split_mode}'."
                },
                overtrading_metrics={
                    "total_signals_generated": 0,
                    "signals_executed": 0,
                    "signals_filtered_duplicate": 0,
                    "max_consecutive_wins": 0,
                    "max_consecutive_losses": 0,
                    "avg_trades_per_day": 0.0,
                },
                data_source=data_source,
                timestamp=datetime.utcnow().isoformat(),
            )

        # 6. Precompute causal indicators across active candles (Wilder/EWM/rolling ending at t)
        full_indicators = IndicatorsService.compute_all_indicators(
            candles=active_candles, symbol=req.symbol, timeframe=req.timeframe
        )

        capital = float(req.initial_capital)
        peak_capital = capital
        max_drawdown = 0.0
        trades: List[BacktestTradeResult] = []

        in_trade = False
        entry_price_raw = 0.0
        entry_price = 0.0
        entry_time = 0
        entry_slippage_cost = 0.0
        quantity = 0.0
        stop_loss = 0.0
        target = 0.0
        trade_id = 1

        total_signals_generated = 0
        signals_filtered_duplicate = 0
        total_gross_pnl = 0.0
        total_commission_accum = 0.0
        total_slippage_accum = 0.0

        # Market regime tracking counters
        regime_counts = {"BULLISH_TREND": 0, "BEARISH_TREND": 0, "SIDEWAYS_RANGE": 0, "HIGH_VOLATILITY": 0}
        regime_trades = {"BULLISH_TREND": 0, "BEARISH_TREND": 0, "SIDEWAYS_RANGE": 0, "HIGH_VOLATILITY": 0}
        regime_pnl = {"BULLISH_TREND": 0.0, "BEARISH_TREND": 0.0, "SIDEWAYS_RANGE": 0.0, "HIGH_VOLATILITY": 0.0}

        # Calculate average ATR for volatility regime classification
        valid_atrs = [p.value for p in full_indicators.atr if p.value is not None]
        mean_atr = (sum(valid_atrs) / len(valid_atrs)) if valid_atrs else 1.0

        # 7. Strict Chronological Forward Simulation Loop
        for i in range(min_history, len(active_candles)):
            curr = active_candles[i]
            # Strict look-ahead prevention: slice historical observations strictly up to candle i
            sub_candles = active_candles[: i + 1]

            # Slice causal indicators strictly up to index i
            sub_indicators = IndicatorsResponse(
                symbol=req.symbol,
                timeframe=req.timeframe,
                is_mock=True,
                rsi=full_indicators.rsi[: i + 1],
                macd=full_indicators.macd[: i + 1],
                ema_9=full_indicators.ema_9[: i + 1],
                ema_21=full_indicators.ema_21[: i + 1],
                ema_50=full_indicators.ema_50[: i + 1],
                ema_200=full_indicators.ema_200[: i + 1],
                sma_20=full_indicators.sma_20[: i + 1],
                sma_50=full_indicators.sma_50[: i + 1],
                sma_200=full_indicators.sma_200[: i + 1],
                atr=full_indicators.atr[: i + 1],
                bollinger=full_indicators.bollinger[: i + 1],
                vwap=full_indicators.vwap[: i + 1] if full_indicators.vwap else [],
                volume_sma=full_indicators.volume_sma[: i + 1] if full_indicators.volume_sma else [],
            )

            # Patterns and support/resistance evaluated strictly on available historical data up to i
            sub_patterns = PatternService.detect_patterns(
                candles=sub_candles, symbol=req.symbol, timeframe=req.timeframe
            )
            sub_sr = SupportResistanceService.calculate_zones(
                candles=sub_candles, symbol=req.symbol, timeframe=req.timeframe
            )

            # Classify regime at step i
            curr_ema9 = sub_indicators.ema_9[-1].value if sub_indicators.ema_9 and sub_indicators.ema_9[-1].value else None
            curr_ema21 = sub_indicators.ema_21[-1].value if sub_indicators.ema_21 and sub_indicators.ema_21[-1].value else None
            curr_ema50 = sub_indicators.ema_50[-1].value if sub_indicators.ema_50 and sub_indicators.ema_50[-1].value else None
            curr_atr = sub_indicators.atr[-1].value if sub_indicators.atr and sub_indicators.atr[-1].value else (curr.close * 0.01)

            current_regime = "SIDEWAYS_RANGE"
            if curr_ema9 and curr_ema21 and curr_ema50:
                if curr.close > curr_ema50 and curr_ema9 > curr_ema21:
                    current_regime = "BULLISH_TREND"
                elif curr.close < curr_ema50 and curr_ema9 < curr_ema21:
                    current_regime = "BEARISH_TREND"

            regime_counts[current_regime] = regime_counts.get(current_regime, 0) + 1
            if curr_atr > (mean_atr * 1.25):
                regime_counts["HIGH_VOLATILITY"] = regime_counts.get("HIGH_VOLATILITY", 0) + 1

            # Dynamically dispatch to StrategyEngine using strategy-specific rules & parameter overrides
            signal = StrategyEngine.evaluate_strategy_signal(
                strategy_id=strat_id,
                symbol=req.symbol,
                market=req.market,
                timeframe=req.timeframe,
                candles=sub_candles,
                indicators=sub_indicators,
                patterns=sub_patterns,
                sr=sub_sr,
                parameters=req.parameters,
            )

            # Check for BUY candidate signal
            if signal.signal_state == "BUY_CANDIDATE":
                total_signals_generated += 1

                if in_trade:
                    # Single-position constraint: ignore duplicate signals while already in a position
                    signals_filtered_duplicate += 1
                else:
                    # Enter trade with realistic slippage modeling
                    slippage_per_unit = curr.close * (req.slippage_pct / 100.0)
                    entry_price_raw = curr.close
                    entry_price = round(curr.close + slippage_per_unit, 4)
                    entry_time = curr.time

                    # Stop-loss and target from strategy or ATR buffer
                    proposed_sl = signal.suggested_stop_loss or (entry_price - (curr_atr * 1.5))
                    stop_loss = round(min(proposed_sl, entry_price - (curr_atr * 0.5)), 4)
                    risk_per_share = max(0.001, entry_price - stop_loss)

                    proposed_tgt = signal.suggested_target or (entry_price + (risk_per_share * 2.0))
                    target = round(max(proposed_tgt, entry_price + (risk_per_share * 1.5)), 4)

                    risk_budget = capital * (req.risk_per_trade_pct / 100.0)
                    calc_qty = max(1.0, round(risk_budget / risk_per_share, 2))
                    max_affordable = max(1.0, round(capital / max(0.01, entry_price), 2))
                    quantity = min(calc_qty, max_affordable)

                    entry_slippage_cost = slippage_per_unit * quantity
                    in_trade = True
                    continue

            if in_trade:
                # Check exit conditions on current candle
                exit_price_raw = 0.0
                exit_reason = ""

                if curr.high >= target:
                    exit_price_raw = target
                    exit_reason = "TARGET_HIT"
                elif curr.low <= stop_loss:
                    exit_price_raw = stop_loss
                    exit_reason = "STOP_LOSS_HIT"
                elif signal.signal_state == "SELL_CANDIDATE":
                    exit_price_raw = curr.close
                    exit_reason = "STRATEGY_EXIT"
                elif i == len(active_candles) - 1:
                    exit_price_raw = curr.close
                    exit_reason = "END_OF_SERIES"

                if exit_price_raw > 0:
                    exit_slippage_per_unit = exit_price_raw * (req.slippage_pct / 100.0)
                    exit_price = round(exit_price_raw - exit_slippage_per_unit, 4)
                    exit_slippage_cost = exit_slippage_per_unit * quantity

                    trade_slippage = round(entry_slippage_cost + exit_slippage_cost, 2)
                    commission = round(req.commission_per_trade * 2.0, 2)  # Entry + exit fees

                    gross_pnl = round((exit_price_raw - entry_price_raw) * quantity, 2)
                    net_pnl = round(gross_pnl - trade_slippage - commission, 2)

                    capital = round(capital + net_pnl, 2)
                    cost_basis = entry_price * quantity
                    roi_pct = round((net_pnl / max(0.01, cost_basis)) * 100, 2)

                    total_gross_pnl += gross_pnl
                    total_commission_accum += commission
                    total_slippage_accum += trade_slippage

                    # Track peak capital and maximum drawdown
                    if capital > peak_capital:
                        peak_capital = capital
                    dd = ((peak_capital - capital) / peak_capital) * 100.0
                    if dd > max_drawdown:
                        max_drawdown = dd

                    # Regime attribution
                    regime_trades[current_regime] = regime_trades.get(current_regime, 0) + 1
                    regime_pnl[current_regime] = round(regime_pnl.get(current_regime, 0.0) + net_pnl, 2)

                    trades.append(
                        BacktestTradeResult(
                            trade_id=trade_id,
                            symbol=req.symbol,
                            entry_time=entry_time,
                            exit_time=curr.time,
                            entry_price=round(entry_price, 4),
                            exit_price=round(exit_price, 4),
                            quantity=quantity,
                            gross_pnl=gross_pnl,
                            net_pnl=net_pnl,
                            roi_pct=roi_pct,
                            exit_reason=exit_reason,
                        )
                    )
                    trade_id += 1
                    in_trade = False

        # 8. Compute Safe Statistical & Risk Metrics (No NaN/Inf)
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.net_pnl > 0]
        losing_trades = [t for t in trades if t.net_pnl <= 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = round((win_count / total_trades) * 100, 2) if total_trades > 0 else 0.0

        total_wins = sum(t.net_pnl for t in winning_trades)
        total_losses = abs(sum(t.net_pnl for t in losing_trades))

        avg_win = round(total_wins / win_count, 2) if win_count > 0 else 0.0
        avg_loss = round(total_losses / loss_count, 2) if loss_count > 0 else 0.0

        # Safe profit factor: avoid infinite or 99.0 magic values
        if total_losses > 0:
            profit_factor = round(total_wins / total_losses, 2)
        elif total_wins > 0:
            profit_factor = round(min(100.0, total_wins), 2)
        else:
            profit_factor = 0.0

        expectancy = round(
            ((win_rate / 100.0) * avg_win) - ((1.0 - (win_rate / 100.0)) * avg_loss), 2
        ) if total_trades > 0 else 0.0

        total_net_pnl = round(capital - req.initial_capital, 2)
        net_roi = round((total_net_pnl / req.initial_capital) * 100, 2)

        # Average holding time calculation
        if total_trades > 0:
            avg_holding_sec = round(sum(t.exit_time - t.entry_time for t in trades) / total_trades, 2)
        else:
            avg_holding_sec = 0.0

        # Sharpe ratio: requires at least 3 trades for minimum sample significance
        sharpe_ratio: Optional[float] = None
        if total_trades >= 3:
            returns = [t.roi_pct / 100.0 for t in trades]
            mean_ret = sum(returns) / len(returns)
            var_ret = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
            std_ret = math.sqrt(var_ret)
            if std_ret > 0:
                sharpe_ratio = round((mean_ret / std_ret) * math.sqrt(252), 4)
            else:
                sharpe_ratio = 0.0

        # Overtrading and streak analytics
        consec_wins = 0
        max_consec_wins = 0
        consec_losses = 0
        max_consec_losses = 0

        for t in trades:
            if t.net_pnl > 0:
                consec_wins += 1
                consec_losses = 0
                max_consec_wins = max(max_consec_wins, consec_wins)
            else:
                consec_losses += 1
                consec_wins = 0
                max_consec_losses = max(max_consec_losses, consec_losses)

        total_seconds = (active_candles[-1].time - active_candles[0].time) if len(active_candles) > 1 else 86400
        days_span = max(1.0, total_seconds / 86400.0)
        avg_trades_per_day = round(total_trades / days_span, 3)

        overtrading_metrics = {
            "total_signals_generated": total_signals_generated,
            "signals_executed": total_trades,
            "signals_filtered_duplicate": signals_filtered_duplicate,
            "max_consecutive_wins": max_consec_wins,
            "max_consecutive_losses": max_consec_losses,
            "avg_trades_per_day": avg_trades_per_day,
        }

        # Market regime evaluation breakdown
        regime_breakdown = {}
        for r_name, count in regime_counts.items():
            if count < 10:
                regime_breakdown[r_name] = {
                    "status": "INSUFFICIENT_DATA",
                    "candle_count": count,
                    "trades": regime_trades.get(r_name, 0),
                    "net_pnl": regime_pnl.get(r_name, 0.0),
                }
            else:
                regime_breakdown[r_name] = {
                    "status": "EVALUATED",
                    "candle_count": count,
                    "trades": regime_trades.get(r_name, 0),
                    "net_pnl": regime_pnl.get(r_name, 0.0),
                }

        return BacktestSummaryResponse(
            strategy_name=strat_def.name,
            symbol=req.symbol,
            timeframe=req.timeframe,
            market=req.market,
            initial_capital=round(req.initial_capital, 2),
            final_capital=round(capital, 2),
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate=win_rate,
            average_win=avg_win,
            average_loss=avg_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            max_drawdown_pct=round(max_drawdown, 2),
            net_pnl=total_net_pnl,
            net_roi_pct=net_roi,
            trades=trades,
            disclaimer=(
                f"BACKTEST SIMULATION: Evaluated {strat_def.name} ({strat_def.strategy_id} v{strat_version}) across "
                f"{len(active_candles)} chronological candles ({split_mode} split) without look-ahead bias. "
                "Simulated results do NOT guarantee live trading success."
            ),
            strategy_id=strat_id,
            strategy_version=strat_version,
            data_split=split_mode,
            dataset_identity=dataset_identity,
            date_range=date_range_meta,
            parameters=req.parameters or {},
            execution_assumptions=execution_assumptions,
            gross_pnl=round(total_gross_pnl, 2),
            total_commission=round(total_commission_accum, 2),
            total_slippage=round(total_slippage_accum, 2),
            average_holding_time_seconds=avg_holding_sec,
            sharpe_ratio=sharpe_ratio,
            regime_breakdown=regime_breakdown,
            overtrading_metrics=overtrading_metrics,
            data_source=data_source,
            timestamp=datetime.utcnow().isoformat(),
        )
