"""End-to-End Smart Intent Routing & Latency Verification Script for Vibe Trader AI."""
import json
import re
import sys
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"

TEST_CASES = [
    {
        "name": "Educational - Stock Market Definition",
        "message": "What is stock market?",
        "expected_intent": "EDUCATIONAL",
        "expected_tool_count": 0,
        "disallowed_tools": ["MarketDataTool", "TechnicalIndicatorsTool", "PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Educational - RSI Explanation",
        "message": "Explain RSI.",
        "expected_intent": "EDUCATIONAL",
        "expected_tool_count": 0,
        "disallowed_tools": ["MarketDataTool", "TechnicalIndicatorsTool", "PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Educational - NIFTY 50 Definition",
        "message": "What is NIFTY 50?",
        "expected_intent": "EDUCATIONAL",
        "expected_tool_count": 0,
        "disallowed_tools": ["MarketDataTool", "TechnicalIndicatorsTool", "PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Educational - Tanglish Stock Market",
        "message": "Stock market na enna?",
        "expected_intent": "EDUCATIONAL",
        "expected_tool_count": 0,
        "disallowed_tools": ["MarketDataTool", "TechnicalIndicatorsTool", "PaperPortfolioTool"],
        "expected_language": "tanglish",
    },
    {
        "name": "Market Overview - Benchmark Status",
        "message": "What is the market doing right now?",
        "expected_intent": "MARKET_OVERVIEW",
        "expected_tool_count": 1,
        "required_tools": ["MarketDataTool"],
        "disallowed_tools": ["PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Instrument Analysis - RELIANCE",
        "message": "Analyze RELIANCE",
        "expected_intent": "INSTRUMENT_ANALYSIS",
        "min_tool_count": 4,
        "required_tools": ["MarketDataTool", "TechnicalIndicatorsTool", "StrategySignalsTool"],
        "disallowed_tools": ["PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Technical Analysis - RSI on Instrument",
        "message": "What is the RSI on RELIANCE?",
        "expected_intent": "TECHNICAL_ANALYSIS",
        "required_tools": ["MarketDataTool", "TechnicalIndicatorsTool"],
        "disallowed_tools": ["PaperPortfolioTool", "StrategySignalsTool"],
        "expected_language": "english",
    },
    {
        "name": "Strategy Explanation - Algorithmic Logic",
        "message": "Why did my strategy generate BUY?",
        "expected_intent": "STRATEGY_EXPLANATION",
        "required_tools": ["StrategySignalsTool"],
        "disallowed_tools": ["PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Portfolio Analysis - Equity & Positions",
        "message": "What is my portfolio equity?",
        "expected_intent": "PORTFOLIO_ANALYSIS",
        "expected_tool_count": 1,
        "required_tools": ["PaperPortfolioTool"],
        "disallowed_tools": ["MarketDataTool", "TechnicalIndicatorsTool", "StrategySignalsTool"],
        "expected_language": "english",
    },
    {
        "name": "Risk Analysis - Limits & Guardian Status",
        "message": "Analyze my portfolio risk",
        "expected_intent": "RISK_ANALYSIS",
        "expected_tool_count": 2,
        "required_tools": ["PaperPortfolioTool", "RiskGuardianTool"],
        "disallowed_tools": ["TechnicalIndicatorsTool", "StrategySignalsTool"],
        "expected_language": "english",
    },
    {
        "name": "Clarification - Ambiguous Command",
        "message": "Trade",
        "expected_intent": "CLARIFICATION",
        "expected_tool_count": 0,
        "disallowed_tools": ["MarketDataTool", "PaperPortfolioTool"],
        "expected_language": "english",
    },
    {
        "name": "Greeting - Fast Path",
        "message": "hello",
        "expected_intent": "GREETING",
        "expected_tool_count": 0,
        "disallowed_tools": ["MarketDataTool", "PaperPortfolioTool"],
        "expected_language": "english",
    },
]


def run_tests():
    print("=" * 80)
    print("VIBE TRADER AI — SMART INTENT ROUTING & LATENCY BENCHMARK SUITE")
    print("=" * 80)

    client = httpx.Client(timeout=60.0)

    # 1. Health & Status check
    try:
        status_res = client.get(f"{BASE_URL}/api/assistant/status")
        status_data = status_res.json()
        print(f"Assistant Status: {status_data.get('status')} | Active Model: {status_data.get('active_model')}")
        print(f"Available Tools: {status_data.get('available_tools')}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        sys.exit(1)

    print("-" * 80)
    session_id = f"test-sess-{int(time.time())}"
    passed = 0
    failed = 0
    results_summary = []

    tamil_unicode_pattern = re.compile(r"[\u0B80-\u0BFF]")

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"\n[Test {idx}/{len(TEST_CASES)}] {tc['name']}")
        print(f"Query: \"{tc['message']}\"")

        t_req_start = time.perf_counter()
        res = client.post(
            f"{BASE_URL}/api/assistant/chat",
            json={
                "session_id": session_id,
                "message": tc["message"],
                "symbol": "NIFTY 50",
                "market": "NSE",
                "timeframe": "1D",
            },
        )
        roundtrip_ms = round((time.perf_counter() - t_req_start) * 1000, 2)

        if res.status_code != 200:
            print(f"FAILED: HTTP {res.status_code}: {res.text}")
            failed += 1
            continue

        data = res.json()
        detected_intent = data.get("detected_intent")
        detected_lang = data.get("detected_language")
        sources = data.get("sources", [])
        tool_names = [s.get("tool_name") for s in sources]
        content = data.get("content", "")
        is_fallback = data.get("is_fallback")
        model_name = data.get("model_name")

        routing_time_ms = data.get("routing_time_ms", 0.0)
        tool_latency_ms = data.get("tool_latency_ms", 0.0)
        inference_latency_ms = data.get("inference_latency_ms", 0.0)
        total_latency_ms = data.get("total_latency_ms", 0.0)

        # Assertions
        errors = []

        # 1. Intent match
        if detected_intent != tc["expected_intent"]:
            errors.append(f"Intent mismatch: expected {tc['expected_intent']}, got {detected_intent}")

        # 2. Tool count match
        if "expected_tool_count" in tc:
            if len(sources) != tc["expected_tool_count"]:
                errors.append(f"Tool count mismatch: expected {tc['expected_tool_count']}, got {len(sources)} ({tool_names})")
        if "min_tool_count" in tc:
            if len(sources) < tc["min_tool_count"]:
                errors.append(f"Min tool count mismatch: expected >={tc['min_tool_count']}, got {len(sources)}")

        # 3. Disallowed tools
        for dt in tc.get("disallowed_tools", []):
            if dt in tool_names:
                errors.append(f"Disallowed tool '{dt}' was invoked! ({tool_names})")

        # 4. Required tools
        for rt in tc.get("required_tools", []):
            if rt not in tool_names:
                errors.append(f"Required tool '{rt}' was missing! ({tool_names})")

        # 5. Language match
        if detected_lang != tc["expected_language"]:
            errors.append(f"Language mismatch: expected {tc['expected_language']}, got {detected_lang}")

        # 6. Strict Tamil Script check (NEVER allow Tamil script characters)
        if tamil_unicode_pattern.search(content):
            errors.append("Contained forbidden Tamil Unicode characters! Must use English/Roman letters only.")

        if errors:
            print("FAILED assertions:")
            for err in errors:
                print(f"   - {err}")
            failed += 1
        else:
            print("PASSED")
            passed += 1

        print(f"   Intent: {detected_intent} | Language: {detected_lang}")
        print(f"   Tools: {len(sources)} ({', '.join(tool_names) if tool_names else 'None'})")
        print(f"   Latencies: Routing: {routing_time_ms}ms | Tools: {tool_latency_ms}ms | Infer: {inference_latency_ms}ms | Total: {total_latency_ms}ms | Roundtrip: {roundtrip_ms}ms")
        print(f"   Model: {model_name} (Fallback: {is_fallback})")
        first_line = content.split('\n')[0][:100]
        print(f"   Preview: {first_line}...")

        results_summary.append({
            "test": tc["name"],
            "query": tc["message"],
            "intent": detected_intent,
            "tool_count": len(sources),
            "tools": tool_names,
            "routing_time_ms": routing_time_ms,
            "tool_latency_ms": tool_latency_ms,
            "inference_latency_ms": inference_latency_ms,
            "total_latency_ms": total_latency_ms,
            "model": model_name,
            "passed": len(errors) == 0,
        })

    # 2. Check history retrieval
    print("\n" + "-" * 80)
    print("Testing Conversation History Retrieval...")
    hist_res = client.get(f"{BASE_URL}/api/assistant/history/{session_id}")
    if hist_res.status_code == 200:
        hist_items = hist_res.json()
        print(f"✅ History retrieved successfully: {len(hist_items)} total turns in session.")
        sample_item = hist_items[-1] if hist_items else None
        if sample_item:
            print(f"   Sample turn: Intent={sample_item.get('detected_intent')} | Tools={len(sample_item.get('sources', []))} | Total Latency={sample_item.get('total_latency_ms')}ms")
    else:
        print(f"❌ Failed to retrieve history: HTTP {hist_res.status_code}")

    print("\n" + "=" * 80)
    print(f"FINAL TEST SUMMARY: {passed} PASSED, {failed} FAILED (Total: {len(TEST_CASES)})")
    print("=" * 80)

    # Save benchmark table JSON for the documentation report
    with open("smart_routing_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print("Benchmark results saved to smart_routing_benchmark_results.json")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
