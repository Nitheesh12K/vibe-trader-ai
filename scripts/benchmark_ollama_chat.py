"""Real local model streaming probe. No mocked timings, no model downloads.

Does not unload the user's model. Cold-load timing is reported only when the
server reports it; warm probes cannot establish a controlled cold baseline.
"""
import argparse
import json
import os
import statistics
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import httpx
from app.core.config import settings

parser = argparse.ArgumentParser()
parser.add_argument("--runs", type=int, default=3)
parser.add_argument("--output", default="docs/ollama_chat_benchmark.json")
args = parser.parse_args()
samples = []
with httpx.Client(timeout=httpx.Timeout(50, connect=2), trust_env=False) as client:
    models = client.get(settings.CHAT_OLLAMA_HOST + "/api/ps").json()
    for i in range(args.runs):
        start = time.perf_counter()
        first = None
        final = {}
        output = ""
        with client.stream("POST", settings.CHAT_OLLAMA_HOST + "/api/generate", json={"model": settings.CHAT_OLLAMA_MODEL, "prompt": "You are Vibe Trader AI, a general-purpose conversational assistant. Reply in English. Answer directly and concisely. No thinking tags. You cannot execute trades.\nUser: What is stock market?\nAssistant:", "think": False, "stream": True, "keep_alive": "60m", "options": {"num_ctx": 4096, "num_predict": 140, "temperature": .2}}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                event = json.loads(line)
                token = event.get("response", "")
                if token and first is None:
                    first = (time.perf_counter() - start) * 1000
                output += token
                if event.get("done"):
                    final = event
        duration = final.get("eval_duration", 0)
        samples.append({"wall_ms": (time.perf_counter() - start) * 1000, "ttft_ms": first, "load_ms": final.get("load_duration", 0)/1e6, "prompt_eval_ms": final.get("prompt_eval_duration", 0)/1e6, "eval_ms": duration/1e6, "tokens": final.get("eval_count"), "tokens_per_second": final.get("eval_count", 0)/(duration/1e9) if duration else None, "done_reason": final.get("done_reason"), "answer": output})
        print(json.dumps(samples[-1]), flush=True)
wall = sorted(s["wall_ms"] for s in samples)
Path(args.output).write_text(json.dumps({"mode": "real Ollama warm sequential probes, streaming transport probe only", "hardware": {"cpu": os.getenv("PROCESSOR_IDENTIFIER"), "logical_processors": os.cpu_count(), "ram_cpu_utilization": "OS inventory access denied"}, "loaded_models": models, "model": settings.CHAT_OLLAMA_MODEL, "median_ms": statistics.median(wall), "p95_ms": wall[-1], "runs": args.runs, "samples": samples}, indent=2), encoding="utf-8")
