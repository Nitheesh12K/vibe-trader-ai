"""Deterministic news tests: mocked search transport and mocked Qwen, no live network."""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.database.base import Base
from app.schemas.news import NewsResult
from app.services.news_service import NewsService, publication_time, validated_url
from app.services.market_assistant_service import MarketAssistantService as Chat
from app.services.news_intent import public_topic

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)


def article(**overrides):
    return {"title": "NIFTY outlook ahead of RBI policy", "url": "https://www.cnbctv18.com/market/nifty-outlook.htm", "content": "Published: 2026-10-04T04:08:29Z. NIFTY analysts watch the upcoming RBI policy. The outcome remains uncertain.", **overrides}


def service(rows=None, handler=None, **config):
    return NewsService(Settings(_env_file=None, **config), httpx.MockTransport(handler or (lambda request: httpx.Response(200, json={"results": rows if rows is not None else [article()]}))), lambda: NOW)


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.mark.parametrize("message,intent", [
    ("Hi", "GREETING"), ("What is stock market?", "EDUCATIONAL"),
    ("What is RSI?", "EDUCATIONAL"), ("What is financial news?", "EDUCATIONAL"),
    ("How does news affect banks?", "EDUCATIONAL"),
    ("What is the latest NIFTY news?", "NEWS_CURRENT"),
    ("Latest news about Infosys", "COMPANY_NEWS"),
    ("Latest news about Reliance?", "COMPANY_NEWS"),
    ("Any recent RBI announcements?", "NEWS_CURRENT"),
    ("Explain today's major global financial news", "NEWS_SUMMARY"),
    ("How might RBI's latest announcement affect banks?", "MARKET_NEWS_IMPACT"),
    ("What's happening in NIFTY today?", "NEWS_CURRENT"),
    ("What's happening in NIFTY right now?", "INSTRUMENT_ANALYSIS"),
    ("NIFTY RSI today", "TECHNICAL_ANALYSIS"),
    ("Why did my strategy generate a BUY signal?", "STRATEGY_EXPLANATION"),
    ("Intha news NIFTY mela enna impact pannum?", "MARKET_NEWS_IMPACT"),
])
def test_news_routes(message, intent):
    assert Chat.detect_intent(message) == intent


def test_language_switches_on_latest_news_message():
    assert Chat.detect_language("Latest NIFTY news", previous_language="tanglish") == "english"
    assert Chat.detect_language("NIFTY latest news sollunga", previous_language="english") == "tanglish"
    assert Chat.detect_language("Intha news NIFTY mela enna impact pannum?", previous_language="english") == "tanglish"


@pytest.mark.parametrize("text", ["A 25-year-long losing streak", "An ８-week losing streak", "A twenty five year losing streak"])
def test_quantitative_prose_cannot_bypass_validation(text):
    from app.schemas.news import NewsAnalysis
    with pytest.raises(ValueError):
        NewsAnalysis(summary=article()["title"], possible_market_implications=text, source_ids=[1])


@pytest.mark.parametrize("message", ["Hi", "What is stock market?", "Explain RSI", "What is financial news?", "Write Python code"])
def test_no_news_tools(db, message):
    with patch("app.services.market_assistant_service.news_service.retrieve", side_effect=AssertionError("Unexpected news retrieval")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        result = Chat.process_chat_message(db, "no-news", message)
    assert result.news is None and result.sources == []


def test_valid_evidence_cache_and_timestamps():
    news = service([article(), article(url=article()["url"] + "?utm_source=test"), article(title="Another NIFTY source", url="https://www.moneycontrol.com/news/second.html")])
    first = news.retrieve("Latest NIFTY news")
    second = news.retrieve("What's happening in NIFTY today?")
    assert len(first.articles) == 2 and first.rejected_results == 1
    assert second.cache_hit and second.articles == first.articles
    assert first.articles[0].published_at != first.articles[0].retrieved_at
    assert first.articles[0].evidence_type == "SEARCH_EXCERPT"


@pytest.mark.parametrize("row", [
    article(url=None), article(url="javascript:alert(1)"), article(url="https://127.0.0.1/private"),
    article(url="https://cnbctv18.com.attacker.test/news/a"), article(url="https://user:secret@cnbctv18.com/news/a"),
    article(url="https://www.cnbctv18.com:444/news/a"), article(url="https://www.cnbctv18.com/"),
    article(content="NIFTY report without publication time"),
    article(content="Updated: 2026-10-04T04:08:29Z NIFTY report"),
    article(content="Published: 2026-09-01T04:08:29Z NIFTY report"),
    article(content="Published: 2026-10-05T04:08:29Z NIFTY report"),
    article(title="Cooking recipes", content="Published: 2026-10-04T04:08:29Z Cooking recipes"),
    article(title=None), article(content=None), [],
])
def test_reject_bad_stale_irrelevant_results(row):
    result = service([row]).retrieve("Latest NIFTY news")
    assert result.status == "NO_RECENT_NEWS" and result.articles == []


@pytest.mark.parametrize("value", ["2026-10-04 12:00", "Oct 4, 2026", "Published: definitely today", "Published: 2026-13-04T00:00:00Z"])
def test_missing_or_malformed_dates(value):
    with pytest.raises(ValueError):
        publication_time(value)


def test_explicit_ist_metadata():
    assert publication_time("October 4, 2026, 9:38:29 AM IST (Published)") == datetime(2026, 10, 4, 4, 8, 29, tzinfo=timezone.utc)


@pytest.mark.parametrize("body", [{}, {"results": {}}, [1, 2]])
def test_malformed_provider(body):
    result = service(handler=lambda request: httpx.Response(200, json=body)).retrieve("Latest NIFTY news")
    assert result.status == "PROVIDER_ERROR"


def test_errors_not_cached_and_recovery():
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) <= 2:
            raise httpx.ReadTimeout("private secret must not leak")
        return httpx.Response(200, json={"results": [article()]})
    news = service(handler=handler)
    assert news.retrieve("Latest NIFTY news").status == "PROVIDER_ERROR"
    recovered = news.retrieve("Latest NIFTY news")
    assert recovered.status == "OK" and not recovered.cache_hit and len(calls) == 3
    assert "secret" not in recovered.model_dump_json()


def test_auth_failure_no_retry_and_no_secret():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(401, json={"error": "super-private-token"})
    result = service(handler=handler).retrieve("Latest NIFTY news")
    assert len(calls) == 1 and "super-private-token" not in result.model_dump_json()
    assert result.error_code == "AUTH_REQUIRED"


def test_rate_limit_has_actionable_notice_without_retry():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429)
    result = service(handler=handler).retrieve("Latest NIFTY news")
    assert result.error_code == "RATE_LIMITED" and "wait" in result.notice
    assert len(calls) == 1


def test_hosted_key_server_side():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"results": [article()]})
    result = service(handler=handler, NEWS_PROVIDER="ollama_hosted", NEWS_API_KEY="test-server-secret").retrieve("Latest NIFTY news")
    assert calls[0].headers["Authorization"] == "Bearer test-server-secret"
    assert "test-server-secret" not in result.model_dump_json()
    assert service(NEWS_PROVIDER="ollama_hosted").retrieve("Latest NIFTY news").status == "PROVIDER_ERROR"


def test_single_flight_and_cache_expiry():
    calls = []
    def handler(request):
        calls.append(request)
        time.sleep(0.05)
        return httpx.Response(200, json={"results": [article()]})
    news = service(handler=handler)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(news.retrieve, ["Latest NIFTY news"] * 4))
    assert len(calls) == 1 and sum(n.cache_hit for n in results) == 3
    news._now = lambda: NOW + timedelta(hours=73)
    assert news.revalidate(results[0]).status == "NO_RECENT_NEWS"
    news.config.NEWS_CACHE_TTL_SECONDS = 0
    news._now = lambda: NOW
    assert not news.retrieve("Latest NIFTY news").cache_hit and len(calls) == 2


def test_public_queries_do_not_send_private_text():
    calls = []
    news = service(handler=lambda request: (calls.append(json.loads(request.content)) or httpx.Response(200, json={"results": [article()]})))
    news.retrieve("Latest RBI announcement for my portfolio account private123")
    assert "RBI" in calls[0]["query"] and "private123" not in calls[0]["query"]
    assert public_topic("Latest news about UnknownCorp") == ("", [])


@pytest.mark.parametrize("message", ["Latest UnknownCorp news", "Today sports news"])
def test_unknown_topic_clarifies_without_provider_call(message):
    news = service(handler=lambda request: (_ for _ in ()).throw(AssertionError("unrelated search")))
    assert news.retrieve(message).status == "CLARIFICATION"


@pytest.mark.parametrize("language,message", [("english", "Latest NIFTY news"), ("tanglish", "NIFTY latest news sollunga")])
def test_relevant_offline_news_fallback_and_history(db, language, message):
    result = service().retrieve(message)
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=result), patch.object(Chat, "collect_market_data_context", side_effect=AssertionError("unrelated market tool")), patch.object(Chat, "collect_portfolio_context", side_effect=AssertionError("unrelated account tool")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        response = Chat.process_chat_message(db, "news-history", message)
    assert response.is_fallback and response.model_name == "DETERMINISTIC_FALLBACK"
    assert response.detected_language == language and response.news.articles
    assert "MarketDataTool" not in response.model_dump_json()
    assert Chat.get_history(db, "news-history")[-1].news == response.news
    assert response.news.summary == "" and response.news.possible_market_implications == ""


def model_mock(payload):
    response = MagicMock(status_code=200)
    response.json.return_value = {"done": True, "response": payload}
    return response


VALID_ANALYSIS = json.dumps({"summary": article()["title"], "possible_market_implications": "Policy developments could affect sentiment; the outcome is uncertain.", "source_ids": [1]})


def test_news_generation_timeout_and_recovery(db):
    with patch("app.services.market_assistant_service.news_service.retrieve", side_effect=lambda q: service().retrieve(q)), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", side_effect=httpx.ReadTimeout("mock timeout")):
        first = Chat.process_chat_message(db, "news-recovery", "Latest NIFTY news")
    assert first.is_fallback and first.news.summary == ""
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=service().retrieve("Latest NIFTY news")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=model_mock(VALID_ANALYSIS)) as generate:
        second = Chat.process_chat_message(db, "news-recovery", "Latest NIFTY news")
    assert not second.is_fallback and second.news.summary
    prompt = generate.call_args.kwargs["json"]["prompt"]
    assert "untrusted" in prompt and "Local AI summary is unavailable" not in prompt


@pytest.mark.parametrize("output", ["not json", "{}", json.dumps({"summary": "Made up event [99]", "possible_market_implications": "", "source_ids": [99]}), VALID_ANALYSIS.replace("could", "will"), VALID_ANALYSIS.replace("RBI", "RBI cut rates 999%"), VALID_ANALYSIS.replace("NIFTY", "https://evil.example NIFTY")])
def test_invalid_news_generation_fallback(db, output):
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=service().retrieve("Latest NIFTY news")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=model_mock(output)):
        result = Chat.process_chat_message(db, "bad-news", "Latest NIFTY news")
    assert result.is_fallback and result.news.summary == ""


def test_no_evidence_no_model_and_followup_clarification(db):
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=service([]).retrieve("Latest NIFTY news")), patch("app.services.ai_provider.OllamaProvider.check_health", side_effect=AssertionError("unnecessary model call")), patch("httpx.Client.post", side_effect=AssertionError("unnecessary generation")):
        result = Chat.process_chat_message(db, "empty-news", "Latest NIFTY news")
        followup = Chat.process_chat_message(db, "empty-news", "How might this news affect banks?")
    assert result.news.status == "NO_RECENT_NEWS" and not result.is_fallback
    assert followup.news.status == "CLARIFICATION" and not followup.news.articles


def test_followup_reuses_only_session_evidence(db):
    news = service()
    with patch("app.services.market_assistant_service.news_service", news), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        initial = Chat.process_chat_message(db, "follow-news", "Latest NIFTY news")
        with patch.object(news, "retrieve", side_effect=AssertionError("duplicate search")):
            response = Chat.process_chat_message(db, "follow-news", "Intha news NIFTY mela enna impact pannum?")
            isolated = Chat.process_chat_message(db, "another-session", "How might this news affect banks?")
    assert response.news.context_reused and response.news.articles == initial.news.articles
    assert response.detected_language == "tanglish" and isolated.news.status == "CLARIFICATION"


def test_missing_inline_citation_uses_validated_structured_ids(db):
    payload = json.loads(VALID_ANALYSIS)
    payload["summary"] = payload["summary"].replace(" [1]", "")
    output = json.dumps(payload)
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=service().retrieve("Latest NIFTY news")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=model_mock(output)):
        result = Chat.process_chat_message(db, "structured-cites", "Latest NIFTY news")
    assert not result.is_fallback and "[1]" in result.news.summary


def test_number_requires_correct_cited_source(db):
    evidence = service([article(), article(title="NIFTY weekly research", url="https://www.moneycontrol.com/news/other.html", content="Published: 2026-10-04T04:08:29Z NIFTY support is 22600.")]).retrieve("Latest NIFTY news")
    output = json.dumps({"summary": "NIFTY support is 22600 [1].", "possible_market_implications": "Could affect sentiment.", "source_ids": [1, 2]})
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=evidence), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=model_mock(output)):
        result = Chat.process_chat_message(db, "wrong-cite", "Latest NIFTY news")
    assert result.is_fallback and result.news.summary == ""


def test_duplicate_headlines_and_empty_responses_not_cached():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"results": []})
    news = service(handler=handler)
    assert news.retrieve("Latest NIFTY news").status == "NO_RECENT_NEWS"
    assert news.retrieve("Latest NIFTY news").status == "NO_RECENT_NEWS" and len(calls) == 2
    duplicate = service([article(), article(url="https://www.moneycontrol.com/news/syndicated.html")]).retrieve("Latest NIFTY news")
    assert len(duplicate.articles) == 1


def test_concurrent_failures_share_result_without_success_cache():
    calls = []
    def handler(request):
        calls.append(request)
        time.sleep(.03)
        return httpx.Response(503)
    news = service(handler=handler, NEWS_RETRIES=0)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(news.retrieve, ["Latest NIFTY news"] * 4))
    assert len(calls) == 1 and all(n.status == "PROVIDER_ERROR" for n in results)
    assert not news._cache


def test_invalid_json_and_oversized_provider_body():
    for body in (b"not-json", b"x" * 200001):
        result = service(handler=lambda request: httpx.Response(200, content=body)).retrieve("Latest NIFTY news")
        assert result.status == "PROVIDER_ERROR"


def test_news_never_submits_broker_orders(db):
    with patch("app.services.broker_adapter.PaperBrokerAdapter.submit_buy_order", side_effect=AssertionError("order submission")), patch("app.services.broker_adapter.PaperBrokerAdapter.submit_sell_order", side_effect=AssertionError("order submission")), patch("app.services.market_assistant_service.news_service.retrieve", return_value=service().retrieve("Latest NIFTY news")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
        result = Chat.process_chat_message(db, "no-orders", "Latest NIFTY news and market impact")
    assert result.news.articles and result.disclaimer.endswith("Paper trading only.")


def test_news_model_validation_logs_do_not_echo_response(db, caplog):
    secret_like_text = "private-account-test-value"
    output = json.dumps({"summary": secret_like_text, "possible_market_implications": "not valid 999", "source_ids": [1]})
    with patch("app.services.market_assistant_service.news_service.retrieve", return_value=service().retrieve("Latest NIFTY news")), patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "ONLINE", "available_models": [Chat.DEFAULT_MODEL]}), patch("httpx.Client.post", return_value=model_mock(output)):
        result = Chat.process_chat_message(db, "safe-log", "Latest NIFTY news")
    assert result.is_fallback and secret_like_text not in caplog.text
