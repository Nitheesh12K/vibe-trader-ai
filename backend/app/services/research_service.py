"""Quantitative Research Engine for Vibe Trader AI.
Provides Walk-Forward Multi-Fold Validation, Out-of-Sample Evaluation,
Benchmark Alpha Attribution (vs Buy-and-Hold and No-Trade),
Market Regime Classification, and Execution Sensitivity Stress Testing.
All calculations are causal, preventing lookahead bias.
"""
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.research import (
    WalkForwardRequest,
    WalkForwardResponse,
    WalkForwardFoldResult,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
    SensitivityScenario,
    RegimeAnalysisResponse,
    MarketRegimeBreakdown,
)
from app.schemas.workflow import BacktestRequest, BacktestSummaryResponse
from app.schemas.market import OHLCCandle
from app.services.backtesting_service import BacktestingService
from app.services.csv_data_provider import CSVDataProvider
from app.services.market_data_service import MarketDataService
from app.services.strategy_engine import StrategyEngine
from app.services.indicators_service import IndicatorsService

logger = logging.getLogger("vibe-trader-ai.research")


class QuantResearchService:
    @staticmethod
    def _fetch_clean_candles(db: Session, symbol: str, timeframe: str) -> List[OHLCCandle]:
        """Loads and sorts candles chronologically, filtering duplicates and invalid OHLC."""
        candles = CSVDataProvider.get_dataset(symbol_or_id=symbol, db=db)
        if not candles:
            market_service = MarketDataService(db=db)
            ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
            candles = ohlc.candles or []

        clean: List[OHLCCandle] = []
        seen = set()
        for c in candles:
            if c.time not in seen and c.high >= c.low and c.open >= 0 and c.close >= 0:
                seen.add(c.time)
                clean.append(c)

        clean.sort(key=lambda x: x.time)
        return clean

    @classmethod
    def run_walk_forward(cls, db: Session, req: WalkForwardRequest) -> WalkForwardResponse:
        """Executes chronological walk-forward validation across rolling folds without temporal overlap."""
        strat_id = BacktestingService.resolve_strategy_id(req.strategy_id)
        strat_def = StrategyEngine.STRATEGY_CATALOG[strat_id]

        all_candles = cls._fetch_clean_candles(db=db, symbol=req.symbol, timeframe=req.timeframe)
        total_candles = len(all_candles)
        min_required = max(strat_def.required_candle_history, 25)

        if total_candles < (min_required * 2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient candles ({total_candles}) for walk-forward validation. Minimum required: {min_required * 2}.",
            )

        num_folds = req.num_folds
        fold_size = total_candles // num_folds
        if fold_size < min_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested {num_folds} folds requires at least {num_folds * min_required} candles, but only {total_candles} are available. Reduce num_folds or supply a longer dataset.",
            )

        folds: List[WalkForwardFoldResult] = []
        all_oos_trades = []
        total_oos_net_pnl = 0.0

        for f_idx in range(num_folds):
            start_idx = f_idx * fold_size
            end_idx = total_candles if f_idx == num_folds - 1 else (f_idx + 1) * fold_size
            fold_candles = all_candles[start_idx:end_idx]

            split_point = int(len(fold_candles) * req.train_ratio)
            train_candles = fold_candles[:split_point]
            test_candles = fold_candles[split_point:]

            if len(train_candles) < 20 or len(test_candles) < 5:
                continue

            # Run In-Sample Backtest
            is_req = BacktestRequest(
                strategy_name=strat_id,
                symbol=req.symbol,
                market=req.market,
                timeframe=req.timeframe,
                initial_capital=req.initial_capital,
                slippage_pct=req.slippage_pct,
                commission_per_trade=req.commission_per_trade,
                data_split="IN_SAMPLE",
                in_sample_ratio=req.train_ratio,
            )
            # Custom simulation for sliced train candles
            is_summary = cls._simulate_candle_slice(
                strat_id=strat_id,
                strat_def=strat_def,
                candles=train_candles,
                symbol=req.symbol,
                market=req.market,
                timeframe=req.timeframe,
                capital=req.initial_capital,
                slippage_pct=req.slippage_pct,
                commission=req.commission_per_trade,
            )

            # Run Out-of-Sample Backtest (Unseen data)
            oos_summary = cls._simulate_candle_slice(
                strat_id=strat_id,
                strat_def=strat_def,
                candles=test_candles,
                symbol=req.symbol,
                market=req.market,
                timeframe=req.timeframe,
                capital=req.initial_capital,
                slippage_pct=req.slippage_pct,
                commission=req.commission_per_trade,
            )

            # Calculate Sortino for OOS
            oos_sortino = cls._calculate_sortino(oos_summary.trades)

            folds.append(
                WalkForwardFoldResult(
                    fold_index=f_idx + 1,
                    train_start=train_candles[0].time,
                    train_end=train_candles[-1].time,
                    train_candles=len(train_candles),
                    test_start=test_candles[0].time,
                    test_end=test_candles[-1].time,
                    test_candles=len(test_candles),
                    in_sample_trades=is_summary.total_trades,
                    in_sample_win_rate=is_summary.win_rate,
                    in_sample_net_pnl=is_summary.net_pnl,
                    in_sample_sharpe=is_summary.sharpe_ratio,
                    in_sample_max_dd=is_summary.max_drawdown_pct,
                    out_of_sample_trades=oos_summary.total_trades,
                    out_of_sample_win_rate=oos_summary.win_rate,
                    out_of_sample_net_pnl=oos_summary.net_pnl,
                    out_of_sample_sharpe=oos_summary.sharpe_ratio,
                    out_of_sample_sortino=oos_sortino,
                    out_of_sample_max_dd=oos_summary.max_drawdown_pct,
                    out_of_sample_profit_factor=oos_summary.profit_factor,
                )
            )
            all_oos_trades.extend(oos_summary.trades)
            total_oos_net_pnl += oos_summary.net_pnl

        # Aggregate Out-of-Sample metrics
        agg_trades = len(all_oos_trades)
        agg_wins = len([t for t in all_oos_trades if t.net_pnl > 0])
        agg_win_rate = round((agg_wins / agg_trades) * 100, 2) if agg_trades > 0 else 0.0
        agg_roi = round((total_oos_net_pnl / req.initial_capital) * 100, 2)
        agg_max_dd = max([f.out_of_sample_max_dd for f in folds], default=0.0)
        agg_sharpe = cls._calculate_sharpe(all_oos_trades)
        agg_sortino = cls._calculate_sortino(all_oos_trades)

        # Baseline: Buy & Hold return across total OOS candles
        first_close = all_candles[0].close
        last_close = all_candles[-1].close
        bh_roi = round(((last_close - first_close) / max(0.01, first_close)) * 100, 2)
        bh_pnl = round(req.initial_capital * (bh_roi / 100.0), 2)
        alpha = round(total_oos_net_pnl - bh_pnl, 2)

        return WalkForwardResponse(
            strategy_id=strat_id,
            strategy_name=strat_def.name,
            symbol=req.symbol,
            timeframe=req.timeframe,
            num_folds=len(folds),
            folds=folds,
            aggregate_oos_trades=agg_trades,
            aggregate_oos_win_rate=agg_win_rate,
            aggregate_oos_net_pnl=round(total_oos_net_pnl, 2),
            aggregate_oos_roi_pct=agg_roi,
            aggregate_oos_max_dd=agg_max_dd,
            aggregate_oos_sharpe=agg_sharpe,
            aggregate_oos_sortino=agg_sortino,
            baseline_buy_and_hold_pnl=bh_pnl,
            baseline_buy_and_hold_roi_pct=bh_roi,
            baseline_no_trade_pnl=0.0,
            alpha_over_buy_and_hold=alpha,
            disclaimer=(
                "QUANTITATIVE RESEARCH ONLY. Evaluates non-overlapping chronological walk-forward folds. "
                "Simulated out-of-sample past metrics do not assure future real-market alpha."
            ),
            timestamp=datetime.utcnow().isoformat(),
        )

    @classmethod
    def run_sensitivity_analysis(cls, db: Session, req: SensitivityAnalysisRequest) -> SensitivityAnalysisResponse:
        """Evaluates strategy robustness under 4 graduated execution friction scenarios."""
        strat_id = BacktestingService.resolve_strategy_id(req.strategy_id)
        strat_def = StrategyEngine.STRATEGY_CATALOG[strat_id]
        candles = cls._fetch_clean_candles(db=db, symbol=req.symbol, timeframe=req.timeframe)

        scenarios_defs = [
            ("Optimal Low Friction", 0.01, 10.0),
            ("Baseline Indian Equities", 0.02, 20.0),
            ("Elevated Friction / Spread", 0.08, 40.0),
            ("Stress Liquidity Freeze", 0.20, 100.0),
        ]

        scenarios: List[SensitivityScenario] = []
        for name, slip, comm in scenarios_defs:
            summary = cls._simulate_candle_slice(
                strat_id=strat_id,
                strat_def=strat_def,
                candles=candles,
                symbol=req.symbol,
                market=req.market,
                timeframe=req.timeframe,
                capital=req.initial_capital,
                slippage_pct=slip,
                commission=comm,
            )
            scenarios.append(
                SensitivityScenario(
                    scenario_name=name,
                    slippage_pct=slip,
                    commission_per_trade=comm,
                    net_pnl=summary.net_pnl,
                    net_roi_pct=summary.net_roi_pct,
                    win_rate=summary.win_rate,
                    total_trades=summary.total_trades,
                    profit_factor=summary.profit_factor,
                    max_drawdown_pct=summary.max_drawdown_pct,
                    sharpe_ratio=summary.sharpe_ratio,
                )
            )

        # Robustness verdict
        baseline_pnl = scenarios[1].net_pnl
        stress_pnl = scenarios[3].net_pnl
        if stress_pnl > 0:
            verdict = "HIGHLY_ROBUST: Strategy maintains positive net return even under extreme liquidity stress."
        elif baseline_pnl > 0 and stress_pnl <= 0:
            verdict = "MODERATELY_SENSITIVE: Profitable under standard costs, but turns negative under high execution friction."
        else:
            verdict = "FRAGILE_OR_UNPROFITABLE: Strategy displays weak edge under current market parameters."

        return SensitivityAnalysisResponse(
            strategy_id=strat_id,
            strategy_name=strat_def.name,
            symbol=req.symbol,
            timeframe=req.timeframe,
            scenarios=scenarios,
            robustness_verdict=verdict,
            disclaimer="Sensitivity stress test results are hypothetical and serve to evaluate slippage tolerance.",
            timestamp=datetime.utcnow().isoformat(),
        )

    @classmethod
    def run_regime_analysis(cls, db: Session, symbol: str, timeframe: str = "1D") -> RegimeAnalysisResponse:
        """Classifies historical candles into 4 market regimes and evaluates distribution."""
        candles = cls._fetch_clean_candles(db=db, symbol=symbol, timeframe=timeframe)
        if len(candles) < 25:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Need at least 25 candles to classify market regimes. Found {len(candles)}.",
            )

        indicators = IndicatorsService.compute_all_indicators(candles=candles, symbol=symbol, timeframe=timeframe)
        valid_atrs = [p.value for p in indicators.atr if p.value is not None]
        mean_atr = (sum(valid_atrs) / len(valid_atrs)) if valid_atrs else 1.0

        counts = {"BULLISH_TREND": 0, "BEARISH_TREND": 0, "HIGH_VOLATILITY": 0, "SIDEWAYS_RANGE": 0}
        total = len(candles)

        for i in range(len(candles)):
            c = candles[i]
            ema50_pt = indicators.ema_50[i].value if i < len(indicators.ema_50) else None
            ema9_pt = indicators.ema_9[i].value if i < len(indicators.ema_9) else None
            ema21_pt = indicators.ema_21[i].value if i < len(indicators.ema_21) else None
            atr_pt = indicators.atr[i].value if i < len(indicators.atr) else None

            if atr_pt and atr_pt > (mean_atr * 1.30):
                counts["HIGH_VOLATILITY"] += 1
            elif ema50_pt and ema9_pt and ema21_pt:
                if c.close > ema50_pt and ema9_pt > ema21_pt:
                    counts["BULLISH_TREND"] += 1
                elif c.close < ema50_pt and ema9_pt < ema21_pt:
                    counts["BEARISH_TREND"] += 1
                else:
                    counts["SIDEWAYS_RANGE"] += 1
            else:
                counts["SIDEWAYS_RANGE"] += 1

        regimes: List[MarketRegimeBreakdown] = []
        descriptions = {
            "BULLISH_TREND": "Price above 50-EMA with 9-EMA above 21-EMA (favorable for momentum/breakout).",
            "BEARISH_TREND": "Price below 50-EMA with 9-EMA below 21-EMA (downtrend velocity).",
            "HIGH_VOLATILITY": "ATR expands > 30% above historical average (wider spreads, increased risk).",
            "SIDEWAYS_RANGE": "EMAs intertwined around median price; mean-reversion favored.",
        }

        for r_name, count in counts.items():
            pct = round((count / total) * 100, 2)
            regimes.append(
                MarketRegimeBreakdown(
                    regime_name=r_name,
                    candle_count=count,
                    percentage_of_time=pct,
                    trades_executed=0,
                    net_pnl=0.0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    description=descriptions.get(r_name, ""),
                )
            )

        return RegimeAnalysisResponse(
            symbol=symbol,
            timeframe=timeframe,
            total_candles=total,
            regimes=regimes,
            methodology="Triple-EMA Trend Filter (9/21/50) + ATR Volatility Threshold.",
            disclaimer="Market regimes are dynamic and classified ex-post. Classification provides structural context.",
            timestamp=datetime.utcnow().isoformat(),
        )

    @classmethod
    def _simulate_candle_slice(
        cls,
        strat_id: str,
        strat_def: Any,
        candles: List[OHLCCandle],
        symbol: str,
        market: str,
        timeframe: str,
        capital: float,
        slippage_pct: float,
        commission: float,
    ) -> BacktestSummaryResponse:
        """Internal helper to simulate a specific candle slice causally."""
        req = BacktestRequest(
            strategy_name=strat_id,
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            initial_capital=capital,
            slippage_pct=slippage_pct,
            commission_per_trade=commission,
            data_split="FULL",
        )
        # Sliced execution using BacktestingService logic directly on given candles
        # Mock a temporary dataset or run via internal loop
        from app.services.pattern_service import PatternService
        from app.services.support_resistance_service import SupportResistanceService
        from app.schemas.workflow import BacktestTradeResult
        from app.schemas.analysis import IndicatorsResponse

        min_history = max(strat_def.required_candle_history, 15)
        if len(candles) < min_history:
            return BacktestSummaryResponse(
                strategy_name=strat_def.name,
                symbol=symbol,
                timeframe=timeframe,
                market=market,
                initial_capital=capital,
                final_capital=capital,
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
                disclaimer="INSUFFICIENT_DATA",
                strategy_id=strat_id,
                strategy_version="1.0.0",
                data_split="SLICE",
                dataset_identity=symbol,
                timestamp=datetime.utcnow().isoformat(),
            )

        full_indicators = IndicatorsService.compute_all_indicators(
            candles=candles, symbol=symbol, timeframe=timeframe
        )

        curr_capital = float(capital)
        peak_capital = curr_capital
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

        for i in range(min_history, len(candles)):
            curr = candles[i]
            sub_candles = candles[: i + 1]

            sub_indicators = IndicatorsResponse(
                symbol=symbol,
                timeframe=timeframe,
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

            sub_patterns = PatternService.detect_patterns(candles=sub_candles, symbol=symbol, timeframe=timeframe)
            sub_sr = SupportResistanceService.calculate_zones(candles=sub_candles, symbol=symbol, timeframe=timeframe)

            signal = StrategyEngine.evaluate_strategy_signal(
                strategy_id=strat_id,
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                candles=sub_candles,
                indicators=sub_indicators,
                patterns=sub_patterns,
                sr=sub_sr,
                parameters=None,
            )

            curr_atr = sub_indicators.atr[-1].value if sub_indicators.atr and sub_indicators.atr[-1].value else (curr.close * 0.01)

            if signal.signal_state == "BUY_CANDIDATE" and not in_trade:
                slippage_unit = curr.close * (slippage_pct / 100.0)
                entry_price_raw = curr.close
                entry_price = round(curr.close + slippage_unit, 4)
                entry_time = curr.time

                proposed_sl = signal.suggested_stop_loss or (entry_price - (curr_atr * 1.5))
                stop_loss = round(min(proposed_sl, entry_price - (curr_atr * 0.5)), 4)
                risk_per_share = max(0.001, entry_price - stop_loss)

                proposed_tgt = signal.suggested_target or (entry_price + (risk_per_share * 2.0))
                target = round(max(proposed_tgt, entry_price + (risk_per_share * 1.5)), 4)

                risk_budget = curr_capital * 0.01  # 1% risk per trade default
                calc_qty = max(1.0, round(risk_budget / risk_per_share, 2))
                max_affordable = max(1.0, round(curr_capital / max(0.01, entry_price), 2))
                quantity = min(calc_qty, max_affordable)

                entry_slippage_cost = slippage_unit * quantity
                in_trade = True
                continue

            if in_trade:
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
                elif i == len(candles) - 1:
                    exit_price_raw = curr.close
                    exit_reason = "END_OF_SERIES"

                if exit_price_raw > 0:
                    exit_slippage_unit = exit_price_raw * (slippage_pct / 100.0)
                    exit_price = round(exit_price_raw - exit_slippage_unit, 4)
                    exit_slippage_cost = exit_slippage_unit * quantity

                    trade_slippage = round(entry_slippage_cost + exit_slippage_cost, 2)
                    comm = round(commission * 2.0, 2)

                    gross_pnl = round((exit_price_raw - entry_price_raw) * quantity, 2)
                    net_pnl = round(gross_pnl - trade_slippage - comm, 2)

                    curr_capital = round(curr_capital + net_pnl, 2)
                    cost_basis = entry_price * quantity
                    roi_pct = round((net_pnl / max(0.01, cost_basis)) * 100, 2)

                    if curr_capital > peak_capital:
                        peak_capital = curr_capital
                    dd = ((peak_capital - curr_capital) / peak_capital) * 100.0
                    if dd > max_drawdown:
                        max_drawdown = dd

                    trades.append(
                        BacktestTradeResult(
                            trade_id=trade_id,
                            symbol=symbol,
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

        total_trades = len(trades)
        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        win_rate = round((len(wins) / total_trades) * 100, 2) if total_trades > 0 else 0.0

        tot_win = sum(t.net_pnl for t in wins)
        tot_loss = abs(sum(t.net_pnl for t in losses))
        profit_factor = round(tot_win / tot_loss, 2) if tot_loss > 0 else (round(min(100.0, tot_win), 2) if tot_win > 0 else 0.0)

        sharpe = cls._calculate_sharpe(trades)
        net_pnl = round(curr_capital - capital, 2)
        net_roi = round((net_pnl / capital) * 100, 2)

        return BacktestSummaryResponse(
            strategy_name=strat_def.name,
            symbol=symbol,
            timeframe=timeframe,
            market=market,
            initial_capital=capital,
            final_capital=curr_capital,
            total_trades=total_trades,
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            average_win=round(tot_win / len(wins), 2) if wins else 0.0,
            average_loss=round(tot_loss / len(losses), 2) if losses else 0.0,
            profit_factor=profit_factor,
            expectancy=0.0,
            max_drawdown_pct=round(max_drawdown, 2),
            net_pnl=net_pnl,
            net_roi_pct=net_roi,
            trades=trades,
            disclaimer="SLICE_SIMULATION",
            strategy_id=strat_id,
            strategy_version="1.0.0",
            data_split="SLICE",
            dataset_identity=symbol,
            sharpe_ratio=sharpe,
            timestamp=datetime.utcnow().isoformat(),
        )

    @staticmethod
    def _calculate_sharpe(trades: List[Any]) -> Optional[float]:
        if len(trades) < 2:
            return None
        returns = [t.roi_pct / 100.0 for t in trades]
        mean_ret = sum(returns) / len(returns)
        var_ret = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = math.sqrt(var_ret)
        if std_ret > 0:
            return round((mean_ret / std_ret) * math.sqrt(252), 4)
        return 0.0

    @staticmethod
    def _calculate_sortino(trades: List[Any]) -> Optional[float]:
        if len(trades) < 2:
            return None
        returns = [t.roi_pct / 100.0 for t in trades]
        mean_ret = sum(returns) / len(returns)
        downside_diffs = [min(0.0, r) ** 2 for r in returns]
        downside_dev = math.sqrt(sum(downside_diffs) / len(returns))
        if downside_dev > 0:
            return round((mean_ret / downside_dev) * math.sqrt(252), 4)
        return None
