"""Service for AI vs Deterministic Strategy Comparison and Divergence Detection.

Evaluates concurrence and divergence between deterministic rule-based strategies
and quantitative ML (XGBoost) or LLM (Qwen) advisory systems.
Guarantees zero autonomous execution, zero human approval bypass, and fail-closed safety.
"""
import uuid
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.entities import (
    AIStrategyComparisonRecordModel,
    AlertEvent,
    AuditLog,
    utcnow,
)
from app.schemas.ai_comparison import (
    AIStrategyComparisonRecord,
    AIComparisonEvaluationRequest,
    AIComparisonFilter,
    AIComparisonSummary,
)

logger = logging.getLogger("vibe-trader-ai.ai_comparison")


class AIComparisonService:
    """Manages comparison records, divergence heuristics, alert deduplication, and summary metrics."""

    # In-memory deduplication cache: (symbol, timeframe) -> last alert timestamp (float)
    _alert_cooldown_cache: Dict[Tuple[str, str], float] = {}
    DEFAULT_ALERT_COOLDOWN_SECONDS: float = 300.0  # 5 minutes

    @classmethod
    def evaluate_concurrence(
        cls,
        deterministic_signal: str,
        deterministic_confidence: float,
        xgboost_direction: Optional[str] = None,
        xgboost_probability: Optional[float] = None,
        qwen_recommendation: Optional[str] = None,
        buy_divergence_prob_threshold: float = 0.40,
        sell_divergence_prob_threshold: float = 0.60,
    ) -> Tuple[str, Optional[str]]:
        """
        Determines whether deterministic and AI signals agree, diverge, or represent a cautionary state.

        Returns:
            Tuple[str, Optional[str]]: (concurrence_status, divergence_reason)
            concurrence_status in {"AGREE", "DIVERGE", "CAUTIONARY"}
        """
        if not deterministic_signal:
            raise ValueError("Deterministic signal must be provided and non-empty.")

        det_signal = deterministic_signal.strip().upper()
        if det_signal not in {"BUY", "SELL", "HOLD"}:
            raise ValueError(f"Invalid deterministic signal '{deterministic_signal}'; must be BUY, SELL, or HOLD.")

        qwen_rec = qwen_recommendation.strip().upper() if qwen_recommendation else None
        xgb_dir = xgboost_direction.strip().upper() if xgboost_direction else None

        # BUY Signal Evaluation
        if det_signal == "BUY":
            # 1. Severe Divergence: AI/ML contradicts BUY
            if xgboost_probability is not None and xgboost_probability < buy_divergence_prob_threshold:
                return (
                    "DIVERGE",
                    f"Deterministic BUY contradicted by low XGBoost probability ({xgboost_probability:.2f} < {buy_divergence_prob_threshold:.2f})."
                )
            if qwen_rec in {"SELL", "HOLD"}:
                return (
                    "DIVERGE",
                    f"Deterministic BUY contradicted by Qwen advisory recommendation ({qwen_rec})."
                )

            # 2. Cautionary: Weak conviction or abstention
            if xgb_dir == "ABSTAIN":
                return (
                    "CAUTIONARY",
                    "Deterministic BUY, but XGBoost model abstains due to near-50% probability uncertainty."
                )
            if xgboost_probability is not None and xgboost_probability < 0.55:
                return (
                    "CAUTIONARY",
                    f"Deterministic BUY with weak XGBoost probability ({xgboost_probability:.2f} in cautionary zone 0.40–0.55)."
                )

            # 3. Concurrence / Alignment
            return ("AGREE", None)

        # SELL Signal Evaluation
        elif det_signal == "SELL":
            # 1. Severe Divergence: AI/ML is strongly bullish
            if (
                xgboost_probability is not None
                and xgboost_probability > sell_divergence_prob_threshold
                and xgb_dir in {"UP", "BULLISH_UP"}
            ):
                return (
                    "DIVERGE",
                    f"Deterministic SELL contradicted by high bullish XGBoost probability ({xgboost_probability:.2f} > {sell_divergence_prob_threshold:.2f})."
                )
            if qwen_rec == "BUY":
                return (
                    "DIVERGE",
                    "Deterministic SELL contradicted by Qwen BUY recommendation."
                )

            # 2. Cautionary
            if xgb_dir == "ABSTAIN":
                return (
                    "CAUTIONARY",
                    "Deterministic SELL, but XGBoost model abstains due to uncertainty."
                )
            if xgboost_probability is not None and 0.45 <= xgboost_probability <= sell_divergence_prob_threshold:
                return (
                    "CAUTIONARY",
                    f"Deterministic SELL with mixed XGBoost probability ({xgboost_probability:.2f})."
                )

            # 3. Concurrence
            return ("AGREE", None)

        # HOLD Signal Evaluation
        else:  # det_signal == "HOLD"
            # 1. Cautionary tension if AI has strong directional conviction
            if xgboost_probability is not None and (xgboost_probability > 0.70 or xgboost_probability < 0.30):
                return (
                    "CAUTIONARY",
                    f"Deterministic HOLD while XGBoost exhibits strong directional probability ({xgboost_probability:.2f})."
                )
            if qwen_rec in {"BUY", "SELL"}:
                return (
                    "CAUTIONARY",
                    f"Deterministic HOLD while Qwen advisory recommends {qwen_rec}."
                )

            # 2. Consensus on neutrality
            return ("AGREE", None)

    @classmethod
    def record_comparison(
        cls,
        db: Session,
        req: AIComparisonEvaluationRequest,
    ) -> AIStrategyComparisonRecord:
        """Evaluates concurrence, logs deduplicated divergence alerts, and persists comparison record."""
        current_time_sec = int(time.time())
        record_timestamp = req.timestamp if req.timestamp is not None else current_time_sec

        # Timestamp staleness check
        staleness_notes = []
        if abs(current_time_sec - record_timestamp) > 86400:
            staleness_notes.append(f"Stale input timestamp ({record_timestamp}) exceeds 24 hours drift.")

        concurrence_status, divergence_reason = cls.evaluate_concurrence(
            deterministic_signal=req.deterministic_signal,
            deterministic_confidence=req.deterministic_confidence,
            xgboost_direction=req.xgboost_predicted_direction,
            xgboost_probability=req.xgboost_probability,
            qwen_recommendation=req.qwen_synthesized_recommendation,
            buy_divergence_prob_threshold=req.buy_divergence_prob_threshold,
            sell_divergence_prob_threshold=req.sell_divergence_prob_threshold,
        )

        all_notes = req.notes or ""
        if staleness_notes:
            all_notes = f"{all_notes} [{' '.join(staleness_notes)}]".strip()

        record_id = f"CMP-{uuid.uuid4().hex[:10].upper()}"

        model_obj = AIStrategyComparisonRecordModel(
            record_id=record_id,
            timestamp=record_timestamp,
            symbol=req.symbol.strip().upper(),
            market=req.market.strip().upper(),
            timeframe=req.timeframe.strip().upper(),
            deterministic_strategy_name=req.deterministic_strategy_name,
            deterministic_signal=req.deterministic_signal.strip().upper(),
            deterministic_confidence=req.deterministic_confidence,
            xgboost_predicted_direction=req.xgboost_predicted_direction,
            xgboost_probability=req.xgboost_probability,
            qwen_synthesized_recommendation=req.qwen_synthesized_recommendation,
            concurrence_status=concurrence_status,
            divergence_reason=divergence_reason,
            human_approval_status="NOT_REQUIRED" if req.deterministic_signal.upper() != "BUY" else "PENDING",
            paper_trade_execution_status="NOT_EXECUTED",
            notes=all_notes or None,
            created_at=utcnow(),
        )

        db.add(model_obj)

        # Alert logging on divergence with deduplication
        if concurrence_status == "DIVERGE":
            cls._maybe_dispatch_divergence_alert(db, model_obj)

        db.commit()
        db.refresh(model_obj)

        return AIStrategyComparisonRecord(
            record_id=model_obj.record_id,
            timestamp=model_obj.timestamp,
            symbol=model_obj.symbol,
            market=model_obj.market,
            timeframe=model_obj.timeframe,
            deterministic_strategy_name=model_obj.deterministic_strategy_name,
            deterministic_signal=model_obj.deterministic_signal,
            deterministic_confidence=model_obj.deterministic_confidence,
            xgboost_predicted_direction=model_obj.xgboost_predicted_direction,
            xgboost_probability=model_obj.xgboost_probability,
            qwen_synthesized_recommendation=model_obj.qwen_synthesized_recommendation,
            concurrence_status=model_obj.concurrence_status,
            divergence_reason=model_obj.divergence_reason,
            human_approval_status=model_obj.human_approval_status,
            paper_trade_execution_status=model_obj.paper_trade_execution_status,
            realized_outcome=model_obj.realized_outcome,
            realized_pnl=model_obj.realized_pnl,
            notes=model_obj.notes,
            created_at=model_obj.created_at.isoformat() if model_obj.created_at else None,
        )

    @classmethod
    def _maybe_dispatch_divergence_alert(
        cls,
        db: Session,
        record: AIStrategyComparisonRecordModel,
    ) -> None:
        """Dispatches an AlertEvent if outside the cooldown threshold for (symbol, timeframe)."""
        cache_key = (record.symbol, record.timeframe)
        now_ts = time.time()
        last_triggered = cls._alert_cooldown_cache.get(cache_key, 0.0)

        if (now_ts - last_triggered) < cls.DEFAULT_ALERT_COOLDOWN_SECONDS:
            logger.info(
                f"Suppressed duplicate divergence alert for {record.symbol} {record.timeframe} "
                f"(cooldown active: {int(now_ts - last_triggered)}s / {cls.DEFAULT_ALERT_COOLDOWN_SECONDS}s)"
            )
            return

        cls._alert_cooldown_cache[cache_key] = now_ts

        alert_event = AlertEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            alert_type="AI_DIVERGENCE",
            symbol=record.symbol,
            market=record.market,
            title=f"AI Divergence Alert: {record.symbol} ({record.deterministic_strategy_name})",
            message=record.divergence_reason or f"Signal divergence detected between deterministic rule and AI advisory.",
            severity="WARNING",
            details_json=json.dumps({
                "record_id": record.record_id,
                "deterministic_signal": record.deterministic_signal,
                "xgboost_probability": record.xgboost_probability,
                "xgboost_direction": record.xgboost_predicted_direction,
                "qwen_recommendation": record.qwen_synthesized_recommendation,
            }),
            is_read=False,
            triggered_at=utcnow(),
        )
        db.add(alert_event)

        # Audit log trail
        audit_entry = AuditLog(
            event_type="AI_DIVERGENCE_DETECTED",
            action="FLAG_DIVERGENCE",
            actor="AI_COMPARISON_SERVICE",
            symbol=record.symbol,
            market=record.market,
            details_json=json.dumps({
                "record_id": record.record_id,
                "strategy": record.deterministic_strategy_name,
                "signal": record.deterministic_signal,
                "divergence_reason": record.divergence_reason,
            }),
            timestamp=utcnow(),
        )
        db.add(audit_entry)

    @classmethod
    def get_summary(
        cls,
        db: Session,
        filter_params: AIComparisonFilter,
    ) -> AIComparisonSummary:
        """Retrieves filtered comparison records and calculates summary agreement/divergence statistics."""
        query = db.query(AIStrategyComparisonRecordModel)

        if filter_params.symbol:
            query = query.filter(AIStrategyComparisonRecordModel.symbol == filter_params.symbol.strip().upper())
        if filter_params.timeframe:
            query = query.filter(AIStrategyComparisonRecordModel.timeframe == filter_params.timeframe.strip().upper())
        if filter_params.concurrence_status:
            query = query.filter(
                AIStrategyComparisonRecordModel.concurrence_status == filter_params.concurrence_status.strip().upper()
            )
        if filter_params.start_timestamp:
            query = query.filter(AIStrategyComparisonRecordModel.timestamp >= filter_params.start_timestamp)
        if filter_params.end_timestamp:
            query = query.filter(AIStrategyComparisonRecordModel.timestamp <= filter_params.end_timestamp)

        total_records = query.count()

        agreement_count = query.filter(AIStrategyComparisonRecordModel.concurrence_status == "AGREE").count()
        divergence_count = query.filter(AIStrategyComparisonRecordModel.concurrence_status == "DIVERGE").count()
        cautionary_count = query.filter(AIStrategyComparisonRecordModel.concurrence_status == "CAUTIONARY").count()

        agreement_rate = round(agreement_count / total_records, 4) if total_records > 0 else 0.0
        divergence_rate = round(divergence_count / total_records, 4) if total_records > 0 else 0.0
        cautionary_rate = round(cautionary_count / total_records, 4) if total_records > 0 else 0.0

        # Outcome-conditioned win rates (if completed trades with outcome exist)
        agree_completed = query.filter(
            AIStrategyComparisonRecordModel.concurrence_status == "AGREE",
            AIStrategyComparisonRecordModel.realized_outcome.in_(["WIN", "LOSS"])
        ).all()
        agree_wins = sum(1 for r in agree_completed if r.realized_outcome == "WIN")
        agreement_trade_win_rate = (
            round(agree_wins / len(agree_completed), 4) if len(agree_completed) > 0 else None
        )

        diverge_completed = query.filter(
            AIStrategyComparisonRecordModel.concurrence_status == "DIVERGE",
            AIStrategyComparisonRecordModel.realized_outcome.in_(["WIN", "LOSS"])
        ).all()
        diverge_wins = sum(1 for r in diverge_completed if r.realized_outcome == "WIN")
        divergence_trade_win_rate = (
            round(diverge_wins / len(diverge_completed), 4) if len(diverge_completed) > 0 else None
        )

        records_rows = (
            query.order_by(desc(AIStrategyComparisonRecordModel.timestamp))
            .offset(filter_params.offset)
            .limit(filter_params.limit)
            .all()
        )

        records = [
            AIStrategyComparisonRecord(
                record_id=r.record_id,
                timestamp=r.timestamp,
                symbol=r.symbol,
                market=r.market,
                timeframe=r.timeframe,
                deterministic_strategy_name=r.deterministic_strategy_name,
                deterministic_signal=r.deterministic_signal,
                deterministic_confidence=r.deterministic_confidence,
                xgboost_predicted_direction=r.xgboost_predicted_direction,
                xgboost_probability=r.xgboost_probability,
                qwen_synthesized_recommendation=r.qwen_synthesized_recommendation,
                concurrence_status=r.concurrence_status,
                divergence_reason=r.divergence_reason,
                human_approval_status=r.human_approval_status,
                paper_trade_execution_status=r.paper_trade_execution_status,
                realized_outcome=r.realized_outcome,
                realized_pnl=r.realized_pnl,
                notes=r.notes,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in records_rows
        ]

        return AIComparisonSummary(
            total_records=total_records,
            agreement_count=agreement_count,
            divergence_count=divergence_count,
            cautionary_count=cautionary_count,
            agreement_rate=agreement_rate,
            divergence_rate=divergence_rate,
            cautionary_rate=cautionary_rate,
            agreement_trade_win_rate=agreement_trade_win_rate,
            divergence_trade_win_rate=divergence_trade_win_rate,
            records=records,
        )

    @staticmethod
    def verify_safety_invariants(
        concurrence_status: str,
        human_approval_given: bool,
        risk_guardian_verdict: str,
    ) -> Dict[str, Any]:
        """
        Validates safety invariants:
        1. AI Agreement NEVER bypasses human approval for BUY orders.
        2. Even if AI and Strategy AGREE, Risk Guardian rejection blocks order.
        3. Divergence NEVER triggers an order execution.
        """
        allowed_to_execute = False
        block_reasons = []

        if concurrence_status == "DIVERGE":
            block_reasons.append("Execution blocked: Divergence between strategy and AI cannot execute trades.")

        if risk_guardian_verdict.upper() == "REJECTED":
            block_reasons.append("Execution blocked: Deterministic Risk Guardian rejected the trade.")

        if not human_approval_given:
            block_reasons.append("Execution blocked: Explicit human approval has not been granted.")

        if not block_reasons:
            allowed_to_execute = True

        return {
            "allowed_to_execute": allowed_to_execute,
            "block_reasons": block_reasons,
            "human_approval_required": True,
            "risk_guardian_authoritative": True,
        }
