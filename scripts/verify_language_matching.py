"""Strict Language Matching Verification Script for Vibe Trader AI.
Tests live HTTP endpoints for English-to-English and Tanglish-to-Tanglish responses.
Verifies:
1. English Greeting -> English response
2. Tanglish Greeting -> Tanglish response (Roman script only)
3. English Capabilities -> English capabilities description
4. Tanglish Capabilities -> Tanglish capabilities description
5. English Technical/General Query -> English Qwen explanation
6. Tanglish Technical/General Query -> Tanglish Qwen explanation (Roman script only)
7. English Market Query -> English grounded data & analysis
8. Tanglish Market Query -> Tanglish grounded data & analysis
9. Multi-turn continuity: Tanglish -> Ambiguous (retains Tanglish) -> English switch (switches immediately) -> Ambiguous (retains English)
10. Strict invariant: Zero Tamil script ([\u0B80-\u0BFF]) across all Tanglish responses.
"""
import json
import re
import sys
import uuid
import httpx

API_BASE = "http://127.0.0.1:8000/api/assistant"
TAMIL_SCRIPT_REGEX = re.compile(r"[\u0B80-\u0BFF]")

def run_test():
    client = httpx.Client(timeout=60.0)
    print("=" * 70)
    print("VIBE TRADER AI — STRICT LANGUAGE-MATCHING VERIFICATION")
    print("=" * 70)

    # 1. Check Assistant Status
    status_resp = client.get(f"{API_BASE}/status")
    assert status_resp.status_code == 200, f"Status check failed: {status_resp.status_code}"
    status_data = status_resp.json()
    print(f"[*] Assistant Status: {status_data['status']} | Active Model: {status_data['active_model']}")

    passed = 0
    total = 0

    def assert_test(name: str, condition: bool, details: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name} {details}")
        else:
            print(f"  [FAIL] {name} {details}")
            raise AssertionError(f"Test failed: {name} - {details}")

    session_id = f"lang-test-{uuid.uuid4().hex[:8]}"

    # TEST 1: English Greeting
    print("\n--- TEST 1: English Greeting ('hi') ---")
    payload = {"session_id": session_id, "message": "hi"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:120]}...")
    assert_test("Detected language is english", data.get("detected_language") == "english", f"got {data.get('detected_language')}")
    assert_test("Greeting is in English", "Hello!" in data["content"] or "help you" in data["content"])
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 2: Tanglish Greeting
    print("\n--- TEST 2: Tanglish Greeting ('vanakkam, epdi irukinga?') ---")
    session_id_2 = f"lang-test-{uuid.uuid4().hex[:8]}"
    payload = {"session_id": session_id_2, "message": "vanakkam, epdi irukinga?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:120]}...")
    assert_test("Detected language is tanglish", data.get("detected_language") == "tanglish", f"got {data.get('detected_language')}")
    assert_test("Greeting is in Tanglish", "Vanakkam!" in data["content"] or "ungaloda" in data["content"])
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 3: English Capabilities
    print("\n--- TEST 3: English Capabilities ('What can you do?') ---")
    payload = {"session_id": session_id, "message": "What can you do?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:120]}...")
    assert_test("Detected language is english", data.get("detected_language") == "english")
    assert_test("Describes capabilities in English", "Market Data" in data["content"] or "Technical Indicators" in data["content"])
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 4: Tanglish Capabilities
    print("\n--- TEST 4: Tanglish Capabilities ('unnaala enna panna mudiyum?') ---")
    session_id_4 = f"lang-test-{uuid.uuid4().hex[:8]}"
    payload = {"session_id": session_id_4, "message": "unnaala enna panna mudiyum?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:120]}...")
    assert_test("Detected language is tanglish", data.get("detected_language") == "tanglish")
    assert_test("Describes capabilities in Tanglish", "copilot" in data["content"] or "kekkalam" in data["content"] or "mudiyum" in data["content"])
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 5: English General / Technical Qwen response
    print("\n--- TEST 5: English Technical Question ('Why is risk management important in trading?') ---")
    payload = {"session_id": session_id, "message": "Why is risk management important in trading?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:150]}...")
    assert_test("Detected language is english", data.get("detected_language") == "english")
    assert_test("Response discusses risk in English", "risk" in data["content"].lower() or "capital" in data["content"].lower())
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 6: Tanglish General / Technical Qwen response
    print("\n--- TEST 6: Tanglish Technical Question ('Trading la risk management yen mukkiyam?') ---")
    payload = {"session_id": session_id_4, "message": "Trading la risk management yen mukkiyam?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:150]}...")
    assert_test("Detected language is tanglish", data.get("detected_language") == "tanglish")
    assert_test("Preserves technical terms in Roman script", "risk" in data["content"].lower() or "loss" in data["content"].lower() or "capital" in data["content"].lower())
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 7: English Market Analysis ('What is the RSI on RELIANCE?')
    print("\n--- TEST 7: English Market Analysis ('What is the RSI on RELIANCE?') ---")
    payload = {"session_id": session_id, "message": "What is the RSI on RELIANCE?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:150]}...")
    assert_test("Detected language is english", data.get("detected_language") == "english")
    assert_test("Mentions RELIANCE or has symbol context", "RELIANCE" in data["content"] or data.get("symbol_context") == "RELIANCE")
    assert_test("Contains RSI data", "RSI" in data["content"].upper() or "48." in data["content"])
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 8: Tanglish Market Analysis ('RELIANCE rsi epdi irukku?')
    print("\n--- TEST 8: Tanglish Market Analysis ('RELIANCE rsi epdi irukku?') ---")
    payload = {"session_id": session_id_4, "message": "RELIANCE rsi epdi irukku?"}
    r = client.post(f"{API_BASE}/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"Response: {data['content'][:150]}...")
    assert_test("Detected language is tanglish", data.get("detected_language") == "tanglish")
    assert_test("Mentions RELIANCE or has symbol context", "RELIANCE" in data["content"] or data.get("symbol_context") == "RELIANCE")
    assert_test("Contains RSI data", "RSI" in data["content"].upper() or "48." in data["content"])
    assert_test("Zero Tamil script", not TAMIL_SCRIPT_REGEX.search(data["content"]))

    # TEST 9: Multi-turn Continuity and Immediate Language Switching
    print("\n--- TEST 9: Multi-turn Continuity & Immediate Switching ---")
    turn_session = f"turn-test-{uuid.uuid4().hex[:8]}"

    # Turn 9.1: Tanglish request
    print(" Turn 9.1: Tanglish message ('TCS trend sollunga')")
    r1 = client.post(f"{API_BASE}/chat", json={"session_id": turn_session, "message": "TCS trend sollunga"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert_test("Turn 9.1 detected tanglish", d1.get("detected_language") == "tanglish")
    assert_test("Turn 9.1 zero Tamil script", not TAMIL_SCRIPT_REGEX.search(d1["content"]))

    # Turn 9.2: Ambiguous message (should retain Tanglish)
    print(" Turn 9.2: Ambiguous message ('TCS 1D')")
    r2 = client.post(f"{API_BASE}/chat", json={"session_id": turn_session, "message": "TCS 1D"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert_test("Turn 9.2 retains tanglish context", d2.get("detected_language") == "tanglish")
    assert_test("Turn 9.2 zero Tamil script", not TAMIL_SCRIPT_REGEX.search(d2["content"]))

    # Turn 9.3: Immediate switch to English
    print(" Turn 9.3: Switch to English ('What about RELIANCE?')")
    r3 = client.post(f"{API_BASE}/chat", json={"session_id": turn_session, "message": "What about RELIANCE?"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert_test("Turn 9.3 immediately switched to english", d3.get("detected_language") == "english")
    assert_test("Turn 9.3 zero Tamil script", not TAMIL_SCRIPT_REGEX.search(d3["content"]))

    # Turn 9.4: Ambiguous message after English (should retain English)
    print(" Turn 9.4: Ambiguous message ('RELIANCE 1D')")
    r4 = client.post(f"{API_BASE}/chat", json={"session_id": turn_session, "message": "RELIANCE 1D"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert_test("Turn 9.4 retains english context", d4.get("detected_language") == "english")

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} checks PASSED successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
