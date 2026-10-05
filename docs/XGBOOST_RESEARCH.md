# VIBE TRADER AI — XGBOOST QUANTITATIVE RESEARCH ENGINE
## Technical Architecture, Causal Mathematical Foundations, Validation, and Safety Guide

---

## 1. Executive Summary

The **XGBoost Quantitative Research Engine** integrates machine learning capabilities into Vibe Trader AI while upholding the platform's core architectural tenets:
1. **Strictly Advisory**: Machine learning predictions and LLM advisory syntheses are purely exploratory research outputs. They operate out-of-band and **NEVER execute real or paper orders directly**, alter portfolio balances, or override the deterministic Risk Guardian and human BUY approval gate.
2. **Causal Data Integrity**: Every feature vector at time $t$ is calculated exclusively from market data available at or before time $t$. Temporal ordering is strictly preserved with zero shuffling and one-bar purge boundaries.
3. **Transparent Benchmarking**: Machine learning models are evaluated against two naive baselines (Majority Class and Momentum Direction) across multiple out-of-sample splits and chronological walk-forward folds.
4. **Resilient Synthesis**: Combines deterministic rule-based strategy signals with XGBoost directional probabilities using Qwen (with graceful offline fallback) and automated divergence alerts.

---

## 2. Target Formulation & Mathematical Indicator Suite

### 2.1 Next-Bar Directional Target
The machine learning objective is binary directional classification for the next bar:

$$Y_t = \begin{cases} 1 & \text{if } \text{Close}[t+1] > \text{Close}[t] \\ 0 & \text{if } \text{Close}[t+1] \le \text{Close}[t] \end{cases}$$

Where:
- $Y_t = 1$ denotes an upward price movement in candle $t+1$.
- $Y_t = 0$ denotes a downward or flat price movement in candle $t+1$.
- **Boundary Purge Safeguard**: The latest candle in any historical dataset ($t = T$) is excluded from training because its future target $\text{Close}[T+1]$ is unobserved.

### 2.2 Nine Strictly Causal Feature Formulations
All 9 features are normalized and computed causally at bar $t$:

| # | Feature Name | Mathematical Definition | Purpose / Economic Rationale |
|---|---|---|---|
| 1 | `rsi_14` | $100 - \frac{100}{1 + \text{RS}_{14}}$ with Wilder's exponential smoothing | Mean-reversion momentum bound $[0, 100]$ |
| 2 | `macd_hist_norm` | $\frac{\text{MACD}_{12, 26} - \text{Signal}_9}{\text{Close}_t}$ | Price-normalized trend acceleration |
| 3 | `ema_spread_9_21` | $\frac{\text{EMA}_9 - \text{EMA}_{21}}{\text{Close}_t}$ | Short-term trend alignment velocity |
| 4 | `ema_trend_50` | $\frac{\text{Close}_t - \text{EMA}_{50}}{\text{Close}_t}$ | Medium-term trend bias relative to 50-period EMA |
| 5 | `atr_norm_14` | $\frac{\text{ATR}_{14}}{\text{Close}_t}$ | Volatility regime normalization |
| 6 | `volume_ratio_20` | $\frac{\text{Volume}_t}{\text{SMA}_{20}(\text{Volume})}$ | Relative volume expansion / institutional participation |
| 7 | `bb_pct_b` | $\frac{\text{Close}_t - \text{Lower}_t}{\text{Upper}_t - \text{Lower}_t}$ | Dynamic range position within 2-sigma Bollinger Bands |
| 8 | `return_1bar` | $\frac{\text{Close}_t}{\text{Close}_{t-1}} - 1$ | Immediate bar momentum |
| 9 | `return_5bar` | $\frac{\text{Close}_t}{\text{Close}_{t-5}} - 1$ | Multi-bar swing momentum |

### 2.3 Warmup Period Dropping
To avoid calculation artifacts from exponential moving averages ($\text{EMA}_{50}$) and rolling windows, the first 50 bars of any historical dataset are discarded during training dataset construction.

---

## 3. Chronological Time-Series Splitting & Validation

### 3.1 Non-Shuffled Temporal Splits
Standard $k$-fold cross-validation with random shuffling introduces severe future-data leakage in financial time-series. The engine enforces strictly non-overlapping, chronological splits:

$$\max(\mathcal{T}_{\text{train}}) < \min(\mathcal{T}_{\text{val}}) < \min(\mathcal{T}_{\text{test}})$$

Default temporal ratio allocations:
- **Training Set**: 70% of chronological bars
- **Validation Set**: 15% of chronological bars (used for early stopping)
- **Test Set**: 15% of chronological bars (held out, touched only once for final metric computation)

### 3.2 Chronological Walk-Forward Multi-Fold Validation
In addition to the static train/val/test split, the engine runs $K$-fold chronological walk-forward evaluation:
1. Divide usable historical bars into $K$ sequential time blocks.
2. In fold $k$, train on all prior blocks $[1, \dots, k-1]$ and evaluate on block $k$.
3. Track out-of-sample accuracy, F1-score, and Brier score across all folds.
4. Record performance stability across changing market regimes.

---

## 4. Naive Benchmark Baselines

To ensure machine learning performance is never overstated, the engine benchmarks every model against two deterministic baselines on the exact same out-of-sample test set:

### 4.1 Majority Class Baseline
Predicts whichever direction was most prevalent in the training window:

$$\hat{Y}_{\text{majority}} = \text{mode}(Y_{\text{train}})$$

$$\text{Accuracy}_{\text{majority}} = \frac{1}{N_{\text{test}}} \sum_{i \in \text{test}} \mathbb{I}(Y_i = \hat{Y}_{\text{majority}})$$

### 4.2 Momentum Direction Baseline
Predicts that next-bar direction will match the current bar's return:

$$\hat{Y}_{\text{momentum}} = \begin{cases} 1 & \text{if } \text{return\_1bar}_t > 0 \\ 0 & \text{otherwise} \end{cases}$$

$$\text{Accuracy}_{\text{momentum}} = \frac{1}{N_{\text{test}}} \sum_{i \in \text{test}} \mathbb{I}(Y_i = \hat{Y}_{\text{momentum}})$$

The system computes and displays performance differentials:
- $\Delta_{\text{majority}} = \text{Accuracy}_{\text{XGB}} - \text{Accuracy}_{\text{majority}}$
- $\Delta_{\text{momentum}} = \text{Accuracy}_{\text{XGB}} - \text{Accuracy}_{\text{momentum}}$

---

## 5. Model Serialization & Artifact Security

### 5.1 Elimination of Pickle Vulnerabilities
Python's `pickle` library poses severe security risks (arbitrary code execution upon unpickling untrusted files). The XGBoost Research Engine enforces:
- **Format**: Native XGBoost JSON (`.json`) using `model.save_model(...)` and `model.load_model(...)`.
- **Location**: Isolated directory `data/models/xgboost/`.
- **Integrity**: SHA256 cryptographic checksum computed immediately upon serialization and verified upon loading.
- **Audit**: Every trained model is registered in the SQLite `xgboost_experiments` table with hyperparameter snapshots and checksums.

---

## 6. Real-Time Advisory Inference & Qwen Synthesis

### 6.1 Single-Vector Causal Inference
At inference time:
1. The engine ingests historical candles ending at current bar $t$.
2. It extracts causal features without requiring future target information.
3. The model outputs class probabilities: $P(Y_{t+1} = 1 \mid \mathcal{F}_t)$ and $P(Y_{t+1} = 0 \mid \mathcal{F}_t)$.
4. Direction is assigned:
   - `BULLISH_UP` if $P(\text{Up}) > 0.52$
   - `BEARISH_DOWN` if $P(\text{Down}) > 0.52$
   - `NEUTRAL` otherwise.
5. The prediction is logged in `xgboost_prediction_records` with status `UNVERIFIED_PENDING_BAR`.

### 6.2 Automated Divergence Detection
When integrating rule-based strategy signals with XGBoost predictions:
- **Confluence**: If Rule = BUY and XGBoost = BULLISH $\implies$ Confirmed Signal.
- **Divergence**: If Rule = BUY but XGBoost = BEARISH $\implies$ Warning Flag Raised:
  > `DIVERGENCE DETECTED: Deterministic rule proposes BUY, but XGBoost model forecasts X% downside probability.`
- **Action**: Unified recommendation downgraded to `CAUTION_BUY` with explicit stop-loss tightening advice.

### 6.3 Local Qwen LLM Integration & Deterministic Fallback
- **Primary Explainer**: Local Ollama instance running `qwen2.5:latest` generating structured advisory explanations.
- **Fail-Safe Fallback**: If Ollama is offline or times out (exceeding 4.0s), the system activates `DeterministicFallbackProvider`. Advisory synthesis never crashes or hangs when AI dependencies are unavailable.

---

## 7. Safety Invariants & Release Verification

1. **Zero Trade Execution**: Under no circumstances can XGBoost predictions trigger real or paper order placement.
2. **Fail-Closed Broker Orders**: Live broker order endpoints (`/api/broker/zerodha/orders`) remain fail-closed (`HTTP 403 Forbidden`).
3. **Mandatory Human Gate**: BUY proposals require human authorization; machine learning cannot approve proposals.
4. **Append-Only Audit**: All training runs, predictions, and advisory syntheses are recorded in the tamper-evident audit log.
