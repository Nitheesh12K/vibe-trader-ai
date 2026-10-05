"""Opt-in REAL public news/Qwen benchmark. Does not stop services or place orders.

Run with the normal backend/frontend running. The offline test runner does not
invoke this script. Outputs public evidence and timing data, never credentials.
"""
import argparse
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.news_service import NewsService
from app.services.market_assistant_service import MarketAssistantService as Chat


def distribution(values):
    values = sorted(values)
    return {"runs": len(values), "median_ms": round(statistics.median(values), 2), "p95_ms": round(values[max(0, int(len(values) * .95 + .999999) - 1)], 2)} if values else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-runs", type=int, default=5)
    parser.add_argument("--chat-runs", type=int, default=3)
    parser.add_argument("--reuse-evidence", action="store_true", help="Summarize previously retrieved real evidence in the benchmark sessions; no new news query")
    parser.add_argument("--output", default="docs/news_benchmark.json")
    args = parser.parse_args()
    out = {"checked_at": datetime.now(timezone.utc).isoformat(), "hardware": {"platform": platform.platform(), "processor": os.environ.get("PROCESSOR_IDENTIFIER", platform.processor()), "logical_cpus": os.cpu_count()}, "provider": "ollama_local", "provider_misses": [], "provider_hits": [], "chat": [], "notes": "Real public news excerpts and real local Qwen. Already warmed model, no streaming/TTFT. p95 is nearest-rank, small sample, not a performance guarantee."}
    output = ROOT / args.output
    def save():
        output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    with httpx.Client(trust_env=False, timeout=70) as client:
        out["ollama_version"] = client.get("http://127.0.0.1:11434/api/version").json()
        out["model_details"] = client.post("http://127.0.0.1:11434/api/show", json={"model": Chat.DEFAULT_MODEL}).json().get("details")
        router = []
        for _ in range(1000):
            start = time.perf_counter()
            Chat.detect_intent("What's happening in NIFTY today?")
            router.append((time.perf_counter() - start) * 1000)
        out["routing"] = distribution(router)
        news = NewsService()
        try:
            for i in range(args.provider_runs):
                news._cache.clear()  # Benchmark-specific cold cache, never model unload.
                result = news.retrieve("Latest NIFTY news")
                out["provider_misses"].append(result.model_dump(mode="json"))
                print(f"Provider miss {i + 1}: {result.status}, {result.retrieval_ms}ms", flush=True)
                cached = news.retrieve("Latest NIFTY news")
                out["provider_hits"].append(cached.model_dump(mode="json"))
                save()
        finally:
            news.client.close()
        for i in range(args.chat_runs):
            start = time.perf_counter()
            response = client.post("http://127.0.0.1:8000/api/assistant/chat", json={"session_id": f"phase7-news-benchmark-{i}", "message": "Summarize this news" if args.reuse_evidence else "Latest NIFTY news"})
            response.raise_for_status()
            data = response.json()
            data["http_roundtrip_ms"] = round((time.perf_counter() - start) * 1000, 2)
            out["chat"].append(data)
            print(f"Chat {i + 1}: {data['http_roundtrip_ms']}ms, fallback={data['is_fallback']}", flush=True)
            save()
    out["metrics"] = {
        "provider_miss": distribution([n["retrieval_ms"] for n in out["provider_misses"]]),
        "provider_hit": distribution([n["retrieval_ms"] for n in out["provider_hits"] if n["cache_hit"]]),
        "qwen_stage": distribution([n["inference_latency_ms"] for n in out["chat"] if n.get("news", {}).get("articles")]),
        "model_total": distribution([n["news"]["model_metrics"]["total_duration"] for n in out["chat"] if n.get("news", {}).get("model_metrics", {}).get("total_duration")]),
        "chat_http_roundtrip": distribution([n["http_roundtrip_ms"] for n in out["chat"]]),
    }
    save()
    print(json.dumps(out["metrics"], indent=2))


if __name__ == "__main__":
    main()
