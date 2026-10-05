"""Repeatable chat benchmark. Offline mode mocks ONLY Ollama availability.

Uses an isolated in-memory database; never changes the user's paper account.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database.base import Base
from app.services.market_assistant_service import MarketAssistantService as Chat

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--runs", type=int, default=10)
args = parser.parse_args()
engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
results = {}
for message in ["Hi", "What is stock market?", "Explain RSI", "What's happening in NIFTY right now?", "Why did our strategy generate a BUY signal?"]:
    samples = []
    for run in range(args.runs):
        with Session(engine) as db, patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE"}):
            start = time.perf_counter()
            response = Chat.process_chat_message(db, f"bench-{run}-{message}", message)
            samples.append({"wall_ms": (time.perf_counter() - start) * 1000, "route_ms": response.routing_time_ms, "tools": len(response.sources), "tool_ms": response.tool_latency_ms, "inference_ms": response.inference_latency_ms, "intent": response.detected_intent})
    ordered = sorted(s["wall_ms"] for s in samples)
    results[message] = {"median_ms": statistics.median(ordered), "p95_ms": ordered[min(len(ordered)-1, int(len(ordered)*.95))], "samples": samples}
Path(args.output).write_text(json.dumps({"mode": "real router/tools/SQLite; mocked Ollama offline", "runs": args.runs, "results": results}, indent=2), encoding="utf-8")
print(json.dumps({m: {k:v for k,v in r.items() if k != "samples"} for m,r in results.items()}, indent=2))
