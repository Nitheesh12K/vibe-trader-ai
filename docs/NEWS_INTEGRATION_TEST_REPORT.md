# News integration test report

Date: 2026-10-04. Existing workspace: `D:\nitheesh\vibe-trader-ai`. No project rebuild, new model, new dependencies, database migration or trading/authentication changes.

## Verified results

| Check | Status | Evidence / scope |
| --- | --- | --- |
| Independent baseline backend | PASS — VERIFIED | 323 passed, 1 real-model test skipped; 22.48s; news_backend_baseline.log |
| Independent baseline frontend | PASS — VERIFIED | 45 passed; news_frontend_baseline.log |
| Final full backend | PASS — VERIFIED | 398 passed, 1 skipped, 12 warnings; 40.63s; news_backend_tests.log |
| Final full frontend | PASS — VERIFIED | 60 passed in six files; 11.48s; news_frontend_tests.log |
| TypeScript type check | PASS — VERIFIED | tsc --noEmit, exit 0; news_typecheck.log |
| Production build | PASS — VERIFIED | Vite build completed, 6.66s; existing approximately 874KB bundle warning remains; news_build.log |
| Actual news provider | PASS — VERIFIED | Ollama 0.34.4 local proxy returned real recent NIFTY articles with explicit dates and direct publisher links; repeated provider samples preserved in news_benchmark.json |
| Current fresh provider availability | PARTIAL | Repeated probes reached actual HTTP 429; unavailable state verified, no retry loop and no invented answer |
| Final real English Qwen news path | PASS — VERIFIED | Three HTTP chat requests using previously retrieved real evidence, configured local Qwen, extractive headline selection + tentative interpretation, all non-fallback; news_benchmark_extractive_final.json |
| Real Tanglish Qwen interpretation | PARTIAL | Real probe failed structured-output validation; relevant Roman-letter fallback/headlines retained; news_real_tanglish.json |
| News source cards on actual website | PASS — VERIFIED | Original links, separate publication/retrieval timestamps, real evidence-only fallback and safe Markdown observed through browser controls |
| Actual website greeting | PASS — VERIFIED | Hi returned built-in GREETING in 7ms with zero tools and zero inference |
| Actual rate-limit website state | PASS — VERIFIED | NEWS_CURRENT returned a built-in, actionable provider-rate-limit message in 594ms; no AI-generated news claimed |
| Desktop/mobile error layout | PASS — VERIFIED | Desktop plus 390×844 viewport, controls usable and text wrapped; viewport restored; screenshots saved |
| Final fresh-search + extractive-Qwen success through browser | NOT TESTED | Final browser attempt was rate-limited before inference; final model path independently verified through actual API using prior real evidence |
| Real company/RBI/global provider coverage | NOT TESTED | Company/topic routing tested with mocks; live coverage was not expanded after provider rate limiting |
| Physical Ollama shutdown/recovery | NOT TESTED | Timeout/offline/recovery tests use deterministic mocks; daemon was not stopped |
| Hosted provider live authentication | NOT TESTED | No hosted API key configured; credential/header behavior transport-mock tested |
| Controlled cold model / CPU utilization / physical RAM | NOT TESTED | Model already resident; not unloaded. Windows CIM inventory denied access |
| Git status/diff | BLOCKED | Workspace has no .git metadata; git status returned 'not a git repository'. Snapshot-based unified review diff supplied instead |

The backend offline runner mocks Ollama health only; new news tests explicitly mock provider transport and model replies. The skipped existing test is not counted as a real-model pass. Real provider/model samples and browser observations above are separate from those mocked tests.

## Defects found and resolved

No news service, schemas or source UI existed at the audit. News phrases could fall into educational/general/instrument routing and historical market context could not answer current-news questions. The new route invokes only NewsTool, reuses public topic aliases and skips Qwen entirely when current evidence is absent. Existing right-now price/indicator and strategy routes are preserved.

Search excerpts do not consistently contain usable publication metadata. The service rejects missing/ambiguous/updated-only/stale/future timestamps, malformed or untrusted URLs, duplicates and off-topic results instead of inventing freshness. Cached and reused evidence keeps its original retrieval time; errors/empty results are not successful cache entries. Concurrent identical requests share one provider result; failed flights cannot resurrect expired previous cache entries.

Real model review found numerical conflation: a headline about the longest losing streak *in* twenty-five years was paraphrased as a twenty-five-year losing streak. Early mechanical numeric validation did not catch that semantic error. Prompt-only brevity/quantity instructions and overly restrictive free-form generation also produced invalid or incomplete summaries. Those intermediate responses are diagnostic evidence, not verified final summaries. The final solution constrains summaries to an exact retrieved headline with matching citation; Qwen still generates a separately labelled qualitative, uncertain interpretation. Interpretation validation rejects quantities (including normalized Unicode digits and spelled quantities), certainty, URLs, malformed output and wrong language. The original headline remains in its source language rather than being translated inaccurately.

Actual provider HTTP 429 prompted specific RATE_LIMITED handling. Authentication, timeout, configuration, malformed response and unavailable failures have distinct safe codes/notices. No quota/reset time is invented; 429 is not automatically retried. A UI check also caught and fixed 'New search evidence' wording on empty/error results. News model validation errors now log only the exception category, not generated input/body text that might echo user information.

## Automated coverage

Seventy-five added backend cases cover intent routing, zero tools for greetings/education, company/topic selection and unsupported-topic clarification without searches, structured public queries without account data, successful/empty/irrelevant search, duplicate URLs/headlines, missing/unsafe URLs, publication metadata/timezone/freshness, provider timeout/authentication/rate-limit/recovery/malformed/oversized payloads, TTL/coalescing/concurrent failures, session-isolated follow-ups, model timeout/recovery/citations/unsupported output/language/fallback, no broker order submissions and safe model-error logs.

Fifteen added frontend cases cover news loading without market loading, closing/reopening during pending work, immediate user messages, English/Tanglish response rendering, history/fallback restoration, links/publishers/timestamps/cache labels, unsafe URLs/HTML text and provider/no-results/clarification states. Existing SafeMarkdown, general-chat, retry and website regression tests remain intact.

## Actual timings

Windows 11 10.0.22631; Intel64 Family 6 Model 154 Stepping 4, twelve logical processors. Installed local model: Qwen3 4.0B Q4_K_M. Public news via Ollama local cloud-search proxy; no fabricated market values or mocked provider data in these timing samples. The model was already resident. Each distribution uses nearest-rank p95; three/five samples are coarse observations, not a speed guarantee.

| Measurement | Runs | Median | p95 / maximum |
| --- | --- | --- | --- |
| Router, NIFTY today | 1000 | 0.01ms | 0.01ms |
| Real provider miss | 5 | 978.31ms | 1684.01ms |
| Process-local evidence cache hit | 5 | 0.09ms | 0.32ms |
| Initial implementation HTTP news request, rejected model output | 3 | 23045.61ms | 50037.90ms |
| Final extractive English HTTP follow-up, real reused evidence | 3 | 15687.04ms | 33968.64ms |
| Final model stage including health/admission | 3 | 15651.38ms | 33929.32ms |
| Final Ollama-reported generation total | 3 | 15113.90ms | 33186.77ms |

Final generation had 399 prompt tokens and 62 output tokens in each sample. Prompt evaluation took 17002.55ms on the first changed prompt, then 260.27/279.30ms with the warm prompt cache. Token evaluation took 16037.51/14822.51/14165.70ms, about 3.87/4.18/4.38 output tokens/second. In the initial rejected run, prompt evaluation used 628 tokens and took 27544.74ms; redundant article headers, repeated headlines and metadata were subsequently removed from model context.

These are different prompt/output configurations and fresh-search versus evidence-reuse requests. They do not establish a controlled percentage speed improvement. No news-capable pre-feature baseline existed. The rate-limited run's approximately 367ms median is a skipped-inference error response, not Qwen performance. The earlier constrained-prose reuse run included busy-model fallbacks; it is also not a successful-generation benchmark. No streaming/TTFT or independent database timing was measured in this phase. Source counts, cache flags, original timestamps, prompt/token metrics and complete public outputs are preserved in the JSON artifacts.

## Commands and repeatability

```powershell
git status --short
$env:DATABASE_URL='sqlite:///D:/nitheesh/vibe-trader-ai/data/news_tests.db'
backend/venv/Scripts/python.exe scripts/run_backend_offline_tests.py
backend/venv/Scripts/python.exe scripts/run_backend_offline_tests.py tests/backend/test_news_integration.py -q --disable-warnings
backend/venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
backend/venv/Scripts/python.exe scripts/benchmark_news.py
backend/venv/Scripts/python.exe scripts/benchmark_news.py --provider-runs 0 --reuse-evidence --output docs/news_benchmark_extractive_final.json
backend/venv/Scripts/python.exe scripts/probe_news_model.py
cd frontend
npm.cmd test -- --run
node_modules/.bin/tsc.cmd --noEmit
npm.cmd run build
```

DATABASE_URL above isolates test writes; normal backend uses its existing application database. Real API benchmarks use dedicated `phase7-news-benchmark-*` sessions. `--reuse-evidence` requires previous real evidence in those sessions and does not retrieve fresh news. Re-running real provider benchmarks spends search allowance; prefer mocked suites during normal development. The public diagnostic probe is opt-in and never invoked by the test suite. No secrets are written to reports.

## Files and review

Modified: `.env.example`, `backend/app/core/config.py`, `backend/app/schemas/chat_assistant.py`, `backend/app/services/market_assistant_service.py`, `frontend/src/types/market.ts`, `frontend/src/components/assistant/MarketAssistantChat.tsx`, `frontend/src/MarketAssistantChat.test.tsx`.

Created: `backend/app/schemas/news.py`, `backend/app/services/news_intent.py`, `backend/app/services/news_service.py`, `frontend/src/components/assistant/NewsSources.tsx`, `frontend/src/NewsSources.test.tsx`, `tests/backend/test_news_integration.py`, `scripts/benchmark_news.py`, `scripts/probe_news_model.py`, and the three requested news documents.

`NEWS_IMPLEMENTATION.diff` and `news_files_changed.json` provide the review summary. Six existing files were copied before edits. The UI test baseline was reconstructed by removing only the known Phase 7 insertion/import; no Git ancestry can be verified. Logs, benchmark JSON, public diagnostic output, screenshots, isolated SQLite databases and the baseline snapshot are additional validation artifacts. No commit/branch/push was performed.

## Remaining actions

PARTIAL: Fresh retrieval currently depends on the provider allowance recovering. Retry one normal news request after the allowance resets; if persistent, check the signed-in Ollama account's search availability. Numeric quota/reset time is unknown. No additional credentials are needed for this machine's already verified local setup; hosted mode is an optional separately configured provider.

PARTIAL: Tanglish generated interpretation remains limited by this model; relevant Roman-letter fallbacks are verified. Final summaries are intentionally extractive quotations, not free-form abstractive summaries. Full article factual verification, comprehensive company/news coverage and guaranteed inference latency are not claimed. Streaming remains a separate future phase. Recheck final fresh English/Tanglish news flows through the browser after provider recovery. Restore the original Git metadata only if a true Git diff/commit is required; do not initialize a replacement repository.
