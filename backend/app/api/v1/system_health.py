"""System Health Center API router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.entities import SystemHealthResponse
from app.services.health_service import health_service

router = APIRouter(prefix="/system", tags=["System Health"])


@router.get("/health", response_model=SystemHealthResponse, summary="Get Full System Subsystems Health Diagnostics")
def get_system_health(db: Session = Depends(get_db)) -> SystemHealthResponse:
    """
    Check real-time health across all platform subsystems:
    FastAPI backend, SQLite DB, AI/Ollama, Market data, CSV storage, Paper broker, Audit, and Zerodha.
    """
    res = health_service.check_all_subsystems(db)
    return SystemHealthResponse(**res)
