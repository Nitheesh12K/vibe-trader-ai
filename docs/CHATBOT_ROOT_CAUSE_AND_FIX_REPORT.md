# Chatbot root cause and fix report

Validation date: 2026-10-04, Asia/Calcutta.

## Actual architecture

Existing React 18/TypeScript/Vite frontend, floating `MarketAssistantChat`, typed API service and React-node-only `SafeMarkdown`; FastAPI synchronous chat endpoints (run in FastAPI's worker thread pool), SQLAlchemy/SQLite chat persistence; existing Ollama provider with local `qwen3-local:latest`; deterministic strategy/indicators/patterns, XGBoost research, portfolio and Risk Guardian services. MarketDataService supplies synthetic OHLC or uploaded CSV, not a verified live broker feed. Broker integration remains read-only, paper trading and approval controls unchanged.

Request path: floating chat → `/api/assistant/chat` → language/intent routing → selected read-only tools → bounded Qwen generation → output checks/fallback → persisted response → safe formatted rendering. Greeting, capabilities and clarification use built-in responses.

The working folder has no `.git` metadata (`git status` reports not a repository), and no AGENTS.md was found outside dependency folders. A Git diff and uncommitted-change attribution were therefore unavailable. Existing functionality and files were inspected before edits; no project/model was replaced. The Python environment reports some canonical paths under an older scratch location; commands were run from the supplied D: workspace.

## Verified causes and changes

| Reported issue | Evidence and resolution | Status |
| --- | --- | --- |
| Hi returns market analysis | Existing fast path already isolated tools; shortened its verbose capability dump to a natural greeting. Active NIFTY context cannot leak into greetings. | PASS — VERIFIED |
| Definitions invoke tools | Existing stock-market/RSI examples already skipped tools. Portfolio/risk keyword precedence still routed definitions to account tools; definitions now precede account terms. | PASS — VERIFIED |
| Instrument mention triggers analysis | Router treated any known symbol as analysis, including coding requests; price requests selected all five tools. Require analysis/live intent and select required groups. | PASS — VERIFIED |
| Strategy explanation invents context | Recomputed hard-coded Multi-Confirmation/NIFTY signal. Now read original saved BuyProposal evidence; ask for identifying details when none is available. | PASS — VERIFIED |
| Qwen offline/timeout | Daemon/model exist. Direct warm generation succeeded; website timeout reproduced during competing test/model load. Previously short health checks and new HTTP clients can add overhead. Preserve bounded 50s timeout, compact prompts, 4K context, no thinking, keep-alive, pooled inference connection and 250ms admission bound. Historical 15s timeout cause cannot be established from retained evidence. | PARTIAL — SOME CHECKS PASSED |
| Irrelevant fallback | Generic education/capability template used for arbitrary questions. Unknown general/educational questions now receive an actionable unavailable response; only supported saved educational definitions are used. | PASS — VERIFIED |
| Misleading provenance | Built-in answers previously called AI_ASSISTANT; now BUILTIN_ASSISTANT, displayed separately from Qwen and fallback. Fallback no longer implies all content is verified market data. | PASS — VERIFIED |
| Markdown | Bold/headings already worked; fenced code, tables and ordered lists were missing. Added safe React rendering for those constructs. | PASS — VERIFIED |
| English/Tanglish | Removed English “bro” and broad suffix false positives, kept vocabulary and finance suffixes, retained immediate explicit language switches. Tamil-script generation is rejected to a labelled Roman-letter fallback. | PARTIAL — SOME CHECKS PASSED |
| Current-market claims | Generated/CSV sources could appear current. Now force live-unavailable disclosure, carry source/time/age, reject malformed/out-of-order bars and CSV timeframe mismatches, reject unsupported generated numerical claims. | PASS — VERIFIED |

## Changed implementation and verification files

- `backend/app/services/market_assistant_service.py`: routing, tool planning, source availability, saved signals, inference pooling/admission, validation and relevant fallbacks.
- `backend/app/services/indicators_service.py`: reuse formulas for selected indicator groups.
- `backend/app/services/market_data_service.py`: preserve uploaded dataset timeframe.
- `backend/app/core/config.py`: configurable chat host/model/timeout.
- `backend/app/api/v1/assistant.py`: safe client error without exception details.
- `backend/main.py`: close pooled inference client on shutdown.
- `frontend/src/components/assistant/MarketAssistantChat.tsx`: neutral/relevant loading, immediate-send guard, history race protection, provenance wording.
- `frontend/src/components/assistant/SafeMarkdown.tsx`: safe tables, code fences and ordered lists.
- Backend chatbot tests and new `test_chat_routing_regressions.py`; frontend chat/Markdown regression tests.
- `scripts/benchmark_chat.py`, `benchmark_ollama_chat.py`, `run_backend_offline_tests.py`; the five requested reports and raw validation artifacts.

## Validation

Baseline chatbot tests: 15 passed, 4 failed. Baseline frontend: 42 passed.
Final backend suite: **323 passed, 1 skipped**, with Ollama health explicitly mocked offline; tests with explicit model mocks still execute. Final frontend: **45 passed**. Production TypeScript/Vite build passed; existing large JS chunk warning remains.
Real Qwen and browser results are separately recorded in WEBSITE_AI_INTEGRATION_TEST_REPORT.md. No live-feed test is claimed.

Commands: `git status --short`; scoped `rg`/PowerShell source inspection; `backend/venv/Scripts/python.exe -m pytest tests/backend/test_market_assistant.py -q --disable-warnings`; regression pytest; `scripts/run_backend_offline_tests.py` with isolated DATABASE_URL; `npm.cmd test -- --run`; `npm.cmd run build`; before/after `scripts/benchmark_chat.py`; uvicorn and Vite startup; actual browser sends; real `/api/tags`, `/api/ps` and `/api/generate` probes. Raw logs and JSON are adjacent to this report.

## Limits

PARTIAL — SOME CHECKS PASSED: Buffered chat API remains non-streaming. A streaming model probe is separate from end-to-end UI streaming. Closing the window does not cancel server inference; requests remain bounded and cannot execute trades. Admission protection is process-local, not a global Ollama scheduler, so other applications/worker processes can still compete. Model factual and Tanglish fluency quality is not guaranteed by output/schema checks. Authentication is the existing localhost single-user design, not certified multi-user isolation. No trading safety/auth controls were weakened.

NOT TESTED — ENVIRONMENT OR ACCESS LIMITATION: controlled unloaded-model cold start, OS RAM/CPU utilization via CIM (access denied), comprehensive mobile browser/device matrix, live broker data, exhaustive natural-language routing coverage.

BLOCKED — REQUIRES USER ACTION: genuinely current-market analysis requires a configured authorized live feed. Multi-user hosting requires a separate authentication/authorization design; keep the existing deployment bound to localhost.

Final checks also reject wrong-language and repeated generated sentences. Final full offline suite: 323 passed, 1 skipped, 12 warnings in 26.96s. Existing README/architecture mention other older model names (deepseek/llama); discovered chatbot code and installed model establish Qwen as the actual chat integration.

Real recovery subsequently passed: general English Qwen conversation completed in 10.305s with zero tools; actual close/reopen preserved history. Wrong-language, degeneracy and status-copying model outputs are now rejected. Qwen Tanglish generation remains unreliable despite safe fallback behavior.
