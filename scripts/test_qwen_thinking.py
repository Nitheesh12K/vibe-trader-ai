import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

ollama_base = "http://127.0.0.1:11434"

# Pre-load model into RAM with keep_alive: "60m"
print("1. Preloading qwen3-local:latest into RAM...")
preload_req = urllib.request.Request(
    f"{ollama_base}/api/generate",
    data=json.dumps({"model": "qwen3-local:latest", "keep_alive": "60m"}).encode(),
    headers={"Content-Type": "application/json"}
)
t0 = time.perf_counter()
urllib.request.urlopen(preload_req)
print(f"Preload complete in {(time.perf_counter()-t0)*1000:.1f}ms")

# Check /api/ps
ps_req = urllib.request.urlopen(f"{ollama_base}/api/ps")
print("RAM status:", json.loads(ps_req.read().decode()).get("models"))

# Test prompt 1: General question
p1 = "You are Vibe Trader AI Assistant. Answer in 2 short sentences: Who are you and how do you help traders?"
print("\n--- Test Prompt 1: General Question ---")
t0 = time.perf_counter()
req1 = urllib.request.Request(
    f"{ollama_base}/api/generate",
    data=json.dumps({
        "model": "qwen3-local:latest",
        "prompt": p1,
        "stream": False,
        "keep_alive": "60m",
        "options": {
            "temperature": 0.3,
            "num_predict": 180,
        }
    }).encode(),
    headers={"Content-Type": "application/json"}
)
res1 = json.loads(urllib.request.urlopen(req1, timeout=60).read().decode())
dur1 = (time.perf_counter() - t0) * 1000
raw1 = res1.get("response", "")
eval_cnt = res1.get("eval_count", 0)
eval_dur = res1.get("eval_duration", 0) / 1e6
tok_s = (eval_cnt / (eval_dur / 1000)) if eval_dur > 0 else 0
print(f"Prompt 1 total time: {dur1:.1f}ms ({dur1/1000:.2f}s)")
print(f"Tokens: {eval_cnt} generated @ {tok_s:.2f} tok/s")
print(f"Has <think>: {'<think>' in raw1}, Has </think>: {'</think>' in raw1}")
print("Response:")
print(raw1)

# Test prompt 2: Market Question with concise context
p2 = """You are Vibe Trader AI Assistant. Use this factual context to answer concisely.
CONTEXT:
- Instrument: RELIANCE (NSE, 1D)
- Close: ₹2956.64 (-0.97%)
- RSI (14): 48.26 (Neutral)
- Strategy Signal: HOLD (Confidence 65%)

Question: What is the RSI and strategy signal on RELIANCE?
Answer:"""

print("\n--- Test Prompt 2: Market Question ---")
t0 = time.perf_counter()
req2 = urllib.request.Request(
    f"{ollama_base}/api/generate",
    data=json.dumps({
        "model": "qwen3-local:latest",
        "prompt": p2,
        "stream": False,
        "keep_alive": "60m",
        "options": {
            "temperature": 0.3,
            "num_predict": 200,
        }
    }).encode(),
    headers={"Content-Type": "application/json"}
)
res2 = json.loads(urllib.request.urlopen(req2, timeout=60).read().decode())
dur2 = (time.perf_counter() - t0) * 1000
raw2 = res2.get("response", "")
eval_cnt2 = res2.get("eval_count", 0)
eval_dur2 = res2.get("eval_duration", 0) / 1e6
tok_s2 = (eval_cnt2 / (eval_dur2 / 1000)) if eval_dur2 > 0 else 0
print(f"Prompt 2 total time: {dur2:.1f}ms ({dur2/1000:.2f}s)")
print(f"Tokens: {eval_cnt2} generated @ {tok_s2:.2f} tok/s")
print(f"Has <think>: {'<think>' in raw2}, Has </think>: {'</think>' in raw2}")
print("Response:")
print(raw2)
