# Website AI integration verification

Date: 2026-10-04 (Asia/Calcutta). Actual Vite website at http://127.0.0.1:5173 with FastAPI at localhost:8000. Verified with the connected browser through the floating chat, not just TestClient. No browser request interception or model response mocking was used for these observations.

| Website check | Observed result | Status |
| --- | --- | --- |
| Open floating chat | Opens with active NIFTY context and input | PASS — VERIFIED |
| Hi | Built-in greeting, GREETING, zero tools and zero inference | PASS — VERIFIED |
| What is stock market? under competing test load | 51.997s timeout; clearly labelled saved educational fallback, zero tools, formatted text | PASS — VERIFIED (failure handling) |
| What is stock market? after compact prompt | Actual Local Qwen answer; EDUCATIONAL; zero tools; 12.540s total | PASS — VERIFIED |
| Explain RSI | Actual Local Qwen answer; EDUCATIONAL; zero tools; 37.088s total before final prompt reduction | PASS — VERIFIED |
| What's happening in NIFTY right now? | Actual Local Qwen answer; one MarketDataTool source; live unavailable and simulated-data disclosure; 39.185s total | PASS — VERIFIED |
| Why did our strategy generate a BUY signal? | Missing identifiable NIFTY proposal → built-in clarification, no fabricated signal, 0.748s | PASS — VERIFIED |
| Stock market na enna? under load | Tanglish saved educational fallback in Roman letters, zero tools, explicitly labelled | PASS — VERIFIED (failure handling) |

Further final-model/language/offline checks are recorded in the verification addendum and chat JSON artifact. UI shows submitted messages immediately, disables duplicate submission, displays appropriate loading, safely formats headings/bold/lists, and distinguishes built-in/Qwen/fallback. Existing frontend test coverage plus added regressions verify opening, closing, sends, duplicate guard, error/retry and safe table/code rendering.

Automated baseline: frontend 42 passes; backend chat 15 passes/4 failures. Final frontend: 45 passes; final backend: 323 passes/1 conditional real-model skip, explicitly mocked offline. These suite results are not real model connectivity claims. Production build passes with a large-chunk warning. Raw logs: frontend_chat_validation.log, frontend_chat_build.log, backend_chat_offline_validation.log.

Safety: chat uses read-only tools, no trade executor or broker order endpoint. Approval/Risk Guardian code was not changed. Full backend safety/risk regression tests ran in the offline suite on isolated SQLite. No actual broker orders were submitted.

PARTIAL — SOME CHECKS PASSED: the real model's earlier RSI answer included a debatable claim about trending/ranging effectiveness; natural-language factual quality still requires review. Browser tests verify the request flow and provenance, not perfect financial education. Buffering remains; no UI streaming or server-side cancellation is claimed. Mobile/responsive styling was preserved but an exhaustive device matrix was not run. Live market tests are NOT TESTED — ENVIRONMENT OR ACCESS LIMITATION because this chat provider has no verified live feed.

## Verification addendum

Real Tanglish inference exposed two model-quality defects: a 16.097s answer repeated the question then answered in English, and a 30.202s answer repeated a nonsensical phrase. These observations caused additional output-language and repetitive-output rejection, tested automatically. Stronger Tanglish prompt examples were added. Status: PARTIAL — SOME CHECKS PASSED for generated Tanglish; safe saved Tanglish fallback is verified. Perfect Qwen Tanglish fluency is not claimed.

The real offline website check used a temporary backend-only CHAT_OLLAMA_HOST pointing to the unreachable localhost:11435. Ollama itself was not stopped or changed, and no network/model mocks were injected. General coding query returned a clearly labelled relevant unavailable response with zero tools in ~0.997s. That check also exposed ambiguous English technical vocabulary inheriting the prior Tanglish language, so explicit English coding markers and a switching regression were added. The service is restored to its normal configured host after this check.

Final market availability path now returns a built-in, explicitly identified availability response when only demo/history is available for a live question. It skips both model health and inference. The earlier actual generated NIFTY result above documents the source/disclosure test, not the final no-inference timing.

Explicit English casual query during the unreachable-endpoint test returned English unavailable text, zero tools, and an explicit fallback label in 1.218s. Manual Refresh Status was exercised. Backend restored to localhost:11434 without altering .env or stopping/downloading the model.

Final website live-NIFTY check: BUILTIN_ASSISTANT, one market source, explicit historical/demo/source timestamp, 33ms backend total, 11.34ms tools, 0.64ms availability response stage. Ollama health/generation skipped. This is availability handling, not a successful live-market analysis.

Recovery initially returned copied unavailable text with a Qwen label in 13.235s. This was a real defect, not a successful recovery claim; history filtering and status-output rejection were added and validated by regressions. Final backend suite: 323 passed, 1 skipped, 12 warnings; focused chat regression suite: 40 passed.

Final real Tanglish market query: natural Roman-letter availability explanation, one source, BUILTIN_ASSISTANT, 31ms total; no inference. Persisted browser test messages and stage metrics are retained in website_chat_observations.json, including intermediate defects instead of hiding failed attempts.

Final real recovery PASS — VERIFIED: “How are you?” returned a natural English Qwen response after status history filtering, GENERAL_CHAT, zero sources/tools, 10.305s backend total, 10.289s inference stage. Actual Close and Reopen preserved conversation and the completed answer. Backend localhost:8000 and frontend localhost:5173 were left running with the normal Ollama host.
