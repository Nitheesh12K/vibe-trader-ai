# AI VS DETERMINISTIC STRATEGY COMPARISON & DIVERGENCE FRAMEWORK

**Author:** Principal Trading Systems Architect & Quantitative ML Engineer  
**System:** Vibe Trader AI — Advanced Local AI & Quantitative Research Engine  
**Date:** 2026-10-03  
**Status:** IMPLEMENTED, TESTED & PRODUCTION-READY (RESEARCH & PAPER-TRADING ONLY)  

---

## 1. Architectural Overview

The AI vs Deterministic Strategy Comparison framework provides an objective, transparent, and auditable concurrence and divergence analysis between:
1. **Deterministic Rule-Based Strategies:** Algorithmic signal generators (e.g., EMA Crossover, RSI Mean Reversion, MACD Momentum) that execute with 100% deterministic logic.
2. **Quantitative Machine Learning (XGBoost):** Walk-forward trained gradient boosting models generating next-bar directional probabilities $P(\text{Close}_{t+1} > \text{Close}_t \mid X_t)$.
3. **Local Large Language Model (Qwen):** Offline reasoning models synthesizing technical signals, volatility regimes, and machine learning inferences into grounded advisory explanations.

```
+-------------------------------------------------------------------------------+
|                       MARKET DATA (OHLCV CAUSAL FEED)                         |
+---------------------------------------+---------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
+---------------------------------+           +---------------------------------+
|   DETERMINISTIC STRATEGIES      |           |    QUANTITATIVE ML & LOCAL AI   |
|   - STRAT-EMA-CROSS             |           |    - XGBoost Causal Classifier  |
|   - STRAT-RSI-REV               |           |    - Qwen Local Synthesizer     |
|   Signal: BUY / SELL / HOLD     |           |    Advisory: UP/DOWN, P(Up)     |
+----------------+----------------+           +----------------+----------------+
                 |                                             |
                 +----------------------+----------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |        AI COMPARISON & DIVERGENCE ENGINE    |
                 |   - Concurrence Evaluation (AGREE / DIVERGE)|
                 |   - Cautionary Zone Debouncing              |
                 |   - Deduplicated Alert Dispatching          |
                 +----------------------+----------------------+
                                        |
         +------------------------------+------------------------------+
         |                                                             |
         v                                                             v
+---------------------------------+           +---------------------------------+
|         DIVERGENCE ALERT        |           |         CONCURRENT ALIGNMENT    |
| - Logged to Audit Trail         |           | - Strictly Advisory             |
| - Deduplicated In-App Alert     |           | - NEVER Bypasses Human Approval |
| - ZERO Order Execution Trigger  |           | - Risk Guardian Remains Sovereign
+---------------------------------+           +---------------------------------+
```

---

## 2. Common Comparison Record Specification

All comparative evaluations are serialized and stored via the `AIStrategyComparisonRecord` schema and backed by the `ai_strategy_comparisons` SQLite/PostgreSQL table:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `record_id` | String | Unique comparison identifier (`CMP-XXXXXXXXXX`) |
| `timestamp` | Integer | Unix epoch timestamp of evaluated candle bar |
| `symbol` | String | Tracked instrument symbol (e.g. `RELIANCE`, `TATASTEEL`) |
| `market` | String | Exchange identifier (`NSE`, `MCX`, `FOREX`) |
| `timeframe` | String | Candle resolution (`1D`, `1H`, `15m`) |
| `deterministic_strategy_name` | String | Evaluated deterministic rule algorithm |
| `deterministic_signal` | Enum | Deterministic rule recommendation: `BUY`, `SELL`, `HOLD` |
| `deterministic_confidence` | Float | Confidence score $[0.0, 1.0]$ of deterministic rule |
| `xgboost_predicted_direction` | Enum | Machine learning advisory direction: `UP`, `DOWN`, `ABSTAIN` |
| `xgboost_probability` | Float | Out-of-sample directional probability $[0.0, 1.0]$ |
| `qwen_synthesized_recommendation`| Enum | Local Qwen synthesized advisory: `BUY`, `SELL`, `HOLD` |
| `concurrence_status` | Enum | Evaluated alignment verdict: `AGREE`, `DIVERGE`, `CAUTIONARY` |
| `divergence_reason` | String | Plain-text explanation when signals conflict |
| `human_approval_status` | Enum | `NOT_REQUIRED`, `PENDING`, `APPROVED`, `REJECTED` |
| `paper_trade_execution_status` | Enum | `NOT_EXECUTED`, `EXECUTED`, `BLOCKED_BY_RISK` |
| `realized_outcome` | Enum | Historical trade result: `WIN`, `LOSS`, `BREAKEVEN`, `PENDING` |
| `realized_pnl` | Float | Realized profit or loss in base currency units |

---

## 3. Concurrence & Divergence Decision Heuristics

The engine evaluates signals under deterministic rules with configurable divergence thresholds (`buy_divergence_prob_threshold = 0.40`, `sell_divergence_prob_threshold = 0.60`):

### A. Deterministic BUY Heuristics
1. **Severe Divergence (`DIVERGE`):**
   - Triggered if XGBoost probability $P(\text{Up}) < 0.40$ (indicating strong downward bias), OR
   - Triggered if Qwen advisory explicitly recommends `SELL` or `HOLD`.
   - *Outcome:* Dispatches warning alert, logs audit event, and halts execution pipeline.
2. **Cautionary State (`CAUTIONARY`):**
   - Triggered if XGBoost probability is in weak uncertainty band ($0.40 \le P(\text{Up}) < 0.55$), OR
   - Triggered if XGBoost direction is `ABSTAIN` (near 50% coin-toss probability).
3. **Agreement (`AGREE`):**
   - Triggered when XGBoost $P(\text{Up}) \ge 0.55$ and Qwen advisory is aligned with `BUY`.

### B. Deterministic SELL Heuristics
1. **Severe Divergence (`DIVERGE`):**
   - Triggered if XGBoost probability $P(\text{Up}) > 0.60$ and direction is `UP`, OR
   - Triggered if Qwen advisory recommends `BUY`.
2. **Cautionary State (`CAUTIONARY`):**
   - Triggered if XGBoost probability is mixed ($0.45 \le P(\text{Up}) \le 0.60$).
3. **Agreement (`AGREE`):**
   - Triggered when both systems agree on downward or neutral momentum.

### C. Deterministic HOLD Heuristics
1. **Cautionary State (`CAUTIONARY`):**
   - Triggered if XGBoost exhibits strong directional probability ($P(\text{Up}) > 0.70$ or $P(\text{Up}) < 0.30$), OR
   - Triggered if Qwen advisory recommends an aggressive directional move (`BUY` or `SELL`).
2. **Agreement (`AGREE`):**
   - Triggered when all systems confirm ranging, low-conviction, or consolidation behavior.

---

## 4. Alert Deduplication & Noise Reduction

To prevent alerting loops when multiple ticks or candle checks arrive on the same symbol:
- **Cooldown Window:** 300 seconds (5 minutes) per `(symbol, timeframe)`.
- **Deduplication Cache:** In-memory high-resolution timestamp mapping.
- **Behavior:** Repeated divergence checks within the cooldown window record the comparison record for audit trails, but suppress secondary `AlertEvent` notifications.

---

## 5. Non-Negotiable Safety Invariants

```
+---------------------------------------------------------------------------------+
|                                SAFETY GUARANTEES                                |
+---------------------------------------------------------------------------------+
| 1. HUMAN APPROVAL SOVEREIGNTY:                                                  |
|    Even if Deterministic Strategy and AI AGREE with 100% confidence on BUY,      |
|    the proposal MUST enter the Human Approval Center. Zero bypass is permitted. |
|                                                                                 |
| 2. RISK GUARDIAN AUTHORITATIVE GATE:                                            |
|    If the deterministic Risk Guardian rejects a trade (e.g. daily loss limit,   |
|    position size limit, emergency stop), AI agreement CANNOT override it.      |
|                                                                                 |
| 3. ZERO AUTONOMOUS BUY EXECUTION ON DIVERGENCE:                                 |
|    Divergence NEVER triggers a trade. Conflicting signals fail-closed.          |
|                                                                                 |
| 4. BROKER ENDPOINT FAIL-CLOSED:                                                 |
|    POST /api/broker/zerodha/orders returns HTTP 403 Forbidden unconditionally. |
+---------------------------------------------------------------------------------+
```

---

## 6. API Reference

### 1. `GET /api/research/ai-comparison`
Retrieves filtered comparison records and aggregate summary metrics.

**Parameters:**
- `symbol` *(optional)*: Filter by instrument (e.g. `RELIANCE`)
- `timeframe` *(optional)*: Filter by timeframe (`1D`, `1H`)
- `concurrence_status` *(optional)*: Filter by `AGREE`, `DIVERGE`, `CAUTIONARY`
- `start_timestamp`, `end_timestamp` *(optional)*: Unix epoch range
- `limit` *(default 50)*, `offset` *(default 0)*

**Response Schema:**
```json
{
  "total_records": 12,
  "agreement_count": 8,
  "divergence_count": 3,
  "cautionary_count": 1,
  "agreement_rate": 0.6667,
  "divergence_rate": 0.25,
  "cautionary_rate": 0.0833,
  "agreement_trade_win_rate": 0.75,
  "divergence_trade_win_rate": 0.33,
  "records": [ ... ]
}
```

### 2. `POST /api/research/ai-comparison/evaluate`
Evaluates concurrence between a deterministic rule and advisory predictions and stores the result.

---

## 7. Automated Test Verification Results

Automated test suite: `tests/backend/test_ai_deterministic_comparison.py`

```text
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\NITHEESH\.gemini\antigravity\scratch\vibe-trader-ai
configfile: pytest.ini
collected 10 items

tests/backend/test_ai_deterministic_comparison.py::test_concurrence_agreement_cases PASSED [ 10%]
tests/backend/test_ai_deterministic_comparison.py::test_divergence_detection_cases PASSED [ 20%]
tests/backend/test_ai_deterministic_comparison.py::test_cautionary_states PASSED [ 30%]
tests/backend/test_ai_deterministic_comparison.py::test_missing_or_invalid_signals PASSED [ 40%]
tests/backend/test_ai_deterministic_comparison.py::test_divergence_alert_dispatching_and_deduplication PASSED [ 50%]
tests/backend/test_ai_deterministic_comparison.py::test_stale_timestamp_handling PASSED [ 60%]
tests/backend/test_ai_deterministic_comparison.py::test_safety_invariants_human_approval_never_bypassed PASSED [ 70%]
tests/backend/test_ai_deterministic_comparison.py::test_safety_invariants_risk_guardian_overrides_ai PASSED [ 80%]
tests/backend/test_ai_deterministic_comparison.py::test_safety_invariants_divergence_never_triggers_trade PASSED [ 90%]
tests/backend/test_ai_deterministic_comparison.py::test_ai_comparison_api_flow PASSED [100%]

======================== 10 passed, 1 warning in 4.11s ========================
```
