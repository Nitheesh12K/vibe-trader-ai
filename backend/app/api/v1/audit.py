"""Append-Only Audit Logs API Router for Vibe Trader AI."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import AuditLog
from app.schemas.workflow import AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["Append-Only Audit Trail"])


@router.get("", response_model=List[AuditLogRead], summary="List Audit Log Events")
def list_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[AuditLogRead]:
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if event_type:
        query = query.filter(AuditLog.event_type == event_type.upper())
    if symbol:
        query = query.filter(AuditLog.symbol == symbol)

    logs = query.limit(limit).all()
    results = []
    for log in logs:
        try:
            details_dict = json.loads(log.details_json or "{}")
        except Exception:
            details_dict = {}

        results.append(
            AuditLogRead(
                id=log.id,
                event_type=log.event_type,
                action=log.action,
                actor=log.actor,
                symbol=log.symbol,
                market=log.market,
                proposal_id=log.proposal_id,
                position_id=log.position_id,
                details=details_dict,
                timestamp=log.timestamp,
            )
        )
    return results
