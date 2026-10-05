import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("==================================================")
print("     OLLAMA / QWEN DIAGNOSTIC & BENCHMARK")
print("==================================================")

ollama_base = "http://127.0.0.1:11434"

# 1. Connectivity check
try:
    req = urllib.request.urlopen(f"{ollama_base}/")
    print(f"1. Ollama Root: HTTP {req.status} ({req.read().decode().strip()})")
except Exception as e:
    print(f"1. Ollama Root FAILED: {e}")
    sys.exit(1)

# 2. Installed models list
try:
    req = urllib.request.urlopen(f"{ollama_base}/api/tags")
    tags = json.loads(req.read().decode())
    models = [m['name'] for m in tags.get('models', [])]
    print(f"2. Installed Models in Ollama: {models}")
    for m in tags.get('models', []):
        size_gb = m.get('size', 0) / (1024**3)
        print(f"   - {m['name']}: {size_gb:.2f} GB, modified: {m.get('modified_at')}")
except Exception as e:
    print(f"2. Error fetching tags: {e}")

# 3. Running / Loaded models in RAM (api/ps)
try:
    req = urllib.request.urlopen(f"{ollama_base}/api/ps")
    ps = json.loads(req.read().decode())
    running = [m['name'] for m in ps.get('models', [])]
    print(f"3. Currently Loaded Models in RAM (/api/ps): {running}")
    for m in ps.get('models', []):
        vram_mb = m.get('size_vram', 0) / (1024**2)
        total_mb = m.get('size', 0) / (1024**2)
        print(f"   - {m['name']}: size={total_mb:.1f}MB, vram={vram_mb:.1f}MB, expires_at={m.get('expires_at')}")
except Exception as e:
    print(f"3. Error fetching ps: {e}")

# 4. Direct Inference Test with detailed timing metrics
model_to_test = "qwen3-local:latest"
if model_to_test not in models and models:
    model_to_test = models[0]
print(f"\n4. Benchmarking direct inference on: '{model_to_test}'")

test_prompts = [
    {
        "name": "Short General Greeting",
        "prompt": "User: Hello! Who are you?\nAssistant:",
        "num_predict": 60,
    },
    {
        "name": "Short Market Question",
        "prompt": "Context: RELIANCE close price is 2956.64, RSI is 48.26.\nUser: What is the RSI on RELIANCE?\nAssistant:",
        "num_predict": 100,
    }
]

for tp in test_prompts:
    print(f"\n--- Testing '{tp['name']}' (num_predict={tp['num_predict']}) ---")
    payload = {
        "model": model_to_test,
        "prompt": tp["prompt"],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": tp["num_predict"],
        },
        "keep_alive": "15m"  # Keep model in RAM for 15 minutes!
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{ollama_base}/api/generate", data=data, headers={"Content-Type": "application/json"})
    
    t0 = time.perf_counter()
    try:
        res = urllib.request.urlopen(req, timeout=60)
        dur = (time.perf_counter() - t0) * 1000
        res_data = json.loads(res.read().decode())
        
        load_dur = res_data.get("load_duration", 0) / 1e6
        prompt_eval_dur = res_data.get("prompt_eval_duration", 0) / 1e6
        eval_dur = res_data.get("eval_duration", 0) / 1e6
        eval_count = res_data.get("eval_count", 0)
        tok_per_sec = (eval_count / (eval_dur / 1000)) if eval_dur > 0 else 0
        
        raw_response = res_data.get("response", "")
        print(f"   Total Wall Time: {dur:.1f}ms ({dur/1000:.2f}s)")
        print(f"   Model Load Time: {load_dur:.1f}ms")
        print(f"   Prompt Eval Time: {prompt_eval_dur:.1f}ms")
        print(f"   Token Generation Time: {eval_dur:.1f}ms ({eval_count} tokens generated @ {tok_per_sec:.2f} tok/s)")
        print(f"   Output preview ({len(raw_response)} chars):")
        print(f"   {raw_response[:200]}...")
    except Exception as e:
        print(f"   Inference failed or timed out: {e}")

print("\n==================================================")
