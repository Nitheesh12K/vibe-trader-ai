"""Vibe Intelligence Core API Router: Multi-agent coordination, learning, and controlled adaptation."""
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import StrategyCandidate, Strategy, utcnow
from app.schemas.intelligence import (
    IntelligenceCycleResponse,
    IntelligenceStatusResponse,
    LearningSummaryOutput,
    OutcomeEvaluationOutput,
    StrategyCandidateRead,
    StrategyCandidateCreate,
    StrategyCandidateAdvanceRequest,
)
from app.services.core_intelligence.coordinator import VibeIntelligenceCore
from app.services.core_intelligence.learning_agent import LearningAgent
from app.services.core_intelligence.outcome_evaluator import OutcomeEvaluator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/intelligence", tags=["Vibe Intelligence Core"])


@router.get("/status", response_model=IntelligenceStatusResponse, summary="Get Vibe Intelligence Core Status")
def get_intelligence_status(db: Session = Depends(get_db)) -> IntelligenceStatusResponse:
    """Return real-time fleet status of all logical agents and surveillance health."""
    return VibeIntelligenceCore.get_status(db=db)


@router.post("/cycle", response_model=IntelligenceCycleResponse, summary="Execute Multi-Agent Intelligence Cycle")
def run_intelligence_cycle(
    symbol: str = Query("EUR/USD", description="Symbol to perceive, reason, and plan for"),
    market: str = Query("FOREX", description="Market category: FOREX, NSE, MCX"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    db: Session = Depends(get_db),
) -> IntelligenceCycleResponse:
    """
    Run an end-to-end multi-agent evaluation cycle:
    Perception -> Reasoning -> Memory -> Planning -> Risk Guardian -> Learning & Trade Management.
    """
    return VibeIntelligenceCore.run_cycle(
        db=db,
        symbol=symbol,
        market=market,
        timeframe=timeframe,
    )


@router.get("/learning/summary", response_model=LearningSummaryOutput, summary="Get Empirical Learning & Expectancy Analysis")
def get_learning_summary(db: Session = Depends(get_db)) -> LearningSummaryOutput:
    """Retrieve quantitative performance evaluation and strategy decay / deterioration alerts."""
    return LearningAgent.evaluate_performance(db=db)


@router.post("/evaluate-outcome/{report_id}", response_model=OutcomeEvaluationOutput, summary="Evaluate Completed Trade Outcome")
def evaluate_outcome(report_id: int, db: Session = Depends(get_db)) -> OutcomeEvaluationOutput:
    """Perform post-trade attribution comparing planned vs actual entry, exit, and slippage."""
    outcome = OutcomeEvaluator.evaluate_trade_report(db=db, report_id=report_id)
    if not outcome:
        raise HTTPException(status_code=404, detail="Trade report not found")
    return outcome


# ============================================================================
# Controlled Strategy Adaptation Lifecycle APIs
# ============================================================================

@router.get("/strategies/candidates", response_model=List[StrategyCandidateRead], summary="List Strategy Candidates")
def list_strategy_candidates(
    stage: Optional[str] = Query(None, description="Filter by lifecycle stage: CANDIDATE, SANDBOX, BACKTESTED, REVIEW, ACTIVATED"),
    db: Session = Depends(get_db),
) -> List[StrategyCandidateRead]:
    """Retrieve strategy adaptation candidates across the controlled lifecycle pipeline."""
    q = db.query(StrategyCandidate)
    if stage:
        q = q.filter(StrategyCandidate.lifecycle_stage == stage.upper())
    candidates = q.order_by(StrategyCandidate.id.desc()).all()

    # Parse validation_metrics_json for schema
    result = []
    for c in candidates:
        metrics = {}
        try:
            metrics = json.loads(c.validation_metrics_json or "{}")
        except Exception:
            pass
        item = StrategyCandidateRead(
            id=c.id,
            candidate_id=c.candidate_id,
            base_strategy_id=c.base_strategy_id,
            name=c.name,
            version=c.version,
            market=c.market,
            timeframe=c.timeframe,
            parameters_json=c.parameters_json,
            rationale=c.rationale,
            lifecycle_stage=c.lifecycle_stage,  # type: ignore
            validation_metrics=metrics,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        result.append(item)
    return result


@router.post("/strategies/candidates", response_model=StrategyCandidateRead, status_code=status.HTTP_201_CREATED, summary="Propose Candidate Strategy Adaptation")
def create_strategy_candidate(
    req: StrategyCandidateCreate,
    db: Session = Depends(get_db),
) -> StrategyCandidateRead:
    """Propose a new candidate strategy adaptation for sandbox evaluation."""
    candidate_id = f"CAND-{uuid.uuid4().hex[:8].upper()}"
    cand = StrategyCandidate(
        candidate_id=candidate_id,
        base_strategy_id=req.base_strategy_id,
        name=req.name,
        version=req.version,
        market=req.market,
        timeframe=req.timeframe,
        parameters_json=req.parameters_json,
        rationale=req.rationale,
        lifecycle_stage="CANDIDATE",
        validation_metrics_json="{}",
        is_active=False,
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    AuditService.log_event(
        db=db,
        event_type="STRATEGY_CANDIDATE_CREATED",
        action=f"Proposed strategy candidate {cand.name} ({cand.version})",
        actor="LEARNING_AGENT",
        market=cand.market,
        details={"candidate_id": cand.candidate_id, "rationale": cand.rationale},
    )

    return StrategyCandidateRead(
        id=cand.id,
        candidate_id=cand.candidate_id,
        base_strategy_id=cand.base_strategy_id,
        name=cand.name,
        version=cand.version,
        market=cand.market,
        timeframe=cand.timeframe,
        parameters_json=cand.parameters_json,
        rationale=cand.rationale,
        lifecycle_stage=cand.lifecycle_stage,  # type: ignore
        validation_metrics={},
        is_active=cand.is_active,
        created_at=cand.created_at,
        updated_at=cand.updated_at,
    )


@router.post("/strategies/candidates/{candidate_id}/advance", response_model=StrategyCandidateRead, summary="Advance Candidate Lifecycle Stage")
def advance_strategy_candidate(
    candidate_id: str,
    req: StrategyCandidateAdvanceRequest,
    db: Session = Depends(get_db),
) -> StrategyCandidateRead:
    """
    Advance candidate through strict lifecycle stages:
    CANDIDATE -> SANDBOX -> BACKTESTED -> OUT_OF_SAMPLE_VALIDATED -> PAPER_TRADING -> REVIEW -> ACTIVATED.
    """
    cand = (
        db.query(StrategyCandidate)
        .filter((StrategyCandidate.candidate_id == candidate_id) | (StrategyCandidate.id == int(candidate_id) if candidate_id.isdigit() else False))
        .first()
    )
    if not cand:
        raise HTTPException(status_code=404, detail="Strategy candidate not found")

    old_stage = cand.lifecycle_stage
    cand.lifecycle_stage = req.target_stage
    cand.updated_at = utcnow()
    db.commit()
    db.refresh(cand)

    AuditService.log_event(
        db=db,
        event_type="STRATEGY_STAGE_ADVANCED",
        action=f"Candidate {cand.candidate_id} advanced from {old_stage} to {req.target_stage}",
        actor="USER",
        details={"candidate_id": cand.candidate_id, "notes": req.validation_notes},
    )

    metrics = {}
    try:
        metrics = json.loads(cand.validation_metrics_json or "{}")
    except Exception:
        pass

    return StrategyCandidateRead(
        id=cand.id,
        candidate_id=cand.candidate_id,
        base_strategy_id=cand.base_strategy_id,
        name=cand.name,
        version=cand.version,
        market=cand.market,
        timeframe=cand.timeframe,
        parameters_json=cand.parameters_json,
        rationale=cand.rationale,
        lifecycle_stage=cand.lifecycle_stage,  # type: ignore
        validation_metrics=metrics,
        is_active=cand.is_active,
        created_at=cand.created_at,
        updated_at=cand.updated_at,
    )


@router.post("/strategies/candidates/{candidate_id}/activate", response_model=StrategyCandidateRead, summary="Explicitly Activate Validated Strategy")
def activate_strategy_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> StrategyCandidateRead:
    """
    Explicit human authorization required to promote a thoroughly validated strategy into live active deployment.
    """
    cand = (
        db.query(StrategyCandidate)
        .filter((StrategyCandidate.candidate_id == candidate_id) | (StrategyCandidate.id == int(candidate_id) if candidate_id.isdigit() else False))
        .first()
    )
    if not cand:
        raise HTTPException(status_code=404, detail="Strategy candidate not found")

    # Promotion to live active Strategy
    active_strat = Strategy(
        name=f"{cand.name} ({cand.version})",
        description=f"Promoted from candidate {cand.candidate_id}. Rationale: {cand.rationale}",
        market=cand.market,
        timeframe=cand.timeframe,
        parameters_json=cand.parameters_json,
        is_active=True,
    )
    db.add(active_strat)

    cand.lifecycle_stage = "ACTIVATED"
    cand.is_active = True
    cand.updated_at = utcnow()
    db.commit()
    db.refresh(cand)

    AuditService.log_event(
        db=db,
        event_type="STRATEGY_ACTIVATED",
        action=f"User authorized deployment of {cand.name} ({cand.version}) into live active strategy pool",
        actor="USER",
        details={"candidate_id": cand.candidate_id, "strategy_name": active_strat.name},
    )

    metrics = {}
    try:
        metrics = json.loads(cand.validation_metrics_json or "{}")
    except Exception:
        pass

    return StrategyCandidateRead(
        id=cand.id,
        candidate_id=cand.candidate_id,
        base_strategy_id=cand.base_strategy_id,
        name=cand.name,
        version=cand.version,
        market=cand.market,
        timeframe=cand.timeframe,
        parameters_json=cand.parameters_json,
        rationale=cand.rationale,
        lifecycle_stage=cand.lifecycle_stage,  # type: ignore
        validation_metrics=metrics,
        is_active=cand.is_active,
        created_at=cand.created_at,
        updated_at=cand.updated_at,
    )
