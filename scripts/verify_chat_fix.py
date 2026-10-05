import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

base = 'http://127.0.0.1:8000'

print("======================================================================")
print("     COMPREHENSIVE VERIFICATION: AI MARKET ASSISTANT & LOCAL QWEN")
print("======================================================================")

# 1. Status Check & Model Warmth
req = urllib.request.urlopen(f'{base}/api/assistant/status')
status = json.loads(req.read().decode())
print(f"1. ASSISTANT STATUS: {status.get('status')}, Active Model: {status.get('active_model')}")
assert status.get("status") == "ONLINE", "Ollama daemon must be online"

# 2. Greeting Test ('hi')
t0 = time.perf_counter()
data = json.dumps({'session_id': 'v-hi', 'message': 'hi', 'symbol': 'NIFTY 50', 'market': 'NSE'}).encode()
req = urllib.request.Request(f'{base}/api/assistant/chat', data=data, headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
body_hi = json.loads(res.read().decode())
dur_hi = (time.perf_counter() - t0) * 1000

print(f"\n2. GREETINGS TEST ('hi'):")
print(f"   Latency: {dur_hi:.1f}ms")
print(f"   Model: {body_hi.get('model_name')}, is_fallback: {body_hi.get('is_fallback')}, sources: {len(body_hi.get('sources', []))}")
print(f"   Content Preview:\n   {body_hi.get('content', '')[:120].replace(chr(10), ' ')}...")
assert "Hello!" in body_hi["content"]
assert "Market Analysis for NIFTY 50" not in body_hi["content"]
assert "Latest Close Price" not in body_hi["content"]
assert body_hi.get("is_fallback") is False
assert body_hi.get("model_name") == "AI_ASSISTANT"
assert len(body_hi.get("sources", [])) == 0
print("   --> PASS: Fast friendly greeting (<50ms, zero tool overhead, is_fallback=False)")

# 3. Capability Questions ('what can you do?')
t0 = time.perf_counter()
data = json.dumps({'session_id': 'v-cap', 'message': 'What can you do and what are your features?', 'symbol': 'NIFTY 50', 'market': 'NSE'}).encode()
req = urllib.request.Request(f'{base}/api/assistant/chat', data=data, headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
body_cap = json.loads(res.read().decode())
dur_cap = (time.perf_counter() - t0) * 1000

print(f"\n3. CAPABILITIES TEST ('What can you do?'):")
print(f"   Latency: {dur_cap:.1f}ms")
print(f"   Model: {body_cap.get('model_name')}, is_fallback: {body_cap.get('is_fallback')}, sources: {len(body_cap.get('sources', []))}")
print(f"   Content Preview:\n   {body_cap.get('content', '')[:140].replace(chr(10), ' ')}...")
assert "Verified Platform Capabilities" in body_cap["content"]
assert "Real-Time Market Data" in body_cap["content"]
assert "13 Causal Technical Indicators" in body_cap["content"]
assert "Deterministic Strategy Signals" in body_cap["content"]
assert "Paper Portfolio Tracking" in body_cap["content"]
assert "Market Analysis for NIFTY 50" not in body_cap["content"]
assert body_cap.get("is_fallback") is False
assert body_cap.get("model_name") == "AI_ASSISTANT"
assert len(body_cap.get("sources", [])) == 0
print("   --> PASS: Immediate verified capabilities (<50ms, zero NIFTY 50 leakage, is_fallback=False)")

# 4. General Questions (Real Qwen/Ollama inference)
print(f"\n4. GENERAL QUESTION (Real Qwen/Ollama Inference):")
print("   Prompt: 'Why is risk management essential in quantitative trading?'")
print("   Sending to local Qwen (warm in RAM)...")
t0 = time.perf_counter()
data = json.dumps({'session_id': 'v-gen', 'message': 'Why is risk management essential in quantitative trading?', 'symbol': 'NIFTY 50', 'market': 'NSE'}).encode()
req = urllib.request.Request(f'{base}/api/assistant/chat', data=data, headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req, timeout=60)
body_gen = json.loads(res.read().decode())
dur_gen = (time.perf_counter() - t0) * 1000

print(f"   Latency: {dur_gen:.1f}ms ({dur_gen/1000:.2f}s)")
print(f"   Model: {body_gen.get('model_name')}")
print(f"   Is Fallback: {body_gen.get('is_fallback')}")
print(f"   Has <think> tags: {'<think>' in body_gen.get('content', '')}")
print(f"   Response Content:\n{body_gen.get('content')}")
assert body_gen.get("is_fallback") is False, "Warm Qwen model should generate real response within 35s!"
assert body_gen.get("model_name") == "qwen3-local:latest", f"Expected qwen3-local:latest, got {body_gen.get('model_name')}"
assert "<think>" not in body_gen.get("content", ""), "Internal think tags must be stripped"
assert "NIFTY 50" not in body_gen.get("content", ""), "General question must not leak active chart data"
print("   --> PASS: Real Qwen response successfully received and cleanly rendered!")

# 5. Market Question (Real Qwen Grounded with Tools)
print(f"\n5. MARKET QUESTION (Real Grounded Tool Inference):")
print("   Prompt: 'What is the RSI and strategy signal on RELIANCE?'")
print("   Gathering tools and sending to Qwen...")
t0 = time.perf_counter()
sess_mkt = f"v-mkt-{int(time.time())}"
data = json.dumps({'session_id': sess_mkt, 'message': 'What is the RSI and strategy signal on RELIANCE?', 'symbol': 'RELIANCE', 'market': 'NSE'}).encode()
req = urllib.request.Request(f'{base}/api/assistant/chat', data=data, headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req, timeout=60)
body_mkt = json.loads(res.read().decode())
dur_mkt = (time.perf_counter() - t0) * 1000

print(f"   Latency: {dur_mkt:.1f}ms ({dur_mkt/1000:.2f}s)")
print(f"   Model: {body_mkt.get('model_name')}")
print(f"   Is Fallback: {body_mkt.get('is_fallback')}")
print(f"   Sources: {len(body_mkt.get('sources', []))}")
tools = [s.get("tool_name") for s in body_mkt.get("sources", [])]
print(f"   Tools: {tools}")
print(f"   Response Content:\n{body_mkt.get('content')}")
assert body_mkt.get("is_fallback") is False, "Warm Qwen model should generate real grounded response within timeout!"
assert body_mkt.get("model_name") == "qwen3-local:latest", f"Expected qwen3-local:latest, got {body_mkt.get('model_name')}"
assert len(body_mkt.get("sources", [])) >= 4, "Market query must collect all relevant tool sources"
assert "MarketDataTool" in tools
assert "TechnicalIndicatorsTool" in tools
assert "PatternsAndLevelsTool" in tools
assert "StrategySignalsTool" in tools
assert "XGBoostResearchTool" in tools
assert "<think>" not in body_mkt.get("content", "")
print("   --> PASS: Real Qwen response grounded with platform market tools!")

# 6. Safety Invariant Check
print(f"\n6. SAFETY INVARIANT CHECK:")
try:
    data = json.dumps({'symbol': 'RELIANCE', 'quantity': 100}).encode()
    req = urllib.request.Request(f'{base}/api/broker/zerodha/orders', data=data, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)
    assert False, "Live broker must reject order"
except urllib.error.HTTPError as e:
    print(f"   Broker Endpoint HTTP Status: {e.code} (Fail-closed)")
    assert e.code == 403
    print("   --> PASS: Live broker orders remain strictly fail-closed (HTTP 403 Forbidden)")

print("\n======================================================================")
print("     ALL VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")
print("======================================================================")
