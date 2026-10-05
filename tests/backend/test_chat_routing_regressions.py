"""Chat regression checks with isolated SQLite and mocked model transport."""
from unittest.mock import patch, MagicMock
import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database.base import Base
from app.services.market_assistant_service import MarketAssistantService as Chat, AssistantIntent as I
from app.services.indicators_service import IndicatorsService
from app.services.market_data_service import MarketDataService


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.mark.parametrize("message,intent", [
    ("Hi", I.GREETING), ("How are you?", I.GENERAL_CHAT),
    ("What is stock market?", I.EDUCATIONAL), ("Explain RSI", I.EDUCATIONAL),
    ("What is NIFTY 50?", I.EDUCATIONAL), ("What is portfolio equity?", I.EDUCATIONAL),
    ("Explain risk limits", I.EDUCATIONAL), ("Explain XGBoost", I.EDUCATIONAL),
    ("Write Python code for NIFTY csv", I.GENERAL_CHAT),
    ("What's happening in NIFTY right now?", I.INSTRUMENT_ANALYSIS),
    ("Why did our strategy generate a BUY signal?", I.STRATEGY_EXPLANATION),
    ("Analyze my portfolio risk", I.RISK_ANALYSIS),
    ("Explain RSI and analyze RELIANCE RSI", I.TECHNICAL_ANALYSIS),
    ("Stock market na enna?", I.EDUCATIONAL),
    ("NIFTY ippo epdi irukku?", I.INSTRUMENT_ANALYSIS),
])
def test_routing(message, intent):
    assert Chat.detect_intent(message) == intent


@pytest.mark.parametrize("message", ["Hi", "What is stock market?", "Explain RSI", "What is portfolio equity?", "Explain XGBoost", "Write Python code"])
def test_no_market_tools(db, message):
    with patch.object(Chat, "collect_market_data_context", side_effect=AssertionError("market tool")), patch.object(Chat, "collect_portfolio_context", side_effect=AssertionError("portfolio tool")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        result = Chat.process_chat_message(db, "no-tools", message, symbol="NIFTY 50")
    assert result.sources == []
    assert result.symbol_context is None
    assert "Market Analysis" not in result.content


def test_relevant_fallback_and_recovery(db):
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        result = Chat.process_chat_message(db, "recover", "Write Python code")
        assert result.is_fallback and "unavailable" in result.content
        assert "portfolio" not in result.content.lower()
    response = MagicMock(status_code=200)
    response.json.return_value = {"response": "```python\nprint('hello')\n```", "done": True}
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=response) as post:
        result = Chat.process_chat_message(db, "recover", "Write Python code")
    assert "Local Qwen AI is unavailable" not in post.call_args.kwargs["json"]["prompt"]
    assert not result.is_fallback and result.model_name == Chat.DEFAULT_MODEL


@pytest.mark.parametrize("payload", [{"response": ""}, {"response": []}, {"response": "<think>secret</think>"}, {"response": "incomplete", "done": False}, {"response": "வணக்கம்"}, {"response": "The market is a market. The market is a market. The market is a market. The market is a market."}, {"response": "Local Qwen AI is unavailable or could not produce a valid answer."}])
def test_invalid_model_output(db, payload):
    response = MagicMock(status_code=200)
    response.json.return_value = payload
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=response):
        result = Chat.process_chat_message(db, "invalid", "Write Python code")
    assert result.is_fallback
    assert "unavailable" in result.content


def test_timeout(db):
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", side_effect=httpx.ReadTimeout("test")):
        result = Chat.process_chat_message(db, "timeout", "Explain RSI")
    assert result.is_fallback and result.sources == []


def test_price_tool_plan_and_live_disclosure(db):
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}), patch.object(IndicatorsService, "compute_all_indicators", side_effect=AssertionError("unneeded indicators")):
        result = Chat.process_chat_message(db, "live", "What's happening in NIFTY right now?")
    assert [s.tool_name for s in result.sources] == ["MarketDataTool"]
    assert "Live market data is unavailable" in result.content
    assert result.sources[0].data_points["live_available"] is False


def test_tanglish_live_availability_skips_model(db):
    with patch("app.services.ai_provider.OllamaProvider.check_health", side_effect=AssertionError("unneeded model health")):
        result = Chat.process_chat_message(db, "tanglish-live", "NIFTY ippo epdi irukku?")
    assert result.detected_language == "tanglish"
    assert result.model_name == "BUILTIN_ASSISTANT"
    assert Chat.detect_language(result.content) == "tanglish"
    assert len(result.sources) == 1


def test_only_rsi_computed(db):
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}), patch.object(IndicatorsService, "calculate_macd", side_effect=AssertionError("unneeded MACD")), patch.object(IndicatorsService, "calculate_atr", side_effect=AssertionError("unneeded ATR")):
        result = Chat.process_chat_message(db, "rsi", "Check RSI on RELIANCE")
    assert [s.tool_name for s in result.sources] == ["MarketDataTool", "TechnicalIndicatorsTool"]


def test_strategy_does_not_recompute_signal(db):
    with patch.object(Chat, "collect_market_data_context", side_effect=AssertionError("recomputed signal")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        result = Chat.process_chat_message(db, "signal", "Why did our strategy generate a BUY signal?")
    assert result.sources == []
    assert "proposal ID" in result.content


def test_reject_out_of_order_candles(db):
    candles = MarketDataService().get_ohlc("RELIANCE")
    candles.candles.reverse()
    with patch.object(MarketDataService, "get_ohlc", return_value=candles):
        context, sources = Chat.collect_market_data_context(db, "RELIANCE")
    assert sources == [] and "rejected" in context


def test_language_switch():
    assert Chat.detect_language("Hey bro, how are you?", "tanglish") == "english"
    assert Chat.detect_language("Explain RSI", "tanglish") == "english"
    assert Chat.detect_language("Write Python code", "tanglish") == "english"
    assert Chat.detect_language("RSI na enna?", "english") == "tanglish"


def test_english_model_answer_to_tanglish_is_rejected(db):
    response = MagicMock(status_code=200)
    response.json.return_value = {"response": "The stock market is where investors buy shares of companies.", "done": True}
    with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=response):
        result = Chat.process_chat_message(db, "wrong-language", "Stock market na enna?")
    assert result.is_fallback and result.detected_language == "tanglish"
    assert "kidaikkala" in result.content


def test_configured_model_is_never_replaced():
    assert Chat._resolve_best_model(["kimi-k2.6:cloud", "llama3.2:latest"], Chat.DEFAULT_MODEL) == Chat.DEFAULT_MODEL


def test_grounded_values_reject_invented_price():
    assert Chat.grounded_numbers_valid("Close 2,950.12; RSI 48.2", "close:2950.12 RSI:48.2")
    assert not Chat.grounded_numbers_valid("Close 99999.12", "close:2950.12 RSI:48.2")


def test_concurrent_inference_has_bounded_admission(db):
    Chat._inference_slot.acquire()
    try:
        with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", side_effect=AssertionError("duplicate concurrent inference")):
            result = Chat.process_chat_message(db, "busy", "Write code")
        assert result.is_fallback
        assert result.inference_latency_ms < 1500
    finally:
        Chat._inference_slot.release()
