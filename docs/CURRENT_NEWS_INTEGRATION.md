# Current news integration

## Architecture

The existing application is React 18 + TypeScript + Vite, FastAPI with synchronous handlers dispatched through its worker thread pool, SQLAlchemy/SQLite, and a pooled HTTP connection to local Ollama. The configured model remains `qwen3-local:latest` (Qwen3 4.0B, Q4_K_M). Existing technical, deterministic strategy, XGBoost, paper portfolio and Risk Guardian services are retained. Market OHLC is demo/uploaded historical data; this feature does not introduce a live price feed.

The existing `POST /api/assistant/chat` now routes news requests to `NewsService`, validates recent search evidence, and passes compact evidence to the existing Qwen generation path. No new chatbot endpoint, model download, dependency or database migration is needed. Typed `news` metadata accompanies the response and is persisted inside the existing `sources_json` NewsTool entry; history restores it. Source cards render original links and publication/retrieval times separately from AI prose.

## Provider selection and setup

PASS — VERIFIED: the installed Ollama 0.34.4 daemon answered a real `POST /api/experimental/web_search` request. Its results contain `title`, `url` and `content`, with publication metadata present in some excerpts. This is a cloud web-search proxy through the local daemon, not offline search performed by the Qwen weights. Only a constructed public financial-topic query is transmitted; user account details and chat history are excluded.

The experimental local route is confirmed in [Ollama's server implementation](https://github.com/ollama/ollama/blob/v0.18.2/server/routes.go#L1575) and through this installation's successful probe. The separate hosted API and its fields are documented in [Ollama web-search documentation](https://docs.ollama.com/capabilities/web-search). Experimental routes may change across daemon versions; unsupported/offline/unauthenticated installations return a safe unavailable state.

For this machine, the existing signed-in daemon works with defaults; no new API key was required. Keep Ollama running with its current model and start the existing backend and frontend:

```powershell
backend/venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
cd frontend
npm.cmd run dev -- --host 127.0.0.1
```

Place overrides in the repository's backend-loaded `.env`, then restart the backend:

| Variable | Default | Meaning |
| --- | --- | --- |
| NEWS_PROVIDER | ollama_local | Local daemon proxy; alternatively ollama_hosted |
| CHAT_OLLAMA_HOST | http://127.0.0.1:11434 | Existing local daemon host; reused for search |
| NEWS_API_KEY | empty | Only hosted mode requires this server-side Ollama API key |
| NEWS_TIMEOUT_SECONDS | 8 | Per-network timeout, bounded to 1–30 seconds |
| NEWS_RETRIES | 1 | At most one additional attempt by default; maximum two retries |
| NEWS_CACHE_TTL_SECONDS | 120 | Process-local cache lifetime; zero disables later-turn reuse |
| NEWS_MAX_AGE_HOURS | 72 | Maximum original publication age; configurable 1–168 hours |
| NEWS_MAX_ARTICLES | 3 | Maximum accepted articles, configurable 1–5 |

For hosted mode use `NEWS_PROVIDER=ollama_hosted` and `NEWS_API_KEY=<your Ollama API key>`. The key is a backend SecretStr and sent only in an Authorization header to the fixed hosted endpoint. Never use a `VITE_` variable for credentials. Hosted authentication is documented by Ollama; this mode is transport-mock tested, not live tested here. No paid subscription or numeric quota is assumed or guaranteed. Local sign-in/cloud availability and hosted quotas remain provider controlled.

## Routing

| Request | Route / context |
| --- | --- |
| Hi | Existing GREETING fast path, zero tools |
| What is stock market? / Explain RSI / What is financial news? | EDUCATIONAL, zero news tools |
| Latest NIFTY news / recent RBI announcements | NEWS_CURRENT, public topic only |
| Latest Infosys / Reliance news | COMPANY_NEWS, requested company only |
| Explain today's major global financial news | NEWS_SUMMARY, global financial topic |
| What's happening in NIFTY today? | NEWS_CURRENT, recent news rather than synthetic candles |
| NIFTY RSI today | Existing TECHNICAL_ANALYSIS |
| What's happening in NIFTY right now? | Existing INSTRUMENT_ANALYSIS, historical/live availability disclosure |
| Why did my strategy generate a BUY signal? | Existing STRATEGY_EXPLANATION, actual saved signal context |
| How might RBI's latest announcement affect banks? | MARKET_NEWS_IMPACT, RBI evidence |
| Intha news NIFTY mela enna impact pannum? | MARKET_NEWS_IMPACT, this session's prior evidence revalidated; clarification if missing/stale |

The existing GREETING label is preserved despite the example calling it GENERAL_CHAT. Definitions about news remain educational. Unsupported explicitly named companies request clarification; supported topic aliases are explicit in `news_intent.py`. The router is deliberately conservative, not an arbitrary web agent. No portfolio, OHLC, indicators or broker calls are added to news turns.

## Model and safety behavior

Only up to three short excerpts by default are supplied, with source IDs and titles; long history and unrelated account context are excluded. Qwen uses the existing semaphore, pooled client, language matching and 50-second model bound. News output uses a JSON schema with summary, possible implications and source IDs; generation is capped at 160 tokens. The summary is extractive: a runtime enum constrains Qwen to an exact supplied headline, quoted unchanged and labelled as AI selection. This deliberately avoids paraphrasing numerical facts after real probes exposed a duration distortion. The selected headline must match its cited source. Original headlines retain their original language; generated implications and surrounding assistant labels follow English/Tanglish.

Generated implications use ASCII Roman letters/punctuation and qualitative descriptions. Unicode normalization and spelled-quantity checks prevent numeric bypasses. Exact values/dates/symbols remain in source cards and expandable retrieved excerpts. Free-form abstractive news summaries are deferred until model factual consistency can be established; no model replacement was made.

Schema/empty-output/language checks, exact headline matching, citation bounds, unsupported-number checks (including cited-article validation), and certainty/URL checks reject invalid answers. Validated structured source IDs supply citations without relying on model-written markup. These checks are conservative; semantic entailment of free-form possible implications is not fully machine-verifiable. Read source excerpts and original articles before relying on an interpretation.

No evidence means no model inference and a built-in no-results, provider-error or clarification response. Failed/invalid Qwen generation means a clearly labelled evidence-only deterministic fallback with retrieved headlines, no invented market report. English and Roman-letter Tanglish reuse existing language behavior; poor Tanglish model output is rejected rather than silently presented.

Paper-only trading, risk controls, approval gates and broker authorization/execution are untouched. No news or generated text has access to order submission. React renders headline text safely, links have a strict HTTPS publisher allowlist and `noopener noreferrer`, and existing safe Markdown renders summaries. Streaming remains a future phase.
