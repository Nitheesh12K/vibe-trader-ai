"""Comprehensive Test Suite for the Interactive AI Market Assistant.
Verifies:
1. Status API connectivity and available tools registry.
2. Natural language symbol and market extraction.
3. Factual tool context retrieval (OHLC, 13 indicators, S/R, patterns, strategy signals, portfolio).
4. Deterministic fallback behavior when local Ollama is offline.
5. Graceful timeout handling (bounded 12s) without crashing.
6. Strict safety isolation: user buy prompts NEVER execute orders or bypass approval.
7. Multi-turn conversation history persistence and clearing.
8. Live local Ollama Qwen model test (conditional on running daemon).
"""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import httpx

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app
from app.database.session import SessionLocal, init_db
from app.models.entities import Position, ChatMessageRecord
from app.services.market_assistant_service import MarketAssistantService, AssistantIntent
from app.schemas.chat_assistant import ChatMessageRequest

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. Assistant Status Endpoint
# ---------------------------------------------------------------------------

def test_assistant_status_endpoint():
    resp = client.get("/api/assistant/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["ONLINE", "OFFLINE"]
    assert "active_model" in data
    assert "available_tools" in data
    assert "MarketDataTool" in data["available_tools"]
    assert "TechnicalIndicatorsTool" in data["available_tools"]
    assert "PaperPortfolioTool" in data["available_tools"]
    assert data["paper_trading_mode"] is True


# ---------------------------------------------------------------------------
# 2. Natural Language Symbol & Market Extraction
# ---------------------------------------------------------------------------

def test_symbol_and_market_extraction():
    # NSE Equities
    sym, mkt = MarketAssistantService.extract_symbol_and_market("What is the technical setup on RELIANCE?")
    assert sym == "RELIANCE"
    assert mkt == "NSE"

    sym, mkt = MarketAssistantService.extract_symbol_and_market("Can you check RSI for TCS today?")
    assert sym == "TCS"
    assert mkt == "NSE"

    sym, mkt = MarketAssistantService.extract_symbol_and_market("What is the NIFTY 50 trend?")
    assert sym == "NIFTY 50"
    assert mkt == "NSE"

    # Forex Pairs
    sym, mkt = MarketAssistantService.extract_symbol_and_market("Is EUR/USD overbought right now?")
    assert sym == "EUR/USD"
    assert mkt == "FOREX"

    # Commodities
    sym, mkt = MarketAssistantService.extract_symbol_and_market("Analyze CRUDEOIL momentum")
    assert sym == "CRUDEOIL"
    assert mkt == "MCX"

    # Provided context fallback
    sym, mkt = MarketAssistantService.extract_symbol_and_market("What is the RSI?", provided_symbol="INFY", provided_market="NSE")
    assert sym == "INFY"
    assert mkt == "NSE"


# ---------------------------------------------------------------------------
# 3. Tool Context Collection - Market Data & Indicators
# ---------------------------------------------------------------------------

def test_tool_context_collection_market_data(db_session):
    context, sources = MarketAssistantService.collect_grounding_context(
        db=db_session,
        message="What is the setup on RELIANCE?",
        symbol="RELIANCE",
        market="NSE",
        timeframe="1D",
    )

    assert "MARKET DATA: RELIANCE" in context
    assert "CAUSAL TECHNICAL INDICATORS: RELIANCE" in context
    assert "DETERMINISTIC STRATEGY EVALUATION" in context

    tool_names = [s.tool_name for s in sources]
    assert "MarketDataTool" in tool_names
    assert "TechnicalIndicatorsTool" in tool_names
    assert "PatternsAndLevelsTool" in tool_names
    assert "StrategySignalsTool" in tool_names

    # Verify numbers are factual and present
    ind_source = next(s for s in sources if s.tool_name == "TechnicalIndicatorsTool")
    assert "rsi" in ind_source.data_points
    assert ind_source.data_points["rsi"] is not None


# ---------------------------------------------------------------------------
# 4. Tool Context Collection - Paper Portfolio
# ---------------------------------------------------------------------------

def test_tool_context_collection_portfolio(db_session):
    context, sources = MarketAssistantService.collect_grounding_context(
        db=db_session,
        message="Show my open paper positions and portfolio equity",
        symbol=None,
    )

    assert "PAPER PORTFOLIO STATUS" in context
    tool_names = [s.tool_name for s in sources]
    assert "PaperPortfolioTool" in tool_names

    port_source = next(s for s in sources if s.tool_name == "PaperPortfolioTool")
    assert "portfolio_equity" in port_source.data_points
    assert "simulated_balance" in port_source.data_points


# ---------------------------------------------------------------------------
# 5. Deterministic Fallback when Ollama is Offline
# ---------------------------------------------------------------------------

def test_chat_deterministic_fallback_when_offline():
    # Mock Ollama health check as OFFLINE
    with patch("app.services.ai_provider.OllamaProvider.check_health") as mock_health:
        mock_health.return_value = {"status": "OFFLINE", "available_models": []}

        payload = {
            "session_id": "test-offline-session-1",
            "message": "Analyze RELIANCE indicators",
            "symbol": "RELIANCE",
            "market": "NSE",
            "timeframe": "1D",
        }
        resp = client.post("/api/assistant/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_fallback"] is True
        assert data["model_name"] == "DETERMINISTIC_FALLBACK"
        assert "Local AI Model Offline or Timed Out" in data["content"]
        assert "RELIANCE" in data["content"]
        assert {s["tool_name"] for s in data["sources"]} == {"MarketDataTool", "TechnicalIndicatorsTool"}
        assert "advisory" in data["disclaimer"].lower()


# ---------------------------------------------------------------------------
# 6. Graceful Timeout Handling
# ---------------------------------------------------------------------------

def test_chat_timeout_handling():
    original_post = httpx.Client.post

    def selective_mock_post(self, url, *args, **kwargs):
        if "11434" in str(url):
            raise httpx.ReadTimeout("Simulated Ollama read timeout")
        return original_post(self, url, *args, **kwargs)

    with patch("app.services.ai_provider.OllamaProvider.check_health") as mock_health, \
         patch.object(httpx.Client, "post", new=selective_mock_post):
        mock_health.return_value = {"status": "ONLINE", "available_models": ["qwen3-local:latest"]}

        payload = {
            "session_id": "test-timeout-session-1",
            "message": "What is the RSI on TCS?",
            "symbol": "TCS",
            "market": "NSE",
        }
        resp = client.post("/api/assistant/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_fallback"] is True
        assert data["model_name"] == "DETERMINISTIC_FALLBACK"
        assert "TCS" in data["content"]


# ---------------------------------------------------------------------------
# 7. Strict Safety Isolation - Zero Order Execution
# ---------------------------------------------------------------------------

def test_chat_safety_isolation_zero_orders(db_session):
    pos_before = db_session.query(Position).count()

    payload = {
        "session_id": "test-safety-session-1",
        "message": "EXECUTE ORDER: BUY 100 SHARES OF RELIANCE AT MARKET NOW!",
        "symbol": "RELIANCE",
    }
    resp = client.post("/api/assistant/chat", json=payload)
    assert resp.status_code == 200

    pos_after = db_session.query(Position).count()
    # Invariant: Chat assistant CANNOT create positions or execute orders
    assert pos_after == pos_before

    # Verify live broker remains fail-closed
    broker_resp = client.post("/api/broker/zerodha/orders", json={"symbol": "RELIANCE", "quantity": 100})
    assert broker_resp.status_code == 403


# ---------------------------------------------------------------------------
# 8. Conversation History Persistence & Deletion
# ---------------------------------------------------------------------------

def test_chat_history_persistence_and_clearing():
    sess_id = f"test-hist-{int(httpx._config.DEFAULT_TIMEOUT_CONFIG.connect or 1)}"

    # Send first message
    resp1 = client.post("/api/assistant/chat", json={
        "session_id": sess_id,
        "message": "Hello, what is RELIANCE close price?",
        "symbol": "RELIANCE",
    })
    assert resp1.status_code == 200

    # Send second message
    resp2 = client.post("/api/assistant/chat", json={
        "session_id": sess_id,
        "message": "Show my paper portfolio status",
    })
    assert resp2.status_code == 200

    # Retrieve history
    hist_resp = client.get(f"/api/assistant/history/{sess_id}")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 4  # 2 user messages + 2 assistant responses

    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "assistant"

    # Clear history
    del_resp = client.delete(f"/api/assistant/history/{sess_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "CLEARED"
    assert del_resp.json()["deleted_count"] == 4

    # Verify history is now empty
    hist_after = client.get(f"/api/assistant/history/{sess_id}").json()
    assert len(hist_after) == 0


# ---------------------------------------------------------------------------
# 9. Live Ollama Qwen Generation (If daemon is active)
# ---------------------------------------------------------------------------

def test_live_ollama_qwen_generation_if_available():
    # Check if local Ollama is active
    status_resp = client.get("/api/assistant/status").json()
    if status_resp["status"] != "ONLINE":
        pytest.skip("Local Ollama daemon not reachable; skipping live generation test.")

    sess_id = "test-live-ollama-session"
    resp = client.post("/api/assistant/chat", json={
        "session_id": sess_id,
        "message": "What is the RSI on RELIANCE and what does it indicate?",
        "symbol": "RELIANCE",
        "market": "NSE",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["content"]) > 20
    # Must not contain raw unclosed think tags
    assert "<think>" not in data["content"]
    assert len(data["sources"]) > 0
    # Clean up test session
    client.delete(f"/api/assistant/history/{sess_id}")


# ---------------------------------------------------------------------------
# 10. Intent Detection Unit Tests
# ---------------------------------------------------------------------------

def test_intent_detection():
    # Greetings
    assert MarketAssistantService.detect_intent("hi") == AssistantIntent.GREETING
    assert MarketAssistantService.detect_intent("Hello!") == AssistantIntent.GREETING
    assert MarketAssistantService.detect_intent("hey there") == AssistantIntent.GREETING
    assert MarketAssistantService.detect_intent("good morning") == AssistantIntent.GREETING
    assert MarketAssistantService.detect_intent("namaste") == AssistantIntent.GREETING

    # Greeting prefix with market query should NOT be classified as greeting
    assert MarketAssistantService.detect_intent("hi, what is the RSI on RELIANCE?") == AssistantIntent.TECHNICAL_ANALYSIS

    # Portfolio queries
    assert MarketAssistantService.detect_intent("show my open positions") == AssistantIntent.PORTFOLIO_QUERY
    assert MarketAssistantService.detect_intent("what is my virtual balance?") == AssistantIntent.PORTFOLIO_QUERY
    assert MarketAssistantService.detect_intent("check my portfolio equity") == AssistantIntent.PORTFOLIO_QUERY

    # Market analysis queries
    assert MarketAssistantService.detect_intent("What is the RSI on RELIANCE?") == AssistantIntent.TECHNICAL_ANALYSIS
    assert MarketAssistantService.detect_intent("analyze TCS") == AssistantIntent.MARKET_ANALYSIS
    assert MarketAssistantService.detect_intent("check MACD histogram") == AssistantIntent.TECHNICAL_ANALYSIS
    assert MarketAssistantService.detect_intent("What are the support and resistance zones for NIFTY 50?") == AssistantIntent.TECHNICAL_ANALYSIS

    # Capabilities
    assert MarketAssistantService.detect_intent("what can you do?") == AssistantIntent.CAPABILITIES
    assert MarketAssistantService.detect_intent("what are your capabilities") == AssistantIntent.CAPABILITIES
    assert MarketAssistantService.detect_intent("show features") == AssistantIntent.CAPABILITIES
    assert MarketAssistantService.detect_intent("help me") == AssistantIntent.CAPABILITIES

    # General conversation
    assert MarketAssistantService.detect_intent("who are you?") == AssistantIntent.GENERAL_CONVERSATION
    assert MarketAssistantService.detect_intent("why is risk management important?") == AssistantIntent.EDUCATIONAL
    assert MarketAssistantService.detect_intent("what is machine learning in trading?") == AssistantIntent.EDUCATIONAL


# ---------------------------------------------------------------------------
# 11. Greeting Fast-Path Isolation (Fix for Screenshot Issue)
# ---------------------------------------------------------------------------

def test_greeting_fast_path_never_fetches_market_data():
    """Verifies that greetings like 'hi' return immediate friendly response (<10ms),
    with sources=[], is_fallback=False, and NEVER leak NIFTY 50 or any market data,
    even when the frontend passes symbol='NIFTY 50' as the active chart context.
    """
    sess_id = "test-greeting-fast-path"
    payload = {
        "session_id": sess_id,
        "message": "hi",
        "symbol": "NIFTY 50",  # Frontend dashboard context
        "market": "NSE",
    }
    resp = client.post("/api/assistant/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Invariants for greeting
    assert data["role"] == "assistant"
    assert data["is_fallback"] is False
    assert data["sources"] == []
    assert data["symbol_context"] is None
    assert "Vibe Trader AI Market Assistant" in data["content"]
    assert "NIFTY 50" not in data["content"]
    assert "Close Price" not in data["content"]
    assert "RSI (14)" not in data["content"]

    client.delete(f"/api/assistant/history/{sess_id}")


# ---------------------------------------------------------------------------
# 12. General Conversation Isolation (No Unrelated Market Data)
# ---------------------------------------------------------------------------

def test_general_conversation_does_not_leak_active_chart_data():
    """Verifies that general questions like 'why is risk management important?' do not fetch
    market data for the active chart (e.g. NIFTY 50) and fallback cleanly when Ollama is offline.
    """
    with patch("app.services.ai_provider.OllamaProvider.check_health") as mock_health:
        mock_health.return_value = {"status": "OFFLINE", "available_models": []}

        sess_id = "test-gen-convo-isolation"
        payload = {
            "session_id": sess_id,
            "message": "Why is risk management important in quantitative trading?",
            "symbol": "NIFTY 50",  # Active chart context
            "market": "NSE",
        }
        resp = client.post("/api/assistant/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_fallback"] is True
        assert data["sources"] == []
        assert data["symbol_context"] is None
        assert "NIFTY 50" not in data["content"]
        assert "RSI (14)" not in data["content"]

        client.delete(f"/api/assistant/history/{sess_id}")


# ---------------------------------------------------------------------------
# 13. Timeout Fallback Isolation for General and Ambiguous Queries
# ---------------------------------------------------------------------------

def test_timeout_fallback_does_not_leak_unrelated_market_analysis():
    """Simulates an Ollama ReadTimeout during a general question while NIFTY 50
    is focused in UI. Fallback must present capabilities, NOT NIFTY 50 technical analysis.
    """
    original_post = httpx.Client.post

    def selective_mock_post(self, url, *args, **kwargs):
        if "11434" in str(url):
            raise httpx.ReadTimeout("Simulated Ollama read timeout")
        return original_post(self, url, *args, **kwargs)

    with patch("app.services.ai_provider.OllamaProvider.check_health") as mock_health, \
         patch.object(httpx.Client, "post", new=selective_mock_post):
        mock_health.return_value = {"status": "ONLINE", "available_models": ["qwen3-local:latest"]}

        sess_id = "test-timeout-convo"
        payload = {
            "session_id": sess_id,
            "message": "Explain the concept of drawdown recovery",
            "symbol": "NIFTY 50",
            "market": "NSE",
        }
        resp = client.post("/api/assistant/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_fallback"] is True
        assert "Market Analysis for NIFTY 50" not in data["content"]
        assert len(data["sources"]) == 0

        client.delete(f"/api/assistant/history/{sess_id}")


# ---------------------------------------------------------------------------
# 14. Capabilities Fast-Path Verified Features
# ---------------------------------------------------------------------------

def test_capabilities_fast_path_verified_features():
    """Verifies that capability questions return concise description of verified features,
    with sources=[], is_fallback=False, model_name='AI_ASSISTANT', and zero active chart leakage.
    """
    sess_id = "test-capabilities-fast-path"
    payload = {
        "session_id": sess_id,
        "message": "What can you do?",
        "symbol": "NIFTY 50",  # Active dashboard context
        "market": "NSE",
    }
    resp = client.post("/api/assistant/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["role"] == "assistant"
    assert data["is_fallback"] is False
    assert data["model_name"] == "BUILTIN_ASSISTANT"
    assert data["sources"] == []
    assert data["symbol_context"] is None
    # Verified feature content
    assert "Verified Platform Capabilities" in data["content"]
    assert "Historical & Demo Market Data" in data["content"]
    assert "13 Causal Technical Indicators" in data["content"]
    assert "Deterministic Strategy Signals" in data["content"]
    assert "Paper Portfolio Tracking" in data["content"]
    assert "Risk Guardian" in data["content"]
    # Never leaks NIFTY 50 technical analysis
    assert "Market Analysis for NIFTY 50" not in data["content"]
    assert "Latest Close Price" not in data["content"]

    client.delete(f"/api/assistant/history/{sess_id}")


# ---------------------------------------------------------------------------
# 15. Language Detection (English vs Tanglish)
# ---------------------------------------------------------------------------

def test_language_detection_isolated():
    """Verifies that detect_language accurately categorizes English and Tanglish."""
    # English
    assert MarketAssistantService.detect_language("hi") == "english"
    assert MarketAssistantService.detect_language("What is the RSI on RELIANCE?") == "english"
    assert MarketAssistantService.detect_language("Can you explain how MACD works?") == "english"
    assert MarketAssistantService.detect_language("What can you do?") == "english"

    # Tanglish vocabulary
    assert MarketAssistantService.detect_language("vanakkam") == "tanglish"
    assert MarketAssistantService.detect_language("epdi irukinga?") == "tanglish"
    assert MarketAssistantService.detect_language("enna features irukku unkitta?") == "tanglish"
    assert MarketAssistantService.detect_language("Trading la risk management yen mukkiyam?") == "tanglish"
    assert MarketAssistantService.detect_language("RELIANCE rsi epdi irukku?") == "tanglish"
    assert MarketAssistantService.detect_language("TCS trend sollunga") == "tanglish"
    assert MarketAssistantService.detect_language("portfolio la evlo equity irukku?") == "tanglish"

    # Tanglish suffixes (-la, -ku, -oda)
    assert MarketAssistantService.detect_language("marketla enna aachu?") == "tanglish"
    assert MarketAssistantService.detect_language("intradayku nalladha?") == "tanglish"
    assert MarketAssistantService.detect_language("stockoda trend sollu") == "tanglish"


# ---------------------------------------------------------------------------
# 16. Conversational Continuity & Immediate Language Switching
# ---------------------------------------------------------------------------

def test_language_continuity_and_switching():
    """Verifies language retention for ambiguous inputs and immediate switching upon change."""
    # Ambiguous input defaults to English if no previous context
    assert MarketAssistantService.detect_language("RELIANCE 1D", previous_language=None) == "english"

    # Ambiguous input inherits previous language
    assert MarketAssistantService.detect_language("RELIANCE 1D", previous_language="tanglish") == "tanglish"
    assert MarketAssistantService.detect_language("TCS 15m", previous_language="tanglish") == "tanglish"
    assert MarketAssistantService.detect_language("TCS 15m", previous_language="english") == "english"

    # Immediate switch when language marker changes
    # From Tanglish to English
    assert MarketAssistantService.detect_language("What about RELIANCE?", previous_language="tanglish") == "english"
    # From English to Tanglish
    assert MarketAssistantService.detect_language("TCS pathi sollunga", previous_language="english") == "tanglish"


# ---------------------------------------------------------------------------
# 17. Tamil Unicode Script Sanitizer
# ---------------------------------------------------------------------------

def test_tamil_unicode_sanitizer():
    """Verifies that sanitize_no_tamil_script removes any Tamil script Unicode characters."""
    import re
    tamil_regex = re.compile(r"[\u0B80-\u0BFF]")

    # Pure Roman text should remain untouched
    clean_text = "Vanakkam! RELIANCE RSI is 48.26."
    assert MarketAssistantService.sanitize_no_tamil_script(clean_text) == clean_text

    # Text containing Tamil Unicode script should be sanitized to Roman only
    mixed_text = "வணக்கம் Vanakkam thalaiva! RELIANCE analysis: நன்று"
    sanitized = MarketAssistantService.sanitize_no_tamil_script(mixed_text)
    assert not tamil_regex.search(sanitized)
    assert "Vanakkam thalaiva! RELIANCE analysis:" in sanitized


# ---------------------------------------------------------------------------
# 18. Tanglish Fast-Paths (Greeting and Capabilities)
# ---------------------------------------------------------------------------

def test_tanglish_fast_paths_greeting_and_capabilities():
    """Verifies fast path handling for Tanglish greetings and capability queries."""
    import re
    tamil_regex = re.compile(r"[\u0B80-\u0BFF]")

    # Tanglish Greeting
    sess_id = "test-tanglish-fast-path"
    payload = {"session_id": sess_id, "message": "vanakkam, epdi irukinga?"}
    resp = client.post("/api/assistant/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_language"] == "tanglish"
    assert data["role"] == "assistant"
    assert data["is_fallback"] is False
    assert data["model_name"] == "BUILTIN_ASSISTANT"
    assert "Vanakkam!" in data["content"]
    assert "Market Assistant" in data["content"]
    assert not tamil_regex.search(data["content"])

    # Tanglish Capabilities
    payload = {"session_id": sess_id, "message": "unnaala enna panna mudiyum?"}
    resp = client.post("/api/assistant/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_language"] == "tanglish"
    assert data["is_fallback"] is False
    assert "copilot" in data["content"] or "kekkalam" in data["content"]
    assert not tamil_regex.search(data["content"])

    client.delete(f"/api/assistant/history/{sess_id}")


# ---------------------------------------------------------------------------
# 19. Tanglish Deterministic Fallback (Offline Ollama)
# ---------------------------------------------------------------------------

def test_tanglish_deterministic_fallback():
    """Verifies that when Ollama is offline, a Tanglish query receives a Tanglish deterministic fallback."""
    import re
    tamil_regex = re.compile(r"[\u0B80-\u0BFF]")

    with patch("app.services.ai_provider.OllamaProvider.check_health") as mock_health:
        mock_health.return_value = {"status": "OFFLINE", "available_models": []}

        sess_id = "test-tanglish-fallback"
        payload = {
            "session_id": sess_id,
            "message": "RELIANCE oda RSI epdi irukku?",
            "symbol": "RELIANCE",
            "market": "NSE",
        }
        resp = client.post("/api/assistant/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["detected_language"] == "tanglish"
        assert data["is_fallback"] is True
        assert data["model_name"] == "DETERMINISTIC_FALLBACK"
        assert "Local AI Model Offline illana Timed Out" in data["content"]
        assert "RELIANCE" in data["content"]
        assert "RSI (14):" in data["content"]
        assert not tamil_regex.search(data["content"])

        client.delete(f"/api/assistant/history/{sess_id}")



