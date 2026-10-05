"""Alerts & Notifications API router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.entities import AlertRuleCreate, AlertRuleUpdate, AlertRuleRead, AlertEventRead
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertRuleRead], summary="List Configured Alerts")
@router.get("/rules", response_model=List[AlertRuleRead], summary="List Configured Alerts (alias)")
def get_alert_rules(
    symbol: Optional[str] = Query(None, description="Optional symbol filter"),
    db: Session = Depends(get_db),
) -> List[AlertRuleRead]:
    """Retrieve all configured user and system alert rules."""
    return alert_service.get_rules(db, symbol=symbol)


@router.post("", response_model=AlertRuleRead, status_code=status.HTTP_201_CREATED, summary="Create Alert Rule")
@router.post("/rules", response_model=AlertRuleRead, status_code=status.HTTP_201_CREATED, summary="Create Alert Rule (alias)")
def create_alert_rule(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
) -> AlertRuleRead:
    """Create a new alert rule."""
    return alert_service.create_rule(
        db=db,
        symbol=payload.symbol,
        market=payload.market,
        alert_type=payload.alert_type,
        condition=payload.condition,
        threshold=payload.threshold,
        threshold_str=payload.threshold_str,
        cooldown_seconds=payload.cooldown_seconds,
        notes=payload.notes,
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Alert Rule")
def delete_alert_rule(
    alert_id: str,
    db: Session = Depends(get_db),
):
    """Delete an alert rule by ID or alert_id."""
    success = alert_service.delete_rule(db, alert_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert rule {alert_id} not found.")
    return None


@router.patch("/{alert_id}/toggle", response_model=AlertRuleRead, summary="Toggle Alert Rule Enabled State")
def toggle_alert_rule(
    alert_id: str,
    db: Session = Depends(get_db),
) -> AlertRuleRead:
    """Enable or disable an alert rule."""
    rule = alert_service.get_rules(db)
    target = next((r for r in rule if r.alert_id == alert_id or str(r.id) == alert_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert rule {alert_id} not found.")

    updated = alert_service.update_rule(db, alert_id, is_enabled=not target.is_enabled)
    return updated


@router.get("/events", response_model=List[AlertEventRead], summary="List Alert Notifications")
def get_alert_events(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[AlertEventRead]:
    """Retrieve triggered alert history and in-app notifications."""
    return alert_service.get_events(db, unread_only=unread_only, limit=limit)


@router.post("/events/{event_id}/read", summary="Mark Notification Read")
@router.patch("/events/{event_id}/read", summary="Mark Notification Read (patch alias)")
def mark_event_read(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Mark a notification event as read."""
    success = alert_service.mark_event_read(db, event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    return {"message": "Notification marked as read."}


@router.post("/events/clear", summary="Clear Notification Events")
def clear_events(db: Session = Depends(get_db)):
    """Clear all triggered notification events."""
    cleared = alert_service.clear_all_events(db)
    return {"message": f"Cleared {cleared} notification events."}


@router.post("/check", response_model=List[AlertEventRead], summary="Trigger Alert Condition Evaluation")
def check_alerts(db: Session = Depends(get_db)) -> List[AlertEventRead]:
    """Evaluate all active alert rules against live/demo prices and session states."""
    return alert_service.evaluate_active_rules(db)
