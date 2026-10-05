"""Autonomous Exit Permissions API Router for Vibe Trader AI."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import AutonomousExitPermission, utcnow
from app.schemas.workflow import AutonomousExitPermissionRead, AutonomousExitPermissionUpdate
from app.services.position_monitor import PositionMonitorService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/autonomous-exit", tags=["Autonomous Exit Permissions"])


@router.get("/permissions", response_model=AutonomousExitPermissionRead, summary="Get Autonomous Exit Permissions")
def get_permissions(db: Session = Depends(get_db)) -> AutonomousExitPermissionRead:
    return PositionMonitorService.get_or_create_permissions(db)


@router.put("/permissions", response_model=AutonomousExitPermissionRead, summary="Update Autonomous Exit Permissions")
def update_permissions(
    req: AutonomousExitPermissionUpdate,
    db: Session = Depends(get_db),
) -> AutonomousExitPermissionRead:
    perm = PositionMonitorService.get_or_create_permissions(db)
    if req.is_enabled is not None:
        perm.is_enabled = req.is_enabled
    if req.allow_stop_loss is not None:
        perm.allow_stop_loss = req.allow_stop_loss
    if req.allow_take_profit is not None:
        perm.allow_take_profit = req.allow_take_profit
    if req.allow_strategy_exit is not None:
        perm.allow_strategy_exit = req.allow_strategy_exit
    if req.allow_max_drawdown is not None:
        perm.allow_max_drawdown = req.allow_max_drawdown
    if req.max_position_scope is not None:
        perm.max_position_scope = req.max_position_scope
    if req.emergency_risk_limit_pct is not None:
        perm.emergency_risk_limit_pct = req.emergency_risk_limit_pct

    perm.updated_at = utcnow()
    db.commit()
    db.refresh(perm)

    AuditService.log_event(
        db=db,
        event_type="AUTONOMOUS_EXIT_SETTINGS_UPDATED",
        action="Updated autonomous exit permissions",
        actor="USER",
        details=req.model_dump(exclude_unset=True),
    )
    return perm
