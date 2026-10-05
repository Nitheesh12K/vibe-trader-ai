"""Bounded, validated search excerpts. Never claim full article verification.

Local Ollama experimentally proxies its signed-in web-search service. Hosted
Ollama search is also supported with a server-side API key. No article URLs are
fetched: this avoids redirects, SSRF and pretending excerpts are full articles.
"""
import json
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import httpx
from app.core.config import settings
from app.schemas.news import NewsArticle, NewsResult
from app.services.news_intent import public_topic

PUBLISHERS = {
    "reuters.com": "Reuters", "cnbctv18.com": "CNBC TV18",
    "economictimes.indiatimes.com": "The Economic Times",
    "moneycontrol.com": "Moneycontrol", "livemint.com": "Mint",
    "business-standard.com": "Business Standard", "rbi.org.in": "Reserve Bank of India",
    "cnbc.com": "CNBC", "bbc.com": "BBC", "bbc.co.uk": "BBC",
    "financialexpress.com": "Financial Express", "thehindubusinessline.com": "BusinessLine",
}


@dataclass
class _Flight:
    event: threading.Event = field(default_factory=threading.Event)
    result: NewsResult | None = None


def validated_url(value: object) -> tuple[str, str]:
    if not isinstance(value, str) or len(value) > 2048 or re.search(r"[\s\\\x00-\x1f]", value):
        raise ValueError("Invalid article URL")
    parts = urlsplit(value)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError("Unsafe article URL")
    domain = next((d for d in PUBLISHERS if host == d or host == "www." + d), None)
    if not domain or not parts.path or parts.path == "/":
        raise ValueError("Unapproved publisher or non-article URL")
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}])
    return urlunsplit(("https", host, parts.path.rstrip("/"), query, "")), PUBLISHERS[domain]


def publication_time(content: str) -> datetime:
    # Only explicit Published metadata. Never use headline/URL dates, Updated
    # dates, relative age or retrieval time as the original publication time.
    match = re.search(r"(?:published(?:\s+(?:at|on|time))?\s*[:\-]?\s*)(\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|[+-]\d{2}:\d{2}))", content, re.I)
    if match:
        return datetime.fromisoformat(match[1].replace("Z", "+00:00")).astimezone(timezone.utc)
    stamp = r"([A-Za-z]+\s+\d{1,2},?\s+\d{4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*(?:IST|UTC|GMT))"
    match = re.search(stamp + r"\s*\(Published\)", content, re.I) or re.search(r"Published(?:\s+(?:at|on))?\s*[:\-]?\s*" + stamp, content, re.I)
    if not match:
        raise ValueError("No explicit publication timestamp")
    raw = re.sub(r"\s+", " ", match[1]).strip()
    zone = raw.split()[-1].upper()
    raw = raw[:-(len(zone) + 1)].replace(",", "")
    for fmt in ("%B %d %Y %I:%M:%S %p", "%B %d %Y %I:%M %p", "%B %d %Y %H:%M:%S", "%B %d %Y %H:%M", "%b %d %Y %I:%M %p", "%b %d %Y %H:%M"):
        try:
            tz = timezone(timedelta(hours=5, minutes=30)) if zone == "IST" else timezone.utc
            return datetime.strptime(raw, fmt).replace(tzinfo=tz).astimezone(timezone.utc)
        except ValueError:
            continue
    raise ValueError("Invalid publication timestamp")


class NewsService:
    def __init__(self, config=settings, transport=None, now=None):
        self.config = config
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.client = httpx.Client(trust_env=False, follow_redirects=False, transport=transport)
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        self._pending: dict[str, _Flight] = {}

    def _request(self, query: str) -> list:
        deadline = time.monotonic() + self.config.NEWS_TIMEOUT_SECONDS * (self.config.NEWS_RETRIES + 1)
        provider = self.config.NEWS_PROVIDER
        headers = {}
        if provider == "ollama_local":
            url = self.config.CHAT_OLLAMA_HOST.rstrip("/") + "/api/experimental/web_search"
        elif provider == "ollama_hosted":
            key = self.config.NEWS_API_KEY.get_secret_value()
            if not key:
                raise ValueError("Missing server-side news credential")
            headers = {"Authorization": "Bearer " + key}
            url = "https://ollama.com/api/web_search"
        else:
            raise ValueError("Unsupported news provider")
        for attempt in range(self.config.NEWS_RETRIES + 1):
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise httpx.ReadTimeout("News retrieval deadline exceeded")
                # Streaming bounds body size and prevents overlarge search data
                # from ever being passed to the model or saved to the database.
                with self.client.stream("POST", url, headers=headers, json={"query": query, "max_results": 5}, timeout=httpx.Timeout(min(self.config.NEWS_TIMEOUT_SECONDS, remaining), connect=min(2, remaining))) as response:
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        if time.monotonic() > deadline:
                            raise httpx.ReadTimeout("News retrieval deadline exceeded")
                        body.extend(chunk)
                        if len(body) > 200_000:
                            raise ValueError("Provider response too large")
                    payload = json.loads(body)
                    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                        raise ValueError("Malformed provider response")
                    return payload["results"][:10]
            except (httpx.TransportError, httpx.HTTPStatusError) as error:
                retryable = isinstance(error, httpx.TransportError) or error.response.status_code in {502, 503, 504}
                if not retryable or attempt == self.config.NEWS_RETRIES:
                    raise
        return []

    def revalidate(self, result: NewsResult, reused=False) -> NewsResult:
        now = self._now()
        articles = [a for a in result.articles if timedelta(0) <= now - a.published_at <= timedelta(hours=self.config.NEWS_MAX_AGE_HOURS)]
        return result.model_copy(deep=True, update={"articles": articles, "checked_at": now, "context_reused": reused, "status": "OK" if articles else "NO_RECENT_NEWS", "summary": "", "possible_market_implications": "", "model_metrics": {}})

    def retrieve(self, message: str) -> NewsResult:
        started = time.perf_counter()
        now = self._now()
        topic, terms = public_topic(message)
        base = dict(provider=self.config.NEWS_PROVIDER, checked_at=now, max_age_hours=self.config.NEWS_MAX_AGE_HOURS)
        if not topic:
            return NewsResult(status="CLARIFICATION", notice="Which company or financial topic should I search?", **base)
        query = f"{topic} latest news {now.date().isoformat()}"
        # Cache and flights are bounded. Different public topics run independently.
        with self._lock:
            entry = self._cache.get(query)
            if entry and time.monotonic() - entry[0] < self.config.NEWS_CACHE_TTL_SECONDS:
                result = self.revalidate(entry[1])
                if result.articles:
                    self._cache.move_to_end(query)
                    return result.model_copy(update={"cache_hit": True, "retrieval_ms": round((time.perf_counter() - started) * 1000, 2)})
            self._cache.pop(query, None)
            flight = self._pending.get(query)
            owner = flight is None
            if owner:
                if len(self._pending) >= 16:
                    return NewsResult(status="PROVIDER_ERROR", notice="News service is busy. Please retry shortly.", **base)
                flight = self._pending[query] = _Flight()
        if not owner:
            flight.event.wait(self.config.NEWS_TIMEOUT_SECONDS * (self.config.NEWS_RETRIES + 1) + 1)
            if flight.result is not None:
                result = self.revalidate(flight.result) if flight.result.articles else flight.result.model_copy(deep=True)
                return result.model_copy(update={"cache_hit": bool(result.articles), "retrieval_ms": round((time.perf_counter() - started) * 1000, 2)})
            return NewsResult(status="PROVIDER_ERROR", notice="The simultaneous news request did not return recent evidence. Please retry.", query=query, **base)
        result = None
        try:
            raw = self._request(query)
            retrieved = self._now()
            articles, seen, titles, rejected = [], set(), set(), 0
            for row in raw:
                try:
                    if not isinstance(row, dict):
                        raise ValueError("Invalid result")
                    title, content = row.get("title"), row.get("content")
                    if not isinstance(title, str) or not title.strip() or not isinstance(content, str):
                        raise ValueError("Missing article text")
                    url, publisher = validated_url(row.get("url"))
                    text = re.sub(r"<[^>]*>", " ", content)[:16000]
                    if not any(re.search(r"\b" + re.escape(term) + r"\b", (title + " " + text).lower()) for term in terms):
                        raise ValueError("Irrelevant result")
                    published = publication_time(text)
                    if not timedelta(0) <= retrieved - published <= timedelta(hours=self.config.NEWS_MAX_AGE_HOURS):
                        raise ValueError("Stale or future publication")
                    normalized_title = re.sub(r"\W+", " ", title.lower()).strip()
                    if url in seen or normalized_title in titles:
                        raise ValueError("Duplicate article")
                    seen.add(url); titles.add(normalized_title)
                    excerpt = text.split("## Story", 1)[-1]
                    excerpt = re.sub(r"^(Author|Source|Language):[^\n]*", "", excerpt, flags=re.M | re.I)
                    excerpt = re.sub(r"^Published:\s*\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|[+-]\d{2}:\d{2})\s*$", "", excerpt, flags=re.M | re.I)
                    excerpt = re.sub(re.escape(title), "", excerpt, flags=re.I)
                    excerpt = re.sub(re.escape(title.split(" - ")[0]), "", excerpt, flags=re.I)
                    if "Synopsis" in excerpt[:700]:
                        excerpt = excerpt.split("Synopsis", 1)[1]
                    excerpt = re.sub(r"\s+", " ", excerpt).strip(" #|-")[:500]
                    articles.append(NewsArticle(title=re.sub(r"<[^>]*>", "", title).strip()[:220], publisher=publisher, url=url, published_at=published, retrieved_at=retrieved, snippet=excerpt, provider=self.config.NEWS_PROVIDER))
                except (ValueError, TypeError):
                    rejected += 1
            articles.sort(key=lambda a: a.published_at, reverse=True)
            base["checked_at"] = retrieved
            result = NewsResult(status="OK" if articles else "NO_RECENT_NEWS", query=query, articles=articles[:self.config.NEWS_MAX_ARTICLES], rejected_results=rejected, notice="Search excerpts only; full article contents have not been independently verified." if articles else "No relevant recent articles with a trusted URL and explicit publication timestamp were returned.", **base)
            if articles:
                with self._lock:
                    self._cache[query] = (time.monotonic(), result.model_copy(deep=True))
                    while len(self._cache) > 64:
                        self._cache.popitem(last=False)
            return result.model_copy(update={"retrieval_ms": round((time.perf_counter() - started) * 1000, 2)})
        except (httpx.HTTPError, ValueError, TypeError) as error:
            # Never relay provider exception/body: it can contain credentials.
            code = "UNAVAILABLE"
            if isinstance(error, httpx.HTTPStatusError):
                code = "RATE_LIMITED" if error.response.status_code == 429 else ("AUTH_REQUIRED" if error.response.status_code in {401, 403} else "UNAVAILABLE")
            elif isinstance(error, httpx.TimeoutException):
                code = "TIMEOUT"
            elif isinstance(error, (ValueError, TypeError)):
                code = "CONFIGURATION_ERROR" if self.config.NEWS_PROVIDER not in {"ollama_local", "ollama_hosted"} or (self.config.NEWS_PROVIDER == "ollama_hosted" and not self.config.NEWS_API_KEY.get_secret_value()) else "BAD_RESPONSE"
            notices = {
                "RATE_LIMITED": "News provider rate limit reached. Please wait before retrying; no automatic rate-limit retry was made.",
                "AUTH_REQUIRED": "News search requires provider authentication. Check Ollama sign-in or the server-side API key.",
                "TIMEOUT": "News provider timed out. Please retry when its connection recovers.",
                "CONFIGURATION_ERROR": "News provider configuration is incomplete or unsupported. Check server-side NEWS_PROVIDER and credentials.",
                "BAD_RESPONSE": "News provider returned an invalid response. No current news was generated.",
                "UNAVAILABLE": "News provider unavailable. Check Ollama web-search connectivity, then retry.",
            }
            result = NewsResult(status="PROVIDER_ERROR", query=query, error_code=code, notice=notices[code], retrieval_ms=round((time.perf_counter() - started) * 1000, 2), **base)
            return result
        finally:
            with self._lock:
                self._pending.pop(query, None)
                flight.result = result
                flight.event.set()


news_service = NewsService()
