# Vibe Trading AI — Trading Simulation Assumptions, Backtesting Limitations & Modeling

## 1. Core Purpose

The **Paper Trading Engine** and **Quantitative Backtesting Engine** in Vibe Trading AI provide a high-fidelity local simulation environment to evaluate algorithmic strategies and AI reasoning without risking actual capital. 

This document details the mathematical assumptions, micro-slippage models, statutory fee calculations, and backtesting limitations implemented in the platform.

---

> [!WARNING]
> **SIMULATION & BACKTEST DISCLAIMER**  
> All simulated trading and backtesting results presented by this platform are hypothetical and deterministic.  
> - **PAST AND BACKTESTED RESULTS DO NOT GUARANTEE FUTURE PERFORMANCE.**  
> - No real money is risked or held. Live broker execution is strictly disabled.  
> - Real live trading involves market risk, price gaps, liquidity evaporation, execution latency, and slippage that cannot be fully captured in simulation.

---

## 2. Capital Calibration (Indian Equities Focus)

| Parameter | Default Demo Calibration | Description |
| :--- | :--- | :--- |
| **Initial Simulated Balance** | **₹2,000.00** | User-configurable virtual capital for small-account testing |
| **Max Risk Per Trade** | **0.5% (₹10.00)** | Maximum capital exposed to risk per individual trade |
| **Max Open Positions** | **1** | Maximum concurrent active positions (prevents overtrading) |
| **Max Position Sizing** | **50.0% (₹1,000.00)**| Maximum capital allocated to any single trade |
| **Daily Loss Stop** | **₹40.00** | Cumulative loss circuit-breaker halting further trades for the day |

---

## 3. Order Execution & Slippage Modeling

### 3.1 Market Order Micro-Slippage
In live markets, market orders experience slippage due to bid-ask spread and latency. The Paper Trading Engine models **adverse execution slippage**:
$$\text{Execution Price}_{\text{BUY}} = \text{Trigger Price} \times (1 + \text{Slippage Rate})$$
$$\text{Execution Price}_{\text{SELL}} = \text{Trigger Price} \times (1 - \text{Slippage Rate})$$
- **Default Slippage Rate**: `0.02%` to `0.05%` (2 to 5 basis points) for liquid equities (`RELIANCE`, `TCS`, `INFY`).
- For volatile market events (ATR expansion), slippage scales proportionally with candle volatility.

### 3.2 Limit & Stop Orders
- **Limit Orders**: Filled only if the subsequent market price reaches or crosses the limit price.
- **Stop Loss Orders**: Triggered when market price reaches the stop price, then executed at market with adverse slippage.

---

## 4. Transaction Costs & Indian Brokerage Model

Simulated trades include realistic statutory taxes and brokerage charges modeled after Zerodha discount pricing:

1. **Brokerage**:
   $$\text{Brokerage} = \min(₹20.00, 0.03\% \times \text{Turnover})$$
   *(Minimum ₹2.00 per simulated round-trip order).*
2. **Securities Transaction Tax (STT)**:
   - Equity Intraday: 0.025% on SELL turnover
   - Equity Delivery: 0.1% on BUY and SELL turnover
3. **Exchange Transaction Charges**:
   - NSE: 0.00297% of turnover
4. **GST (Goods & Services Tax)**:
   - 18% on (Brokerage + Exchange charges)
5. **SEBI Turnover Charges & Stamp Duty**:
   - Factored into round-trip trade reporting and net P&L calculations.

---

## 5. Trailing Stop Loss & Position Management

When autonomous exit permissions are enabled:
- **High-Water Mark**: The engine continuously tracks the highest price reached since entry.
- **Dynamic Trail**:
  $$\text{Stop Loss}_{\text{trailing}} = \text{Peak Price} - (k \times \text{ATR}_{14})$$
  *(Where $k$ is configurable between 1.5 and 2.5).*
- Trailing stops ratchet strictly upward for Long positions and never move downward.
- **Guarded Exit Principle**: The autonomous exit monitor can only close existing open positions to protect capital; it can never open new positions or increase position exposure.

---

## 6. Backtesting Engine Assumptions & Limitations

The quantitative backtesting engine (`BacktestingService`) provides historical simulation under the following architectural controls:

### 6.1 Look-Ahead Bias Prevention
- **Causal Sequential Indexing**: Every candle $t$ is evaluated strictly using historical data available up to $t$ ($\{C_0, C_1, \dots, C_t\}$). Future candles ($\{C_{t+1}, \dots\}$) are strictly inaccessible to the strategy engine at step $t$.
- **Indicator Warmup**: Strategies require a minimum warmup window (e.g. 21 periods for EMA-21, 35 periods for MACD, 14 periods for RSI) before generating signals.

### 6.2 In-Sample vs. Out-of-Sample Methodology
- **Data Partitioning**: Datasets are partitioned chronologically (default 70% in-sample for parameter calibration, 30% out-of-sample for validation).
- **Overfitting Prevention**: Strategy parameters are hardcoded and intentionally not optimized via automated curve-fitting.

### 6.3 Technical Limitations of Backtesting
1. **Queue Priority & Partial Liquidity**: Backtesting assumes simulated orders are fully filled at the candle close or open price adjusted for slippage. In live markets, orders join a queue and may experience partial fills.
2. **Spread Widening**: Backtesting uses synthetic or historical OHLC mid/close prices. It does not model extreme spread widening during news events or market open/close auctions.
3. **Survivor Bias**: Backtesting on current index constituents (`NIFTY 50`) carries survivor bias unless delisted or historical constituent sets are explicitly supplied.
4. **Regime Shifts**: Historical performance during a bullish or range-bound market regime will not predict strategy behavior during a liquidity freeze or systemic crash.
