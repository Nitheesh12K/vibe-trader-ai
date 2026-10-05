# Chat performance optimization

PASS — VERIFIED: price-only queries now invoke one tool rather than five; saved-signal clarification does not compute market indicators. Definitions and general questions invoke zero market/account tools. RSI-only calculation skips unrelated MACD/ATR. Duplicate history query removed; history/context/output bounded. Prompt reduced from repeated instruction blocks to concise intent/language rules. Inference connection pooled, keep-alive maintained, and concurrent generation admission bounded at 250ms. No trading safety controls, credentials, freshness rules or approval gates were weakened.

## Repeatable offline comparison

Run `backend/venv/Scripts/python.exe scripts/benchmark_chat.py --output docs/chat_benchmark_after.json`. Ten sequential runs for each identical input, fresh in-memory SQLite database. Real routing/SQLite/tools; only Ollama health mocked OFFLINE. This measures deterministic flow, not Qwen speed or browser network latency. Raw before/after samples, tool counts and route/tool/inference timings are in chat_benchmark_before.json and chat_benchmark_after.json.

| Input | Before median / p95 ms | After median / p95 ms |
| --- | --- | --- |
| Hi | 1.12 / 18.03 | 2.49 / 35.77 |
| What is stock market? | 1.46 / 2.44 | 3.09 / 7.84 |
| Explain RSI | 1.53 / 2.74 | 2.74 / 5.20 |
| NIFTY right now | 12.15 / 193.61 | 6.18 / 311.14 |
| Why our strategy BUY? | 11.91 / 12.74 | 3.53 / 5.41 |

Median work fell for the two formerly expensive analytical routes. Small general-route timings rose under differing host load; no universal speed improvement is claimed. First-use data imports dominate NIFTY p95; ten samples provide only a coarse p95 estimate. No separate SQL query timing instrument was installed; wall minus response stages is not presented as measured database latency.

## Real model observations

Existing installed Qwen: 4.0B, Q4_K_M; model file approximately 2.50GB, loaded allocation approximately 3.18GB, GPU allocation zero. Windows CPU identifier: Intel64 Family 6 Model 154 Stepping 4, 12 logical processors. CIM CPU/RAM inventory access denied; utilization/physical RAM are NOT TESTED — ENVIRONMENT OR ACCESS LIMITATION.

Real direct warm RSI probe: 8190.30ms wall, 7.14ms model load, 515.56ms prompt evaluation, 7255.10ms token evaluation, 78 generated tokens (~10.75 tokens/s), stopped normally. This was a short direct prompt, not an equivalent full chat benchmark.

Actual website: compact stock-market answer 12540ms, prior verbose RSI prompt 37088ms, NIFTY grounded answer 39185ms. A loaded/contended website request timed out at 51997ms. Different inputs/loads are not paired latency evidence. The retained 50s bound is supported by observed successful ~37–39s runs; the reported old 15s configuration was not reproduced in current source.

`scripts/benchmark_ollama_chat.py` provides repeated actual streaming transport probes with TTFT, server load/prompt/token timings, tokens/s, model allocation, raw answers and wall median/p95. Streaming probe results do not imply the buffered website supports streaming. Controlled cold-start measurements are NOT TESTED; the model was already resident, and it was not unloaded just to benchmark. No fixed response-time promise is made.

PARTIAL — SOME CHECKS PASSED: UI API remains buffered and response speed depends on CPU/model/other Ollama clients. Process-local admission cannot prevent inference load from unrelated application modules or other processes. Frontend retains an approximately 872KB JS bundle warning; unrelated app-wide code splitting was not undertaken.

Final availability optimization: when a live request has only historical/demo sources, return a clearly identified built-in availability response immediately. Qwen cannot create missing live data. Mixed educational requests can still use Qwen with the relevant context. Strategy clarification also skips model health/inference.

Real repeated streaming probe (3 warm sequential runs): median 13671.89ms; coarse p95/max 23076.46ms. TTFT values: 926.51ms, 325.90ms, 391.67ms. Tokens/s: 3.94, 3.35, 3.31. Raw data: ollama_chat_benchmark.json. No controlled paired real-model before/after claim is made. Some probes overlapped offline CPU regression work, so these numbers include host contention.
