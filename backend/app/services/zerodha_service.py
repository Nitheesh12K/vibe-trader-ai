"""Zerodha Kite Connect Personal (Free) Integration.
Provides authentication and account verification with fail-closed live execution controls.
"""
import os
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from fastapi import HTTPException, status
from app.models.entities import utcnow
from app.services.audit_service import AuditService

logger = logging.getLogger("vibe-trader-ai.zerodha")


class ZerodhaBrokerService:
    """Manages secure Zerodha Kite Connect Personal authentication and safe account query."""

    def __init__(self):
        self.api_key = os.getenv("ZERODHA_API_KEY", "")
        self.api_secret = os.getenv("ZERODHA_API_SECRET", "")
        self.access_token: Optional[str] = None
        self.user_profile: Optional[Dict[str, Any]] = None
        self.connected_at: Optional[datetime] = None

    def get_masked_key(self) -> str:
        if not self.api_key or len(self.api_key) < 6:
            return "NOT_CONFIGURED"
        return f"{self.api_key[:3]}****{self.api_key[-3:]}"

    def get_login_url(self) -> str:
        if not self.api_key:
            return "https://kite.zerodha.com/connect/login?v=3&api_key=YOUR_API_KEY"
        return f"https://kite.zerodha.com/connect/login?v=3&api_key={self.api_key}"

    def get_status(self) -> Dict[str, Any]:
        """Returns connection status without revealing secrets or private tokens."""
        is_conn = bool(self.access_token and self.user_profile)
        return {
            "broker_name": "Zerodha Kite Connect Personal (Free)",
            "is_connected": is_conn,
            "api_key_configured": bool(self.api_key),
            "api_key_masked": self.get_masked_key(),
            "user_id": self.user_profile.get("user_id") if self.user_profile else None,
            "user_name": self.user_profile.get("user_name") if self.user_profile else None,
            "user_type": self.user_profile.get("user_type") if self.user_profile else None,
            "email": self.user_profile.get("email") if self.user_profile else None,
            "broker": "ZERODHA",
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "live_execution_mode": "STRICTLY_DISABLED (FAIL_CLOSED)",
            "disclaimer": (
                "Zerodha Kite Connect Personal (Free) is integrated for read-only authentication and account identity only. "
                "Live broker order execution is strictly disabled. All orders operate in local paper-trading simulation."
            ),
        }

    def get_connection_status(self) -> Dict[str, Any]:
        """Alias for get_status."""
        return self.get_status()

    def authenticate_with_request_token(self, request_token: str, db=None) -> Dict[str, Any]:
        """
        Exchanges request_token from OAuth callback for an access_token using SHA-256 checksum.
        API secret is kept strictly server-side.
        """
        if not self.api_key or not self.api_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zerodha API Key or API Secret not configured in server environment (.env).",
            )

        # Checksum = SHA256(api_key + request_token + api_secret)
        raw_str = f"{self.api_key}{request_token}{self.api_secret}"
        checksum = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    "https://api.kite.trade/session/token",
                    data={
                        "api_key": self.api_key,
                        "request_token": request_token,
                        "checksum": checksum,
                    },
                )
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    self.access_token = data.get("access_token")
                    self.user_profile = {
                        "user_id": data.get("user_id"),
                        "user_name": data.get("user_name"),
                        "user_type": data.get("user_type"),
                        "email": data.get("email"),
                    }
                    self.connected_at = utcnow()

                    if db:
                        AuditService.log_event(
                            db=db,
                            event_type="ZERODHA_CONNECTED",
                            action=f"Zerodha account {self.user_profile.get('user_id')} connected successfully",
                            actor="USER",
                        )

                    return self.get_status()
                else:
                    error_msg = res.json().get("message", "Token exchange failed.")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Zerodha authentication error: {error_msg}",
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Zerodha authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to communicate with Zerodha Kite servers: {str(e)}",
            )

    def disconnect(self, db=None) -> Dict[str, Any]:
        """Clears active session credentials."""
        user_id = self.user_profile.get("user_id") if self.user_profile else "UNKNOWN"
        self.access_token = None
        self.user_profile = None
        self.connected_at = None

        if db:
            AuditService.log_event(
                db=db,
                event_type="ZERODHA_DISCONNECTED",
                action=f"Zerodha session disconnected for user {user_id}",
                actor="USER",
            )

        return self.get_status()

    def place_live_order(self, *args, **kwargs):
        """
        STRICTLY DISABLED / FAIL-CLOSED.
        Under no circumstances allows live broker order placement in this release.
        """
        logger.critical("ATTEMPTED LIVE BROKER ORDER EXECUTION — REJECTED UNDER FAIL-CLOSED SECURITY POLICY.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "SECURITY LOCK: Live broker order execution is strictly disabled. "
                "Vibe Trader AI operates exclusively in simulated paper-trading mode. "
                "Broker connection is limited to read-only account verification."
            ),
        )


zerodha_service = ZerodhaBrokerService()
