# AI failure and fallback report

PASS — VERIFIED: Qwen is retained; configured model cannot silently switch to llama or cloud. Chat host/model/timeout are `CHAT_OLLAMA_HOST`, `CHAT_OLLAMA_MODEL`, `CHAT_TIMEOUT_SECONDS` in existing Settings. Defaults: localhost:11434, qwen3-local:latest, 50s. The installed Qwen is 4.0B Q4_K_M, with reported GPU memory zero.

| Failure | Result |
| --- | --- |
| Daemon offline / configured model missing | Relevant explicitly labelled fallback; retry after checking service/model |
| Model timeout/network/HTTP failure | Bounded request, no automatic generation loop or trading side effects |
| Another chat inference active | 250ms admission limit, fallback rather than unbounded model queue |
| Empty/think-only/non-string/incomplete response | Reject to relevant fallback |
| Invalid Ollama JSON | Exception handled as inference failure |
| Tamil script despite Roman-letter requirement | Reject to labelled language-matched fallback, do not display mutilated generated text |
| Unsupported market numbers | Reject to deterministic source-based explanation |
| General/unknown educational question | AI-unavailable message, no irrelevant market template |
| Supported saved educational concept | Clearly described saved educational fallback, no tools |
| Missing or ambiguous strategy record | Request instrument/proposal ID; no fabricated BUY explanation |
| Malformed/out-of-order candles / wrong CSV timeframe | No analysis sources; describe unavailable context |
| Historical or simulated data | Explicit live-unavailable disclosure before generated/deterministic analysis |

Built-in greetings/help/clarification: `BUILTIN_ASSISTANT`, not Qwen. Generated answers: configured Qwen name and `is_fallback=false`. Failure output: `DETERMINISTIC_FALLBACK`, `is_fallback=true`. Frontend displays separate labels. The source panel retains original timestamps and identifies missing timestamps rather than saying “Real-time”.

Recovery is checked with mocked offline→online transport and real browser service recovery. No negative availability cache prevents recovery. Warm-up now checks HTTP status rather than logging preload success after HTTP errors. The inference HTTP client is pooled and closed on application shutdown; keep-alive retains the model without reinstalling it. Recent messages and retrieved prompt context are bounded.

PARTIAL — SOME CHECKS PASSED: availability health check remains the existing provider's short bounded check, and a busy host can temporarily fail it. Admission is local to one server process. General knowledge correctness, semantic language fluency, and all event hallucinations cannot be mechanically guaranteed by numerical validation. Numerical grounding is conservative and may reject an otherwise valid derived number. Model output is never a trade authorization.

Real Qwen produced English and then degenerate repeated text for Tanglish. Final checks reject wrong-language and repeated-sentence output to relevant saved Roman-letter fallback. This is a model fluency limitation, not proof of fluent generation. The final direct live-availability and missing-signal responses skip model availability checks entirely.

A real recovery conversation initially copied an old unavailable response from history despite successful inference. Failure/built-in/status history is now excluded, including pre-existing rows with incorrect old flags; direct copied-unavailable output is rejected. Regression verifies the inference prompt excludes previous unavailable text.
