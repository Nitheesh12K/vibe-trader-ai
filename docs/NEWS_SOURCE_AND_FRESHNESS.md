# News sources and freshness

## Evidence policy

Search results are explicitly `SEARCH_EXCERPT` evidence. An article's full contents, publisher authenticity, or factual accuracy are not independently verified merely because a result appears in search. The cards and API clearly state this limitation. Headlines, snippets, original source URLs, mapped publisher, explicit publication time, provider, and actual retrieval time are retained separately from Qwen's summary and interpretation.

Accepted HTTPS publisher domains are Reuters, CNBC TV18, Economic Times, Moneycontrol, Mint, Business Standard, RBI, CNBC, BBC, Financial Express and BusinessLine. Exact hosts and their `www.` form are allowed; arbitrary subdomains, private hosts, userinfo, alternate ports, malformed URLs and tracking redirects are rejected. Only direct article paths are accepted; known tracking query parameters and fragments are removed for deduplication. The service never fetches user-supplied or article URLs. Titles/URLs and normalized duplicate headlines are deduplicated before selecting recent results.

Publication time must be explicit: a Published ISO timestamp with timezone or supported Published date/time metadata with IST/UTC/GMT. Dates in URLs/headlines, relative ages, Last Updated fields alone and missing/ambiguous times are insufficient. Future and older-than-window articles are excluded. Missing metadata, off-topic results and unapproved publishers count as rejected results; one malformed result does not discard good evidence. The allowlist and strict date rules intentionally reduce coverage.

## Cache and failure policy

Default publication age limit is 72 hours and the process-local successful-result cache lasts 120 seconds. Cached results are checked again for age and retain original `published_at` and `retrieved_at`. `checked_at` is a new freshness check, never a replacement for retrieval. UI labels distinguish new search, cached/coalesced evidence and reused conversation evidence. None is labelled breaking/live price data.

The cache is bounded to 64 public queries; in-flight searches are limited to 16 and identical simultaneous queries share one result. Empty results and provider errors are not cached as successful news. Waiters share the actual empty/error status rather than treating stale previous cache entries as fresh. An expired cache initiates a new search. Follow-ups reuse only the recent evidence stored in that session; missing or expired evidence triggers clarification.

Search requests use an 8-second network timeout by default, a finite overall attempt budget, a 200KB response bound, and at most one retry. Transport errors and gateway 502/503/504 failures can retry; authentication/429/malformed responses do not loop. Failures expose safe configuration/connectivity guidance, never raw exception bodies, sign-in tokens or API keys. Provider errors do not trigger Qwen to fabricate news. A valid chat turn still returns HTTP 200 with typed unavailable status; invalid chat payloads retain FastAPI's existing validation status.

`error_code` distinguishes RATE_LIMITED, AUTH_REQUIRED, TIMEOUT, CONFIGURATION_ERROR, BAD_RESPONSE and UNAVAILABLE. Real repeated validation searches reached HTTP 429 on this machine; the configured account's numeric quota/reset time was not established. No quota is invented. Wait for the provider allowance to recover before retrying fresh retrieval; existing session evidence can still be discussed while within its documented publication window and explicitly labelled reused.

## Remaining limits

There is no guarantee that every recent article is indexed or contains usable publication metadata. The service retrieves a small excerpt set, not a comprehensive exchange bulletin, official price feed or causal event study. Relevance uses deterministic topic terms. The publisher allowlist and supported company aliases require deliberate code updates to broaden coverage. Caching/coalescing are per backend process, not cross-worker distributed infrastructure.

Ollama local search requires reachable cloud search and a signed-in daemon that supports its experimental proxy. Model inference remains local. Hosted mode requires the documented server-side API key. A stopped/offline provider can recover on the next request because failures are not cached. Qwen failures preserve evidence-only headlines and are labelled as fallback.

Primary provider references: [API fields and hosted authentication](https://docs.ollama.com/capabilities/web-search), [local proxy implementation](https://github.com/ollama/ollama/blob/v0.18.2/server/routes.go#L1804).
