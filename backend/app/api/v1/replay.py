"""Market Replay Simulator API router."""
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.entities import ReplaySessionCreate, ReplaySessionRead, ReplayStepRequest
from app.services.replay_service import replay_service

router = APIRouter(prefix="/replay", tags=["Market Replay"])


def format_session_read(session, latest_step: Optional[Dict[str, Any]] = None) -> ReplaySessionRead:
    state = json.loads(session.state_json) if isinstance(session.state_json, str) else session.state_json
    all_candles = state.get("all_candles", [])
    cur_candle = None
    cur_price = None

    if all_candles and session.current_index < len(all_candles):
        cur_candle = all_candles[session.current_index]
        cur_price = cur_candle["close"]

    unrealized = sum((p.get("unrealized_pnl", 0.0)) for p in state.get("open_positions", []))

    return ReplaySessionRead(
        id=session.id,
        session_id=session.session_id,
        name=session.name,
        symbol=session.symbol,
        market=session.market,
        dataset_id=session.dataset_id,
        timeframe=session.timeframe,
        initial_capital=session.initial_capital,
        virtual_balance=session.virtual_balance,
        realized_pnl=session.realized_pnl,
        unrealized_pnl=unrealized,
        total_candles=session.total_candles,
        current_index=session.current_index,
        status=session.status,
        speed_ms=session.speed_ms,
        current_candle=cur_candle,
        current_price=cur_price,
        current_signal=state.get("current_signal"),
        risk_state="NORMAL",
        open_positions=state.get("open_positions", []),
        closed_trades=state.get("closed_trades", []),
        pending_proposal=state.get("pending_proposal"),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.post("/sessions", response_model=ReplaySessionRead, status_code=status.HTTP_201_CREATED, summary="Create Replay Session")
def create_session(
    payload: ReplaySessionCreate,
    db: Session = Depends(get_db),
) -> ReplaySessionRead:
    """Create a new chronological market replay simulation session."""
    session = replay_service.create_session(
        db=db,
        symbol=payload.symbol,
        market=payload.market,
        dataset_id=payload.dataset_id,
        timeframe=payload.timeframe,
        initial_capital=payload.initial_capital,
        name=payload.name,
    )
    return format_session_read(session)


@router.get("/sessions/{session_id}", response_model=ReplaySessionRead, summary="Get Replay Session State")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> ReplaySessionRead:
    """Retrieve current replay simulation state."""
    session = replay_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Replay session {session_id} not found.")
    return format_session_read(session)


@router.post("/{session_id}/step", response_model=ReplaySessionRead, summary="Advance Replay Step (+1 or +N Candles)")
@router.post("/sessions/{session_id}/step", response_model=ReplaySessionRead, summary="Advance Replay Step (+1 or +N Candles) (alias)")
def step_session(
    session_id: str,
    payload: ReplayStepRequest,
    db: Session = Depends(get_db),
) -> ReplaySessionRead:
    """Step forward chronologically by step_count candles."""
    res = replay_service.step(db, session_id, step_count=payload.step_count)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Replay session {session_id} not found.")
    session = replay_service.get_session(db, session_id)
    return format_session_read(session, res)


@router.post("/{session_id}/play", summary="Start Play Mode")
@router.post("/sessions/{session_id}/play", summary="Start Play Mode (alias)")
def play_session(session_id: str, db: Session = Depends(get_db)):
    """Set replay status to PLAYING."""
    session = replay_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    session.status = "PLAYING"
    db.commit()
    return {"status": "PLAYING", "session_id": session_id}


@router.post("/{session_id}/pause", summary="Pause Play Mode")
@router.post("/sessions/{session_id}/pause", summary="Pause Play Mode (alias)")
def pause_session(session_id: str, db: Session = Depends(get_db)):
    """Set replay status to PAUSED."""
    session = replay_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    session.status = "PAUSED"
    db.commit()
    return {"status": "PAUSED", "session_id": session_id}


@router.post("/{session_id}/reset", summary="Reset Replay Session")
@router.post("/sessions/{session_id}/reset", summary="Reset Replay Session (alias)")
def reset_session(session_id: str, db: Session = Depends(get_db)):
    """Reset replay back to the first candle and clean virtual state."""
    res = replay_service.reset_session(db, session_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found.")
    session = replay_service.get_session(db, session_id)
    return format_session_read(session)


@router.post("/{session_id}/approve", summary="Approve Proposal in Replay")
@router.post("/sessions/{session_id}/approve", summary="Approve Proposal in Replay (alias)")
def approve_proposal(
    session_id: str,
    proposal_id: str,
    db: Session = Depends(get_db),
):
    """Approve and execute a trade proposal within the replay sandbox."""
    res = replay_service.approve_proposal(db, session_id, proposal_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal approval failed.")
    return res


@router.post("/{session_id}/close-position", summary="Close Position in Replay")
@router.post("/sessions/{session_id}/close-position", summary="Close Position in Replay (alias)")
def close_position(
    session_id: str,
    position_id: str,
    db: Session = Depends(get_db),
):
    """Manually close an open position within the replay sandbox."""
    res = replay_service.close_position(db, session_id, position_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Position close failed.")
    return res
