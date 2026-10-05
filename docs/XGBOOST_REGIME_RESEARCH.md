# XGBOOST QUANTITATIVE ENHANCEMENTS & CAUSAL MARKET-REGIME RESEARCH

**Author:** Quantitative ML Engineer & Algorithmic Trading Systems Architect  
**System:** Vibe Trader AI — Advanced XGBoost Research & Regime Classification Subsystem  
**Date:** 2026-10-04  
**Status:** VALIDATED & DEPLOYED (RESEARCH & PAPER-TRADING ONLY)  

---

## 1. Executive Summary

This report documents the architectural enhancements delivered to the XGBoost Quantitative Machine Learning Engine in Vibe Trader AI:
1. **Feature Schema Versioning (`2.0.0-causal`):** Strict contract enforcement between model training and inference pipelines to eliminate feature drift and schema misalignment.
2. **Probability Calibration Check:** Integration of Brier score loss calculations and automated calibration warning flags ($BS > 0.28$) to identify overconfident or uninformative model outputs.
3. **Prediction Abstention Zone ($0.48 \le P(\text{Up}) \le 0.52$):** Neutrality threshold preventing forced binary directional calls when model uncertainty is statistically equivalent to a coin toss.
4. **Causal Market-Regime Classification:** Strict zero-lookahead regime tagging (`TRENDING_BULLISH`, `TRENDING_BEARISH`, `HIGH_VOLATILITY_EXPANSION`, `RANGING_LOW_VOLATILITY`).
5. **Regime-Conditioned Evaluation:** Disaggregation of out-of-sample test accuracy across market regimes to isolate environment-specific model efficacy.

---

## 2. Feature Schema Versioning Contract (`FEATURE_SCHEMA_VERSION = "2.0.0-causal"`)

To prevent training-inference divergence, feature definitions are versioned explicitly. Every model artifact records the schema version used during training. At inference time, the model booster validates the feature pipeline version:

```python
FEATURE_SCHEMA_VERSION = "2.0.0-causal"

FEATURE_NAMES = [
    "rsi_14",           # 14-period Relative Strength Index [0, 100]
    "macd_hist_norm",   # Normalized MACD Histogram (12, 26, 9)
    "ema_spread_9_21",  # (EMA_9 - EMA_21) / Close
    "ema_trend_50",     # (Close - EMA_50) / EMA_50
    "atr_norm_14",      # ATR_14 / Close (volatility ratio)
    "volume_ratio_20",  # Volume / Volume_SMA_20
    "bb_pct_b",         # Bollinger %B ((Close - Lower) / (Upper - Lower))
    "return_1bar",      # (Close[t] - Close[t-1]) / Close[t-1]
    "return_5bar",      # (Close[t] - Close[t-5]) / Close[t-5]
]
```

### Safety Gate:
If a model trained on legacy `v1.0` or an unknown schema version is loaded for inference, `XGBoostFeaturePipeline.validate_feature_schema` raises a typed `ValueError`:
```text
ValueError: Feature schema version mismatch: model expects '1.0.0', but feature pipeline version is '2.0.0-causal'.
```
This fails-closed before any prediction record is created or transmitted.

---

## 3. Probability Calibration & Brier Score Validation

Traditional accuracy metrics (accuracy, F1, ROC-AUC) evaluate ranking order but ignore whether predicted probabilities match empirical base rates. The engine computes the **Brier Score**:

$$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^N (P_i - Y_i)^2$$

Where $P_i \in [0, 1]$ is the predicted probability of an upward bar, and $Y_i \in \{0, 1\}$ is the actual realized direction.

| Calibration Metric Range | Calibration Status | Operational Behavior |
| :--- | :--- | :--- |
| **Brier Score $< 0.20$** | `WELL_CALIBRATED` | High confidence probabilities; suitable for advisory synthesis |
| **$0.20 \le$ Brier Score $\le 0.25$** | `STANDARD_CALIBRATION` | Acceptable out-of-sample predictive calibration |
| **$0.25 <$ Brier Score $\le 0.28$** | `MARGINAL_CALIBRATION` | Marginal edge over uninformative 50/50 baseline ($BS = 0.25$) |
| **Brier Score $> 0.28$** | `POOR_CALIBRATION_WARNING` | Flagged in model metadata; warning displayed in research UI |

---

## 4. Prediction Abstention Zone ($0.48 \le P(\text{Up}) \le 0.52$)

In standard binary classification, an inference probability of $P(\text{Up}) = 0.501$ forces a `BULLISH_UP` label. In financial time series, this introduces severe noise and spurious signals.

### Abstention Mechanism:
- If $0.48 \le P(\text{Up}) \le 0.52$:
  - `predicted_class = -1`
  - `predicted_direction = "ABSTAIN"`
  - `data_freshness_status = "ABSTAIN_UNCERTAINTY_ZONE"`
- The downstream AI comparison and Qwen explainer interpret `ABSTAIN` as a `CAUTIONARY` state, preventing false breakout recommendations.

---

## 5. Causal Market-Regime Classification

The market regime classifier evaluates 4 distinct market microstructures using **only data available at or before candle $t$**:

```
                              [ Candle Bar t ]
                                     |
               +---------------------+---------------------+
               |                                           |
        Normalized ATR > 0.025?                   Normalized ATR <= 0.025
               |                                           |
               v                                           v
    HIGH_VOLATILITY_EXPANSION                     Evaluate Trend & Spread
                                                           |
                          +--------------------------------+--------------------------------+
                          |                                                                 |
                   EMA_Trend > 0.005                                                 EMA_Trend < -0.005
                 & EMA_Spread > 0.002                                              & EMA_Spread < -0.002
                          |                                                                 |
                          v                                                                 v
                   TRENDING_BULLISH                                                  TRENDING_BEARISH
                          |                                                                 |
                          +--------------------------------+--------------------------------+
                                                           |
                                                    Otherwise (Flat)
                                                           |
                                                           v
                                                 RANGING_LOW_VOLATILITY
```

### Regime Specifications:
1. **`HIGH_VOLATILITY_EXPANSION`:** Normalized ATR exceeds 2.5% of price. High tail risk, wide bid-ask spreads.
2. **`TRENDING_BULLISH`:** Price $> 0.5\%$ above 50-period EMA, and 9-EMA $> 0.2\%$ above 21-period EMA.
3. **`TRENDING_BEARISH`:** Price $< 0.5\%$ below 50-period EMA, and 9-EMA $< 0.2\%$ below 21-period EMA.
4. **`RANGING_LOW_VOLATILITY`:** Moderate ATR, intertwined moving averages, mean-reverting price action.

---

## 6. Regime-Conditioned Model Evaluation

During training, the evaluation pipeline categorizes each test candle by its causal regime and produces an environment breakdown:

```json
{
  "regime_breakdown": {
    "TRENDING_BULLISH": {
      "sample_count": 28,
      "accuracy": 0.6786,
      "brier_score": 0.1982,
      "percentage_of_test": 37.3
    },
    "TRENDING_BEARISH": {
      "sample_count": 19,
      "accuracy": 0.6316,
      "brier_score": 0.2104,
      "percentage_of_test": 25.3
    },
    "HIGH_VOLATILITY_EXPANSION": {
      "sample_count": 8,
      "accuracy": 0.5000,
      "brier_score": 0.2640,
      "percentage_of_test": 10.7
    },
    "RANGING_LOW_VOLATILITY": {
      "sample_count": 20,
      "accuracy": 0.5500,
      "brier_score": 0.2315,
      "percentage_of_test": 26.7
    }
  }
}
```

---

## 7. Automated Test Verification Results

Automated test suite: `tests/backend/test_xgboost_regime_enhancements.py`

| Test Name | Verified Behavior | Status |
| :--- | :--- | :---: |
| `test_feature_schema_version_constant` | Confirms `FEATURE_SCHEMA_VERSION == "2.0.0-causal"` | **PASS** |
| `test_feature_schema_validation_success` | Validates matching schema version returns `True` | **PASS** |
| `test_feature_schema_validation_mismatch_rejected` | Rejects mismatched versions (`1.0.0`, `v1.0`, empty) | **PASS** |
| `test_well_calibrated_model_metrics` | Confirms low Brier score yields `WELL_CALIBRATED` | **PASS** |
| `test_poor_calibration_warning_triggered` | Confirms Brier score $>0.28$ triggers warning | **PASS** |
| `test_prediction_abstention_in_low_confidence_zone` | Confirms $P \in [0.48, 0.52]$ produces `ABSTAIN` (class -1) | **PASS** |
| `test_directional_prediction_outside_abstention_zone` | Confirms $P > 0.52$ produces directional output | **PASS** |
| `test_market_regime_classification_bullish` | Confirms positive trend/spread yields `TRENDING_BULLISH` | **PASS** |
| `test_market_regime_classification_bearish` | Confirms negative trend/spread yields `TRENDING_BEARISH` | **PASS** |
| `test_market_regime_classification_high_volatility` | Confirms ATR $> 0.025$ yields `HIGH_VOLATILITY_EXPANSION` | **PASS** |
| `test_market_regime_classification_ranging` | Confirms flat EMAs yield `RANGING_LOW_VOLATILITY` | **PASS** |
| `test_regimes_for_dataframe_causality` | Confirms row-by-row causality without lookahead | **PASS** |
| `test_regime_conditioned_accuracy_tally` | Confirms accurate test split tally per regime | **PASS** |
