"""Risk Management & Emergency Stop API Router for Vibe Trader AI."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import RiskSettings, utcnow
from app.schemas.workflow import RiskSettingsRead, RiskSettingsUpdate, EmergencyStopToggle
from app.services.risk_service import RiskService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/risk", tags=["Risk Management & Emergency Stop"])


@router.get("/settings", response_model=RiskSettingsRead, summary="Get Risk Settings")
def get_risk_settings(db: Session = Depends(get_db)) -> RiskSettingsRead:
    return RiskService.get_or_create_settings(db)


@router.put("/settings", response_model=RiskSettingsRead, summary="Update Risk Settings")
def update_risk_settings(req: RiskSettingsUpdate, db: Session = Depends(get_db)) -> RiskSettingsRead:
    settings = RiskService.get_or_create_settings(db)
    if req.simulated_balance is not None:
        settings.simulated_balance = req.simulated_balance
    if req.max_risk_per_trade_pct is not None:
        settings.max_risk_per_trade_pct = req.max_risk_per_trade_pct
    if req.max_daily_loss is not None:
        settings.max_daily_loss = req.max_daily_loss
    if req.max_open_positions is not None:
        settings.max_open_positions = req.max_open_positions
    if req.max_position_size_pct is not None:
        settings.max_position_size_pct = req.max_position_size_pct
    if req.emergency_stop_active is not None:
        settings.emergency_stop_active = req.emergency_stop_active

    settings.updated_at = utcnow()
    db.commit()
    db.refresh(settings)

    AuditService.log_event(
        db=db,
        event_type="RISK_SETTINGS_UPDATED",
        action="Updated risk management settings",
        actor="USER",
        details=req.model_dump(exclude_unset=True),
    )
    return settings


@router.post("/emergency-stop", response_model=RiskSettingsRead, summary="Toggle Emergency Stop")
def toggle_emergency_stop(req: EmergencyStopToggle, db: Session = Depends(get_db)) -> RiskSettingsRead:
    """
    Immediate global kill-switch halting all autonomous order submissions and blocking new BUYs.
    """
    settings = RiskService.get_or_create_settings(db)
    settings.emergency_stop_active = req.emergency_stop_active
    settings.updated_at = utcnow()
    db.commit()
    db.refresh(settings)

    action_label = "TRIGGERED EMERGENCY STOP" if req.emergency_stop_active else "CLEARED EMERGENCY STOP"
    AuditService.log_event(
        db=db,
        event_type="EMERGENCY_STOP_TRIGGERED" if req.emergency_stop_active else "EMERGENCY_STOP_CLEARED",
        action=f"User {action_label}: {req.reason}",
        actor="USER",
        details={"active": req.emergency_stop_active, "reason": req.reason},
    )
    return settings


@router.post("/reset-defaults", response_model=RiskSettingsRead, summary="Reset to ₹2,000 Virtual Capital Demo Defaults")
def reset_risk_settings_defaults(db: Session = Depends(get_db)) -> RiskSettingsRead:
    """Resets virtual paper capital to ₹2,000 with 0.5% risk (₹10) and 2% daily loss limit (₹40)."""
    settings = RiskService.get_or_create_settings(db)
    settings.simulated_balance = 2000.0
    settings.max_risk_per_trade_pct = 0.5
    settings.max_daily_loss = 40.0
    settings.max_open_positions = 1
    settings.max_position_size_pct = 50.0
    settings.emergency_stop_active = False
    settings.updated_at = utcnow()
    db.commit()
    db.refresh(settings)

    AuditService.log_event(
        db=db,
        event_type="RISK_SETTINGS_RESET",
        action="Reset virtual paper equity to ₹2,000 simulation defaults",
        actor="USER",
    )
    return settings


@router.get("/portfolio-summary", summary="Get Portfolio Summary")
def get_portfolio_summary(db: Session = Depends(get_db)):
    """Retrieve live portfolio breakdown of balance, cash, equity, and open exposures."""
    from app.services.portfolio_service import PortfolioService
    return PortfolioService.get_portfolio_summary(db=db)


@router.get("/reconcile", summary="Audit and Reconcile Portfolio State")
def reconcile_portfolio(db: Session = Depends(get_db)):
    """
    Runs mathematical reconciliation auditing Cash + Market Value == Equity,
    verifying all positions, orders, and realized P&L records are consistent.
    """
    from app.services.portfolio_service import PortfolioService
    return PortfolioService.reconcile_portfolio(db=db)


