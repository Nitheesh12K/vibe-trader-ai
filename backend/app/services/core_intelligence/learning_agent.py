import time
from typing import Optional
from sqlalchemy.orm import Session
from app.models.entities import (
    TradeReport,
    StrategyCandidate,
    Strategy,
    utcnow,
)
from app.schemas.intelligence import LearningSummaryOutput, AgentMetadata


class LearningAgent:
    """Logical agent measuring performance metrics and generating candidate adaptations."""

    NAME = "Learning Agent"
    VERSION = "1.0.0"

    _cached_summary: Optional[LearningSummaryOutput] = None
    _last_trade_count: int = -1
    _last_candidate_count: int = -1

    @classmethod
    def evaluate_performance(
        cls,
        db: Session,
        force_refresh: bool = False,
    ) -> LearningSummaryOutput:
        start_time = time.perf_counter()
        now = utcnow()

        trade_count = db.query(TradeReport).count()
        candidate_count = db.query(StrategyCandidate).count()

        # Event-driven optimization: Return cached summary in 0.0ms if no new trades/candidates occurred
        if not force_refresh and cls._cached_summary is not None:
            if trade_count == cls._last_trade_count and candidate_count == cls._last_candidate_count:
                cached = cls._cached_summary.model_copy()
                cached.agent = AgentMetadata(
                    name=cls.NAME,
                    version=cls.VERSION,
                    status="COMPLETED",
                    execution_time_ms=0.0,
                    timestamp=now,
                )
                cached.timestamp = now
                return cached

        reports = db.query(TradeReport).order_by(TradeReport.id.asc()).all()
        candidates = db.query(StrategyCandidate).all()

        total_trades = len(reports)
        if total_trades == 0:
            # Baseline when no trades have been completed yet
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            meta = AgentMetadata(
                name=cls.NAME,
                version=cls.VERSION,
                status="COMPLETED",
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=now,
            )
            output = LearningSummaryOutput(
                agent=meta,
                total_trades_analyzed=0,
                win_rate=0.0,
                profit_factor=0.0,
                expectancy=0.0,
                average_win=0.0,
                average_loss=0.0,
                max_drawdown_pct=0.0,
                average_slippage=0.0,
                performance_by_regime={},
                performance_deterioration_detected=False,
                deterioration_reasons=["Awaiting initial completed paper trades for empirical performance baseline."],
                candidate_strategy_count=len(candidates),
                timestamp=now,
            )
            cls._cached_summary = output
            cls._last_trade_count = 0
            cls._last_candidate_count = len(candidates)
            return output

        wins = [r for r in reports if r.net_pnl > 0]
        losses = [r for r in reports if r.net_pnl <= 0]

        win_rate = (len(wins) / total_trades) * 100.0
        total_gross_win = sum(r.net_pnl for r in wins)
        total_gross_loss = abs(sum(r.net_pnl for r in losses))

        profit_factor = (total_gross_win / total_gross_loss) if total_gross_loss > 0 else (total_gross_win if total_gross_win > 0 else 1.0)
        avg_win = (total_gross_win / len(wins)) if wins else 0.0
        avg_loss = (total_gross_loss / len(losses)) if losses else 0.0

        loss_rate = (len(losses) / total_trades) if total_trades > 0 else 0.0
        expectancy = ((win_rate / 100.0) * avg_win) - (loss_rate * avg_loss)

        avg_slippage = (sum(r.slippage for r in reports) / total_trades) if total_trades > 0 else 0.0

        # Calculate max drawdown
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for r in reports:
            cumulative += r.net_pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        max_dd_pct = (max_dd / 100000.0) * 100.0  # relative to simulated balance base

        # Breakdown by Market
        perf_by_market = {}
        for market in ["FOREX", "NSE", "MCX"]:
            m_trades = [r for r in reports if r.market == market]
            if m_trades:
                m_wins = [r for r in m_trades if r.net_pnl > 0]
                m_net = sum(r.net_pnl for r in m_trades)
                perf_by_market[market] = {
                    "trades": float(len(m_trades)),
                    "win_rate": round((len(m_wins) / len(m_trades)) * 100.0, 1),
                    "net_pnl": round(m_net, 2),
                }

        # Deterioration Detection
        deterioration = False
        reasons = []

        # Check recent trade window (last 5 trades)
        if len(reports) >= 5:
            recent_trades = reports[-5:]
            recent_wins = [r for r in recent_trades if r.net_pnl > 0]
            recent_win_rate = (len(recent_wins) / len(recent_trades)) * 100.0
            if recent_win_rate < 30.0:
                deterioration = True
                reasons.append(f"Recent win rate decayed to {recent_win_rate:.1f}% across last 5 trades.")

        if profit_factor < 1.0 and total_trades >= 3:
            deterioration = True
            reasons.append(f"Cumulative profit factor ({profit_factor:.2f}) is below 1.0 threshold.")

        if max_dd_pct > 10.0:
            deterioration = True
            reasons.append(f"Max drawdown ({max_dd_pct:.1f}%) exceeds safety ceiling (10.0%).")

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        meta = AgentMetadata(
            name=cls.NAME,
            version=cls.VERSION,
            status="COMPLETED",
            execution_time_ms=round(elapsed_ms, 2),
            timestamp=now,
        )

        output = LearningSummaryOutput(
            agent=meta,
            total_trades_analyzed=total_trades,
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            expectancy=round(expectancy, 2),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            max_drawdown_pct=round(max_dd_pct, 2),
            average_slippage=round(avg_slippage, 4),
            performance_by_regime=perf_by_market,
            performance_deterioration_detected=deterioration,
            deterioration_reasons=reasons,
            candidate_strategy_count=len(candidates),
            timestamp=now,
        )
        cls._cached_summary = output
        cls._last_trade_count = total_trades
        cls._last_candidate_count = len(candidates)
        return output
