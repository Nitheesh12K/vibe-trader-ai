"""Pydantic schemas for the Interactive AI Market Assistant."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatSourceItem(BaseModel):
    """Retrieved evidence source or tool invocation result."""
    tool_name: str = Field(..., description="Name of the tool/service providing the data")
    symbol: Optional[str] = Field(None, description="Instrument symbol")
    market: Optional[str] = Field(None, description="Market category: NSE, FOREX, MCX")
    timeframe: Optional[str] = Field(None, description="Timeframe of the data: 1m, 5m, 15m, 1h, 1D")
    timestamp: Optional[str] = Field(None, description="Data observation timestamp or freshness date")
    summary: str = Field(..., description="Human-readable citation summary")
    data_points: Dict[str, Any] = Field(default_factory=dict, description="Key retrieved numerical/categorical facts")


class ChatMessageRequest(BaseModel):
    """User message input request for the AI Market Assistant."""
    session_id: str = Field(..., min_length=1, max_length=64, description="Session ID for thread continuity")
    message: str = Field(..., min_length=1, max_length=2000, description="User's natural language market query")
    symbol: Optional[str] = Field(None, description="Currently selected or focused instrument symbol")
    market: Optional[str] = Field(None, description="Market category: NSE, FOREX, MCX")
    timeframe: Optional[str] = Field("1D", description="Active charting timeframe")


class ChatMessageResponse(BaseModel):
    """Assistant message output with grounding citations and safety disclosure."""
    message_id: str
    session_id: str
    role: str = "assistant"
    content: str
    sources: List[ChatSourceItem] = Field(default_factory=list)
    symbol_context: Optional[str] = None
    market_context: Optional[str] = None
    timeframe_context: Optional[str] = None
    model_name: str
    is_fallback: bool = False
    detected_language: str = "english"
    detected_intent: Optional[str] = "GENERAL_CHAT"
    routing_time_ms: Optional[float] = 0.0
    tool_latency_ms: Optional[float] = 0.0
    inference_latency_ms: Optional[float] = 0.0
    total_latency_ms: Optional[float] = 0.0
    disclaimer: str = (
        "AI Market Assistant output is strictly advisory and educational. "
        "It cannot place trades, alter risk limits, or bypass approvals. "
        "Paper trading only."
    )
    created_at: datetime


class ChatHistoryItem(BaseModel):
    """Persisted conversation item."""
    message_id: str
    session_id: str
    role: str
    content: str
    sources: List[ChatSourceItem] = Field(default_factory=list)
    symbol_context: Optional[str] = None
    market_context: Optional[str] = None
    timeframe_context: Optional[str] = None
    model_name: Optional[str] = None
    is_fallback: bool = False
    detected_language: Optional[str] = "english"
    detected_intent: Optional[str] = "GENERAL_CHAT"
    routing_time_ms: Optional[float] = 0.0
    tool_latency_ms: Optional[float] = 0.0
    inference_latency_ms: Optional[float] = 0.0
    total_latency_ms: Optional[float] = 0.0
    created_at: datetime


class AssistantStatusResponse(BaseModel):
    """Operational and connectivity status of the AI Assistant."""
    status: str  # "ONLINE" or "OFFLINE"
    active_model: str
    available_models: List[str]
    host: str
    available_tools: List[str]
    paper_trading_mode: bool = True
    disclaimer: str = "Advisory-only. Zero real order execution."
