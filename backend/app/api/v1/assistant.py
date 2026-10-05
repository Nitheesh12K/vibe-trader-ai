"""API router for the Interactive AI Market Assistant."""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.chat_assistant import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryItem,
    AssistantStatusResponse,
)
from app.services.market_assistant_service import MarketAssistantService

logger = logging.getLogger("vibe-trader-ai.assistant_router")

router = APIRouter(prefix="/assistant", tags=["Interactive AI Market Assistant"])


@router.get("/status", response_model=AssistantStatusResponse, summary="Get Assistant Status & Model Info")
def get_assistant_status() -> AssistantStatusResponse:
    """Check connectivity to the local Ollama LLM and list available tools."""
    return MarketAssistantService.get_status()


@router.post("/chat", response_model=ChatMessageResponse, summary="Send User Market Query to AI Assistant")
def chat_with_assistant(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
) -> ChatMessageResponse:
    """
    Submits a user query to the AI Market Assistant.
    Retrieves grounded market data and indicators, invokes local Qwen (or deterministic fallback),
    and logs citations and conversation history.
    """
    try:
        response = MarketAssistantService.process_chat_message(
            db=db,
            session_id=payload.session_id,
            user_message=payload.message,
            symbol=payload.symbol,
            market=payload.market,
            timeframe=payload.timeframe or "1D",
        )
        return response
    except Exception as e:
        logger.error(f"Error handling assistant chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate a response. Please retry; check the backend logs if this continues.",
        )


@router.get("/history/{session_id}", response_model=List[ChatHistoryItem], summary="Get Chat History for Session")
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
) -> List[ChatHistoryItem]:
    """Retrieve full chronological conversation history for the given session ID."""
    return MarketAssistantService.get_history(db=db, session_id=session_id)


@router.delete("/history/{session_id}", summary="Clear Session Chat History")
def clear_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Wipes conversation history for the given session ID."""
    deleted_count = MarketAssistantService.clear_history(db=db, session_id=session_id)
    return {
        "status": "CLEARED",
        "session_id": session_id,
        "deleted_count": deleted_count,
    }
