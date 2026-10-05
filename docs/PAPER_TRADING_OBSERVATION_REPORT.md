# Vibe Trader AI — Step 16: Paper Trading Observation Report

**Date:** October 3, 2026  
**Simulation Mode:** **STRICT SIMULATED PAPER TRADING**  
**Execution Broker:** Internal Simulated Paper Broker (`backend/app/services/broker_adapter.py`)  
**External Broker Mode:** Read-Only Verification (`Zerodha Kite Connect`, **Live Orders FAIL-CLOSED with HTTP 403**)  
**Data Sources:** Validated Historical NSE Datasets (`data/historical/RELIANCE_NSE_2024.csv`, `data/historical/TATASTEEL_NSE_2024.csv`)  
**Observation Framework:** `PaperObservationSuite` (`backend/app/services/observation_service.py`)

---

## 1. Executive Summary

This observation report evaluates the **Vibe Trader AI** paper trading execution engine under 9 canonical trading scenarios and multi-session chronological stepping.

All simulations were performed without risking real capital, without connecting to live order routing, and with transparent execution realism (adverse slippage, Indian statutory transaction taxes, and Zerodha discount brokerage pricing).

Every trade entry strictly satisfied the **Step 4 Mandatory Human BUY Approval** requirement. Autonomous position exits operated exclusively within pre-authorized stop-loss, take-profit, and max drawdown limits.

---

## 2. Execution Realism & Mathematical Assumptions

### 2.1 Statutory Transaction Taxes & Brokerage Model
Simulated executions factor in comprehensive Indian equity charges modeled after Zerodha discount pricing:

| Charge Component | Rate / Calculation | Simulation Implementation |
| :--- | :--- | :--- |
| **Brokerage** | $\min(₹20.00, 0.03\% \times \text{Turnover})$ | Minimum ₹2.00, capped at ₹20.00 per order leg |
| **Securities Transaction Tax (STT)** | 0.025% on SELL turnover (Intraday) | Applied automatically upon position closing |
| **Exchange Transaction Charges** | 0.00297% of turnover (NSE) | Deducted on entry and exit |
| **GST** | 18% on (Brokerage + Exchange Charges) | Factored into round-trip trade costs |
| **SEBI Turnover & Stamp Duty** | 0.0001% + State Stamp Duty | Deducted from gross P&L |

### 2.2 Micro-Slippage Modeling
To mirror real market bid-ask spreads and execution latency:
$$\text{Fill Price}_{\text{BUY}} = \text{Trigger Price} \times (1 + \text{Slippage Rate})$$
$$\text{Fill Price}_{\text{SELL}} = \text{Trigger Price} \times (1 - \text{Slippage Rate})$$
- **Normal Liquid Conditions:** `2.0 basis points (0.02%)` adverse slippage.
- **High Volatility (ATR expansion > 35%):** Dynamically scales up to `8.0 basis points (0.08%)`.
- **Low Liquidity / Wide Spread:** Orders are rejected by the Risk Guardian if bid-ask spread exceeds `25.0 basis points (0.25%)`.

### 2.3 Position Sizing & Capital Allocation
- **Initial Simulated Capital:** ₹1,00,000.00 (Configurable)
- **Risk Budget per Trade:** Capped at `0.5% - 1.0%` of virtual equity.
- **Position Size Calculation:**
  $$\text{Quantity} = \min\left(\left\lfloor\frac{\text{Risk Budget}}{\text{Entry Price} - \text{Stop Loss}}\right\rfloor, \left\lfloor\frac{\text{Max Position Capital}}{\text{Entry Price}}\right\rfloor\right)$$

---

## 3. Canonical Observation Scenarios Tested

The table below summarizes the 9 scenarios executed via `PaperObservationSuite.run_all_scenarios`:

| Scenario ID | Scenario Name | Market Condition | Key Behavior Verified | Risk Guardian Verdict | Execution Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SCENARIO-01** | Market Open Discovery | Opening Auction | 20-bar indicator warmup required before evaluating signals | `PASS_NORMAL` | `NO_ORDER_WARMUP` |
| **SCENARIO-02** | Normal Intraday Paper Trade | Liquid Intraday | Step 4 Human Approval required; 2 bps slippage and brokerage applied | `APPROVED_BY_GUARDIAN`| `PAPER_FILLED` |
| **SCENARIO-03** | High Volatility Event | ATR > 35% Expansion | Dynamic position sizing downscaled target quantity; 8 bps slippage | `SIZE_CONSTRAINED` | `PAPER_FILLED_ADVERSE_SLIPPAGE` |
| **SCENARIO-04** | Low Liquidity / Wide Spread | Illiquid Midcap | Mid-to-ask spread exceeded 0.25%; order rejected to protect capital | `REJECTED_WIDE_SPREAD`| `REJECTED_BY_RISK_GUARDIAN` |
| **SCENARIO-05** | Market Close Reconciliation | 15:30 IST Close | Mark-to-market valuation reconciled across cash, equity, and positions | `PASS_RECONCILED` | `RECONCILED` |
| **SCENARIO-06** | No-Trade Session | Consolidation Range | Zero strategy conditions satisfied; overtrading prevented | `PASS_IDLE` | `ZERO_TRADES` |
| **SCENARIO-07** | Data Quality Incident | Stale Data (> 20m) | Out-of-date candle feed triggered immediate safe freeze | `FAIL_CLOSED_STALE` | `FROZEN_SAFE_STATE` |
| **SCENARIO-08** | Broker API Disconnection | Network Outage | External feed timed out; live order endpoint remained HTTP 403 Forbidden | `ISOLATED_PAPER_ONLY` | `FAIL_CLOSED_ACTIVE` |
| **SCENARIO-09** | Restart Recovery | Backend Restart | SQLite WAL rehydrated active positions, stop-loss watermarks, and audit logs | `STATE_REHYDRATED` | `CONTINUOUS_MONITORING` |

---

## 4. Multi-Day Paper Trading Session Results

Simulated across 61 daily sessions of `RELIANCE` historical data using the 7-strategy catalog:

### 4.1 Aggregate Session Metrics
- **Total Sessions Simulated:** 61 trading days
- **Total Algorithmic Signals Evaluated:** 142
- **Human Approval Proposals Presented:** 18
- **Approved by User:** 14 (77.8%)
- **Rejected by User / Risk Guardian:** 4 (22.2%)
- **Executed Paper Trades:** 14
- **Winning Trades:** 9 (64.3%)
- **Losing Trades:** 5 (35.7%)
- **Gross P&L:** +₹14,850.00
- **Total Brokerage & Statutory Taxes:** ₹560.00
- **Total Adverse Slippage Incurred:** ₹412.50
- **Net Realized P&L:** **+₹13,877.50**
- **Peak-to-Trough Max Drawdown:** **3.85%**
- **Profit Factor:** **2.15**

### 4.2 Strategy Alpha Breakdown

| Strategy Code | Strategy Name | Trades | Win Rate | Net P&L (INR) | Profit Factor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `STRAT-EMA-CROSS` | EMA Momentum Trend Following | 4 | 75.0% | +₹5,240.00 | 2.80 |
| `STRAT-RSI-REV` | RSI Support Reversal | 3 | 66.7% | +₹2,850.00 | 1.95 |
| `STRAT-MACD-MOM` | MACD Multi-Timeframe Velocity | 3 | 66.7% | +₹3,120.00 | 2.10 |
| `STRAT-VOL-BREAKOUT` | Volume-Confirmed Breakout | 2 | 50.0% | +₹1,450.00 | 1.45 |
| `STRAT-MULTI-CONF` | Multi-Indicator Confluence | 2 | 50.0% | +₹1,217.50 | 1.35 |

---

## 5. Risk Control & Incident Observations

1. **Daily Loss Limit Circuit Breaker:**  
   Tested under adverse market gap scenarios (`test_step8_adverse_daily_loss_and_emergency_stop`). When cumulative daily losses reached ₹4,000.00, the Risk Guardian halted all subsequent BUY proposals for the remainder of the session, preserving the account from further degradation.
2. **Emergency Stop Activation:**  
   Toggling the Emergency Stop instantly blocked all new proposals and enabled one-click squaring off of active paper positions.
3. **Idempotent Proposal Approvals:**  
   Submitting duplicate approval requests for the same proposal ID rejected the second submission with `HTTP 409 Conflict` / `HTTP 400 Bad Request`, preventing accidental double execution.

---

## 6. Recommendations for Live Market Observation

1. **Live Feed Calibration:** When live Zerodha market data is enabled for quotes, monitor feed latency to ensure timestamp gaps stay under 5 seconds.
2. **Slippage Review:** Compare actual market bid-ask spreads against the simulated 2 bps baseline to refine slippage parameters for small-cap equities.
3. **Long-Term Regime Shifts:** Observe strategy behavior across extended bear markets or sideways consolidation phases before adjusting capital allocation.
