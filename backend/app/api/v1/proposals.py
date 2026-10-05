"""Buy Proposals API Router for Vibe Trader AI."""
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import (
    BuyProposal,
    Position,
    PaperTrade,
    RiskSettings,
    utcnow,
)
from app.schemas.workflow import (
    BuyProposalRead,
    BuyProposalApproveRequest,
    BuyProposalRejectRequest,
)
from app.services.risk_service import RiskService
from app.services.broker_adapter import paper_broker
from app.services.audit_service import AuditService
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService
from app.services.strategy_engine import StrategyEngine

router = APIRouter(prefix="/proposals", tags=["Buy Proposals & Approval Center"])


def _proposal_to_schema(p: BuyProposal) -> BuyProposalRead:
    matched = json.loads(p.matched_conditions_json or "[]")
    unmatched = json.loads(p.unmatched_conditions_json or "[]")
    indicators = json.loads(p.supporting_indicators_json or "{}")

    return BuyProposalRead(
        id=p.id,
        proposal_id=p.proposal_id,
        symbol=p.symbol,
        market=p.market,
        strategy_id=p.strategy_id,
        strategy_name=p.strategy_name,
        current_price=p.current_price,
        proposed_entry_price=p.proposed_entry_price,
        proposed_quantity=p.proposed_quantity,
        stop_loss=p.stop_loss,
        target=p.target,
        risk_amount=p.risk_amount,
        risk_reward_ratio=p.risk_reward_ratio,
        estimated_costs=p.estimated_costs,
        matched_conditions=matched,
        unmatched_conditions=unmatched,
        supporting_indicators=indicators,
        confidence_score=p.confidence_score,
        confidence_method=p.confidence_method,
        explanation=p.explanation,
        uncertainties=p.uncertainties,
        data_source=p.data_source,
        data_timestamp=p.data_timestamp,
        expires_at=p.expires_at,
        status=p.status,
        rejection_reason=p.rejection_reason,
        risk_check_details=p.risk_check_details,
        version=p.version,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=List[BuyProposalRead], summary="List BUY Proposals")
def list_proposals(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter: PENDING, APPROVED, REJECTED, EXPIRED, EXECUTED"),
    symbol: Optional[str] = Query(None, description="Filter by instrument symbol"),
    market: Optional[str] = Query(None, description="Filter by market segment"),
    db: Session = Depends(get_db),
) -> List[BuyProposalRead]:
    """Retrieve all AI BUY proposals with optional status or market filter."""
    query = db.query(BuyProposal).order_by(BuyProposal.created_at.desc())
    if status_filter:
        query = query.filter(BuyProposal.status == status_filter.upper())
    if symbol:
        query = query.filter(BuyProposal.symbol == symbol)
    if market:
        query = query.filter(BuyProposal.market == market.upper())

    proposals = query.limit(50).all()
    # Check expiry for pending proposals
    now = utcnow()
    modified = False
    for p in proposals:
        p_exp = p.expires_at.replace(tzinfo=None) if p.expires_at.tzinfo else p.expires_at
        if p.status == "PENDING" and p_exp <= now:
            p.status = "EXPIRED"
            modified = True
    if modified:
        db.commit()

    return [_proposal_to_schema(p) for p in proposals]


@router.get("/{proposal_id}", response_model=BuyProposalRead, summary="Get Single Proposal")
def get_proposal(proposal_id: str, db: Session = Depends(get_db)) -> BuyProposalRead:
    p = db.query(BuyProposal).filter(
        (BuyProposal.proposal_id == proposal_id) | (BuyProposal.id == int(proposal_id) if proposal_id.isdigit() else False)
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return _proposal_to_schema(p)


@router.post("/{proposal_id}/approve", summary="Explicitly Approve BUY Proposal")
def approve_proposal(
    proposal_id: str,
    req: BuyProposalApproveRequest,
    db: Session = Depends(get_db),
):
    """
    Explicit user approval of a BUY proposal.
    Triggers independent server-side risk checks and executes paper order if valid.
    """
    p = db.query(BuyProposal).filter(
        (BuyProposal.proposal_id == proposal_id) | (BuyProposal.id == int(proposal_id) if proposal_id.isdigit() else False)
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if p.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot approve proposal with status '{p.status}'. Only PENDING proposals can be approved.")

    now = utcnow()
    if req.expected_version is not None and req.expected_version != p.version:
        raise HTTPException(
            status_code=400,
            detail=f"Proposal version mismatch (Expected v{req.expected_version}, but current proposal is v{p.version}). Previous approval is invalidated."
        )

    p_exp = p.expires_at.replace(tzinfo=None) if p.expires_at.tzinfo else p.expires_at
    if now > p_exp:
        p.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="Proposal has expired. A fresh proposal must be generated.")

    # Atomic state transition from PENDING to EXECUTING to prevent concurrent race conditions / double-execution
    rows_updated = db.query(BuyProposal).filter(
        BuyProposal.id == p.id,
        BuyProposal.status == "PENDING"
    ).update({"status": "EXECUTING"}, synchronize_session="fetch")
    db.commit()

    if rows_updated == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve proposal with status '{p.status}'. Only PENDING proposals can be approved."
        )

    # Independent Server-Side Risk Validation
    passed, reason, details = RiskService.validate_buy_execution(db, p)
    if not passed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Order blocked by Risk Validation: {reason}"
        )

    # Risk checks passed! Execute paper BUY order
    fill = paper_broker.submit_buy_order(
        symbol=p.symbol,
        market=p.market,
        quantity=p.proposed_quantity,
        price=p.proposed_entry_price,
        stop_loss=p.stop_loss,
        target=p.target,
    )

    if fill.get("status") in ["FAILED", "REJECTED", "CANCELLED"]:
        p.status = "REJECTED"
        p.rejection_reason = f"Paper order failed at simulated broker: {fill.get('reason', fill.get('status'))}"
        p.updated_at = now
        db.commit()

        AuditService.log_event(
            db=db,
            event_type="ORDER_EXECUTION_FAILED",
            action=f"Order {fill['order_id']} failed at broker: {fill.get('reason', fill.get('status'))}",
            actor="PAPER_BROKER",
            symbol=p.symbol,
            market=p.market,
            proposal_id=p.proposal_id,
            details=fill,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Paper order execution failed ({fill.get('status')}): {fill.get('reason')}. No position opened."
        )

    # Use actual filled quantity (supports PARTIAL fills)
    executed_qty = fill.get("quantity", p.proposed_quantity)

    pos_id = f"POS-{uuid.uuid4().hex[:8].upper()}"
    position = Position(
        position_id=pos_id,
        proposal_id=p.id,
        symbol=p.symbol,
        market=p.market,
        side="LONG",
        quantity=executed_qty,
        entry_price=fill["fill_price"],
        current_price=fill["fill_price"],
        stop_loss=p.stop_loss,
        target=p.target,
        unrealized_pnl=0.0,
        unrealized_pnl_pct=0.0,
        highest_price=fill["fill_price"],
        status="OPEN",
        created_at=now,
    )
    db.add(position)

    # Mirror into PaperTrade for legacy portfolio integration
    paper_trade = PaperTrade(
        symbol=p.symbol,
        market=p.market,
        side="Long",
        order_type="MARKET",
        quantity=executed_qty,
        entry_price=fill["fill_price"],
        stop_loss=p.stop_loss,
        take_profit=p.target,
        status="Open",
        notes=f"Auto-executed from approved AI Proposal {p.proposal_id}. {req.notes or ''}".strip(),
        created_at=now,
    )
    db.add(paper_trade)

    p.status = "EXECUTED"
    p.updated_at = now
    db.commit()
    db.refresh(position)

    # Record Audit Events
    AuditService.log_event(
        db=db,
        event_type="PROPOSAL_APPROVED",
        action=f"User explicitly approved Proposal {p.proposal_id}",
        actor="USER",
        symbol=p.symbol,
        market=p.market,
        proposal_id=p.proposal_id,
        position_id=pos_id,
        details={"notes": req.notes, "approval_time": now.isoformat()},
    )
    AuditService.log_event(
        db=db,
        event_type="ORDER_EXECUTED",
        action=f"Executed virtual BUY order for {p.proposed_quantity} {p.symbol} @ {fill['fill_price']}",
        actor="PAPER_BROKER",
        symbol=p.symbol,
        market=p.market,
        proposal_id=p.proposal_id,
        position_id=pos_id,
        details=fill,
    )

    return {
        "status": "APPROVED_AND_EXECUTED",
        "proposal_id": p.proposal_id,
        "position_id": position.position_id,
        "symbol": p.symbol,
        "fill_price": fill["fill_price"],
        "quantity": p.proposed_quantity,
        "fees": fill["fees"],
        "message": f"Successfully executed BUY for {p.proposed_quantity} {p.symbol} at ${fill['fill_price']:,.4f}.",
    }


@router.post("/{proposal_id}/reject", summary="Explicitly Reject BUY Proposal")
def reject_proposal(
    proposal_id: str,
    req: BuyProposalRejectRequest,
    db: Session = Depends(get_db),
):
    """
    Explicit user rejection of a BUY proposal. Prevents execution and logs event.
    """
    p = db.query(BuyProposal).filter(
        (BuyProposal.proposal_id == proposal_id) | (BuyProposal.id == int(proposal_id) if proposal_id.isdigit() else False)
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if p.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot reject proposal with status '{p.status}'.")

    now = utcnow()
    p.status = "REJECTED"
    p.rejection_reason = req.reason
    p.updated_at = now
    db.commit()

    AuditService.log_event(
        db=db,
        event_type="PROPOSAL_REJECTED",
        action=f"User rejected Proposal {p.proposal_id}: {req.reason}",
        actor="USER",
        symbol=p.symbol,
        market=p.market,
        proposal_id=p.proposal_id,
        details={"reason": req.reason, "rejection_time": now.isoformat()},
    )

    return {
        "status": "REJECTED",
        "proposal_id": p.proposal_id,
        "rejection_reason": req.reason,
        "message": f"Proposal {p.proposal_id} was rejected and will not be executed.",
    }


@router.post("/scan-and-generate", summary="Scan Symbol for BUY Opportunities")
def scan_and_generate_proposal(
    symbol: str = Query("EUR/USD", description="Symbol to analyze"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D"),
    market: str = Query("FOREX", description="Market: FOREX, NSE, MCX"),
    db: Session = Depends(get_db),
):
    """Run real-time technical analysis on a symbol and generate a BUY proposal if criteria match."""
    market_service = MarketDataService(db=db)
    ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
    if not ohlc.candles or len(ohlc.candles) < 20:
        raise HTTPException(status_code=400, detail="Insufficient candle data to evaluate opportunities.")

    indicators = IndicatorsService.compute_all_indicators(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)
    patterns = PatternService.detect_patterns(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)
    sr = SupportResistanceService.calculate_zones(candles=ohlc.candles, symbol=symbol, timeframe=timeframe)

    proposal = StrategyEngine.evaluate_opportunity(
        db=db,
        symbol=symbol,
        market=market,
        timeframe=timeframe,
        candles=ohlc.candles,
        indicators=indicators,
        patterns=patterns,
        sr=sr,
    )

    if not proposal:
        return {
            "opportunity_detected": False,
            "symbol": symbol,
            "message": "Conditions did not satisfy minimum confluence rules for a high-probability BUY setup at this time.",
        }

    return {
        "opportunity_detected": True,
        "proposal": _proposal_to_schema(proposal),
    }
