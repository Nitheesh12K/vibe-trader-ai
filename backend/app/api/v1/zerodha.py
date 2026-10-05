"""Zerodha Kite Connect REST API endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.zerodha_service import zerodha_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/broker/zerodha", tags=["Broker Integration - Zerodha Kite"])


class ZerodhaCallbackRequest(BaseModel):
    request_token: str = Field(..., min_length=4, description="Request token from Zerodha OAuth redirect")


@router.get("/status", summary="Get Zerodha Connection Status")
def get_zerodha_status():
    """Retrieve connection status, user identity, and security enforcement mode."""
    return zerodha_service.get_status()


@router.get("/login-url", summary="Get Zerodha Kite OAuth Login URL")
def get_zerodha_login_url():
    """Generates the official Zerodha OAuth login link for Kite Connect Personal."""
    return {
        "login_url": zerodha_service.get_login_url(),
        "api_key_configured": bool(zerodha_service.api_key),
    }


@router.post("/callback", summary="Exchange Request Token for Zerodha Session")
def zerodha_callback(payload: ZerodhaCallbackRequest, db: Session = Depends(get_db)):
    """Exchanges request_token from OAuth callback for an active session using server-side secret."""
    return zerodha_service.authenticate_with_request_token(payload.request_token, db=db)


@router.post("/disconnect", summary="Disconnect Zerodha Session")
def disconnect_zerodha(db: Session = Depends(get_db)):
    """Safely terminates active Zerodha session."""
    return zerodha_service.disconnect(db=db)


@router.post("/orders", summary="Attempt Live Broker Order (Fail-Closed)")
def place_live_order_disabled():
    """
    STRICTLY DISABLED / FAIL-CLOSED.
    Enforces that no live orders can be placed through the broker integration.
    """
    return zerodha_service.place_live_order()
