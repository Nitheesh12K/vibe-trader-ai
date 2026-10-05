"""Continuous Market Monitoring API Router for Vibe Trader AI."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.entities import (
    WatchlistInstrument,
    Strategy,
    BuyProposal,
    Position,
    RiskSettings,
)
from app.schemas.workflow import MonitoringStatusResponse
from app.services.monitoring_service import ContinuousMonitoringService

router = APIRouter(prefix="/monitoring", tags=["Continuous Market Monitoring"])


@router.get("/status", response_model=MonitoringStatusResponse, summary="Get Market Monitoring Status")
def get_monitoring_status(db: Session = Depends(get_db)) -> MonitoringStatusResponse:
    risk_settings = db.query(RiskSettings).first()
    pending_count = db.query(BuyProposal).filter(BuyProposal.status == "PENDING").count()
    open_pos_count = db.query(Position).filter(Position.status == "OPEN").count()
    active_strats_count = db.query(Strategy).filter(Strategy.is_active == True).count()
    instruments_count = db.query(WatchlistInstrument).count()

    return MonitoringStatusResponse(
        is_active=ContinuousMonitoringService.is_active(),
        monitored_markets=["FOREX", "NSE", "MCX"],
        total_instruments=instruments_count,
        active_strategies_count=active_strats_count,
        last_scan_timestamp=ContinuousMonitoringService.get_last_scan_timestamp(),
        pending_proposals_count=pending_count,
        open_positions_count=open_pos_count,
        emergency_stop_active=risk_settings.emergency_stop_active if risk_settings else False,
    )


@router.post("/scan", summary="Trigger On-Demand Market Scan")
def trigger_market_scan(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Execute a scan cycle checking prices, expiring proposals, and discovering BUY opportunities."""
    return ContinuousMonitoringService.run_market_scan(db)


@router.post("/toggle", summary="Toggle Monitoring Service")
def toggle_monitoring(
    active: bool = Query(..., description="Set active status"),
    db: Session = Depends(get_db),
):
    ContinuousMonitoringService.set_active(active)
    return {"is_active": ContinuousMonitoringService.is_active()}
