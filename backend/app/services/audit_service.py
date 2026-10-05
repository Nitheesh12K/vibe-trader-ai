"""Audit Logging Service for Vibe Trader AI."""
import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import AuditLog, utcnow

logger = logging.getLogger("vibe-trader-ai.audit")


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        action: str,
        actor: str = "SYSTEM",
        symbol: Optional[str] = None,
        market: Optional[str] = None,
        proposal_id: Optional[str] = None,
        position_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Record an immutable event in the append-only audit trail.
        """
        details_str = json.dumps(details or {})
        log_entry = AuditLog(
            event_type=event_type,
            action=action,
            actor=actor,
            symbol=symbol,
            market=market,
            proposal_id=proposal_id,
            position_id=position_id,
            details_json=details_str,
            timestamp=utcnow(),
        )
        db.add(log_entry)
        try:
            db.commit()
            db.refresh(log_entry)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record audit log: {e}")
        return log_entry
