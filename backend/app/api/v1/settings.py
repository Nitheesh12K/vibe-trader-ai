"""User Settings & Central Settings Center API endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import (
    UserSettings,
    RiskSettings,
    AutonomousExitPermission,
    AuditLog,
    utcnow,
)
from app.schemas.entities import (
    UserSettingsRead,
    UserSettingsUpdate,
    SettingsAllRead,
    SettingsAllUpdate,
)
from app.services.ai_provider import ai_provider
from app.services.zerodha_service import zerodha_service

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=UserSettingsRead, summary="Get User Settings")
def get_user_settings(db: Session = Depends(get_db)) -> UserSettingsRead:
    """Retrieve user preferences and trading settings. Creates defaults if not found."""
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings(
            theme="dark",
            default_market="ALL",
            default_timeframe="1D",
            risk_percentage=1.0,
            notifications_enabled=True,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("", response_model=UserSettingsRead, summary="Update User Settings")
def update_user_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
) -> UserSettingsRead:
    """Update user preferences."""
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(settings, field, val)

    settings.updated_at = utcnow()
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/all", response_model=SettingsAllRead, summary="Get Consolidated Settings")
def get_all_settings(db: Session = Depends(get_db)) -> SettingsAllRead:
    """Retrieve unified system settings: User, Risk, Auto-Exit, AI, and Broker."""
    u_set = db.query(UserSettings).first()
    if not u_set:
        u_set = UserSettings()
        db.add(u_set)
        db.commit()
        db.refresh(u_set)

    r_set = db.query(RiskSettings).first()
    if not r_set:
        r_set = RiskSettings()
        db.add(r_set)
        db.commit()
        db.refresh(r_set)

    a_perm = db.query(AutonomousExitPermission).first()
    if not a_perm:
        a_perm = AutonomousExitPermission()
        db.add(a_perm)
        db.commit()
        db.refresh(a_perm)

    ai_stat = ai_provider.get_status()
    b_stat = zerodha_service.get_connection_status()

    return SettingsAllRead(
        user_settings={
            "id": u_set.id,
            "theme": u_set.theme,
            "default_market": u_set.default_market,
            "default_timeframe": u_set.default_timeframe,
            "risk_percentage": u_set.risk_percentage,
            "notifications_enabled": u_set.notifications_enabled,
        },
        risk_settings={
            "id": r_set.id,
            "simulated_balance": r_set.simulated_balance,
            "max_risk_per_trade_pct": r_set.max_risk_per_trade_pct,
            "max_daily_loss": r_set.max_daily_loss,
            "max_open_positions": r_set.max_open_positions,
            "max_position_size_pct": r_set.max_position_size_pct,
            "emergency_stop_active": r_set.emergency_stop_active,
        },
        autonomous_exit={
            "id": a_perm.id,
            "is_enabled": a_perm.is_enabled,
            "allow_stop_loss": a_perm.allow_stop_loss,
            "allow_take_profit": a_perm.allow_take_profit,
            "allow_strategy_exit": a_perm.allow_strategy_exit,
            "allow_max_drawdown": a_perm.allow_max_drawdown,
        },
        ai_status=ai_stat,
        broker_status=b_stat,
    )


@router.put("/all", response_model=SettingsAllRead, summary="Update Consolidated Settings")
def update_all_settings(
    payload: SettingsAllUpdate,
    db: Session = Depends(get_db),
) -> SettingsAllRead:
    """Update unified system settings with server-side validation and audit log generation."""
    u_set = db.query(UserSettings).first()
    r_set = db.query(RiskSettings).first()
    a_perm = db.query(AutonomousExitPermission).first()

    changed_fields = []

    # 1. User preferences
    if payload.theme is not None:
        u_set.theme = payload.theme
        changed_fields.append(f"theme={payload.theme}")
    if payload.default_market is not None:
        u_set.default_market = payload.default_market
        changed_fields.append(f"default_market={payload.default_market}")
    if payload.default_timeframe is not None:
        u_set.default_timeframe = payload.default_timeframe
        changed_fields.append(f"default_timeframe={payload.default_timeframe}")
    if payload.risk_percentage is not None:
        u_set.risk_percentage = payload.risk_percentage
        changed_fields.append(f"risk_percentage={payload.risk_percentage}")
    if payload.notifications_enabled is not None:
        u_set.notifications_enabled = payload.notifications_enabled
        changed_fields.append(f"notifications_enabled={payload.notifications_enabled}")

    # 2. Risk boundaries
    if payload.max_risk_per_trade_pct is not None:
        if payload.max_risk_per_trade_pct <= 0 or payload.max_risk_per_trade_pct > 10:
            raise HTTPException(status_code=400, detail="Max risk per trade must be between 0.1% and 10%.")
        r_set.max_risk_per_trade_pct = payload.max_risk_per_trade_pct
        changed_fields.append(f"max_risk_per_trade_pct={payload.max_risk_per_trade_pct}")

    if payload.max_daily_loss is not None:
        if payload.max_daily_loss <= 0:
            raise HTTPException(status_code=400, detail="Max daily loss must be positive.")
        r_set.max_daily_loss = payload.max_daily_loss
        changed_fields.append(f"max_daily_loss={payload.max_daily_loss}")

    if payload.max_open_positions is not None:
        if payload.max_open_positions < 1 or payload.max_open_positions > 50:
            raise HTTPException(status_code=400, detail="Max open positions must be between 1 and 50.")
        r_set.max_open_positions = payload.max_open_positions
        changed_fields.append(f"max_open_positions={payload.max_open_positions}")

    if payload.emergency_stop_active is not None:
        r_set.emergency_stop_active = payload.emergency_stop_active
        changed_fields.append(f"emergency_stop_active={payload.emergency_stop_active}")

    # 3. Autonomous exit permissions
    if payload.allow_stop_loss is not None:
        a_perm.allow_stop_loss = payload.allow_stop_loss
        changed_fields.append(f"allow_stop_loss={payload.allow_stop_loss}")
    if payload.allow_take_profit is not None:
        a_perm.allow_take_profit = payload.allow_take_profit
        changed_fields.append(f"allow_take_profit={payload.allow_take_profit}")
    if payload.allow_strategy_exit is not None:
        a_perm.allow_strategy_exit = payload.allow_strategy_exit
        changed_fields.append(f"allow_strategy_exit={payload.allow_strategy_exit}")
    if payload.allow_max_drawdown is not None:
        a_perm.allow_max_drawdown = payload.allow_max_drawdown
        changed_fields.append(f"allow_max_drawdown={payload.allow_max_drawdown}")

    # Log audit event for settings modification
    if changed_fields:
        audit = AuditLog(
            event_type="CONFIG_CHANGE",
            action="SETTINGS_UPDATED",
            actor="USER",
            details_json=json.dumps({"modified_fields": changed_fields}),
            timestamp=utcnow(),
        )
        db.add(audit)

    db.commit()
    db.refresh(u_set)
    db.refresh(r_set)
    db.refresh(a_perm)

    return get_all_settings(db)
