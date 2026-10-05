# Smart intent routing

PASS — VERIFIED: deterministic routing runs before model generation and tools. No model is used just to classify.

| Intent | Model/tool behavior |
| --- | --- |
| GREETING | Short built-in English/Tanglish greeting; zero tools/inference |
| GENERAL_CHAT | Qwen with bounded recent history; zero market/account tools |
| EDUCATIONAL | Qwen directly; no live data. Definitions precede portfolio/risk terms |
| MARKET_OVERVIEW | Benchmark OHLC context only; disclose historical/demo provenance |
| INSTRUMENT_ANALYSIS | Requested instrument; market context plus explicitly requested groups |
| TECHNICAL_ANALYSIS | Market candles and requested indicators/patterns; no portfolio/research by default |
| STRATEGY_EXPLANATION | Persisted proposal and original evidence; no recomputation of a historical signal |
| PORTFOLIO_ANALYSIS | Paper portfolio context only |
| RISK_ANALYSIS | Existing portfolio and Risk Guardian context |
| CLARIFICATION | Built-in concise follow-up; zero market calls |

CAPABILITIES is an existing additional compatibility category, served by built-in verified feature descriptions.

Definitions such as “What is stock market?”, “Explain RSI”, “What is portfolio equity?”, “Explain XGBoost” skip tools. “Write Python code for NIFTY csv” does not become a market query. A mixed definition/analysis query uses the market tool plan; its explanation is based on that context. The latest explicit symbol wins over the active chart symbol. Technical analysis without either asks for clarification. Broad market overview uses NIFTY as the existing benchmark; this is not a worldwide market aggregator.

`select_market_tools` always requests MarketDataTool for instrument analysis; indicator names/trend add TechnicalIndicatorsTool; patterns/support/resistance add PatternsAndLevelsTool; explicit strategy/signal requests add StrategySignalsTool; explicit XGBoost adds XGBoostResearchTool. RSI-only computation reuses the existing RSI formula without calculating other groups. Unspecified broad technical analysis retains the existing indicator bundle. Indicator groups (e.g. EMA) calculate their supported periods.

Strategy explanations select the saved proposal by symbol or recognized proposal ID; when unscoped records are ambiguous or missing, ask for identifying details. These are read-only queries and never approve/execute a proposal.

Source/tool counts are recorded per response; tool latency is measured. Tools share a SQLAlchemy Session and some calculations depend on candles, so they remain sequential rather than unsafely sharing that Session across parallel workers. No new data cache or freshness exception was introduced.

PARTIAL — SOME CHECKS PASSED: lexical routing is deliberately conservative but finite. It does not resolve every possible ticker, timeframe phrase, mixed account/market request or Tamil spelling. Existing timeframe payload remains authoritative; uploaded timeframe is now checked before analysis. Add table-driven regressions for new supported phrasing.
