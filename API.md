# Vibe Trading AI — API Reference & Endpoint Specification

FastAPI Backend Base URL: `http://127.0.0.1:8000`  
Interactive OpenAPI Swagger Docs: `http://127.0.0.1:8000/docs`  
ReDoc Documentation: `http://127.0.0.1:8000/redoc`

---

## 1. System Health & Status

### `GET /api/health`
Returns the status of the FastAPI backend and database connectivity.
- **Response**:
```json
{
  "status": "ok",
  "app_name": "Vibe Trader AI",
  "version": "0.1.0",
  "timestamp": "2026-10-02T10:00:00Z",
  "environment": "development",
  "database_connected": true
}
```

---

## 2. Technical Analysis & Indicators

### `POST /api/analysis/indicators`
Computes all deterministic indicators for the supplied or fetched candle series.
- **Request Body**:
```json
{
  "symbol": "RELIANCE",
  "timeframe": "1D",
  "candles": []
}
```
- **Returns**: `rsi`, `macd`, `ema_9`, `ema_21`, `ema_50`, `ema_200`, `sma_20`, `sma_50`, `sma_200`, `bollinger_bands`, `atr`, `vwap`, `volume_sma`.

### `POST /api/analysis/patterns`
Evaluates candlestick series for rule-based pattern matching (Doji, Hammer, Inverted Hammer, Bullish/Bearish Engulfing, Morning/Evening Star, Shooting Star).

### `POST /api/analysis/support-resistance`
Calculates clustered swing high and swing low price zones with configurable tolerance.

### `GET /api/analysis/bundle`
Returns a unified bundle of candles, indicators, patterns, and support/resistance zones.

---

## 3. Algorithmic Strategy Catalogue & Signal Evaluation

### `GET /api/strategies/catalogue/all`
Returns all 7 pre-configured algorithmic strategies with descriptions, parameters, indicator dependencies, and lifecycle status.

### `POST /api/strategies/{strategy_code}/evaluate`
Runs real-time deterministic signal evaluation for a specific strategy code.
- **Supported Strategy Codes**:
  - `STRAT-EMA-CROSS`: Fast/Slow EMA Trend Follower
  - `STRAT-RSI-REV`: RSI Oversold/Overbought Mean Reversion
  - `STRAT-MACD-MOM`: MACD Histogram & Signal Crossover
  - `STRAT-VWAP-TREND`: Volume-Weighted Average Price Intraday Bias
  - `STRAT-BB-REV`: Bollinger Bands Mean Reversion
  - `STRAT-VOL-BREAKOUT`: High Volume Range Breakout
  - `STRAT-MULTI-CONF`: Multi-Indicator Confluence Engine
- **Response**:
```json
{
  "strategy_code": "STRAT-EMA-CROSS",
  "strategy_name": "Fast/Slow EMA Trend Follower",
  "signal_state": "BUY_CANDIDATE",
  "symbol": "RELIANCE",
  "timeframe": "1D",
  "confidence": 0.82,
  "trigger_price": 2950.0,
  "entry_level": 2950.0,
  "stop_loss_level": 2895.0,
  "target_level": 3060.0,
  "risk_reward_ratio": 2.0,
  "reasons": ["EMA 9 (2955.0) crossed above EMA 21 (2930.0)"],
  "caveats": ["Trailing stop recommended below swing low"],
  "generated_at": "2026-10-02T10:00:00Z"
}
```

---

## 4. AI Reasoning & Hallucination Defense

### `GET /api/analysis/ai/status`
Returns connection status to local Ollama (`http://127.0.0.1:11434`), loaded model (`deepseek-r1:1.5b`), and fallback availability.

### `POST /api/analysis/ai/evaluate`
Synthesizes market reasoning, multi-indicator confluence, and risk factors with strict Pydantic schemas and anti-hallucination validation.
- **Request Body**:
```json
{
  "symbol": "RELIANCE",
  "timeframe": "1D",
  "market": "NSE",
  "include_patterns": true
}
```
- **Response**:
```json
{
  "symbol": "RELIANCE",
  "timeframe": "1D",
  "sentiment": "BULLISH",
  "confidence_score": 0.85,
  "market_regime": "Trend Continuation",
  "primary_rationale": "Bullish momentum confirmed across EMA alignment and positive RSI trajectory.",
  "key_evidence": ["EMA 9 > EMA 21", "RSI is 58.2", "Price above VWAP"],
  "conflicting_signals": [],
  "uncertainty_factors": ["High volatility expected ahead of quarterly earnings"],
  "recommended_action": "BUY_CANDIDATE",
  "risk_caveats": ["Mandatory stop loss at 2895.0"],
  "hallucination_defense_passed": true,
  "quality_metrics": {
    "input_completeness_pct": 100,
    "data_freshness_seconds": 12,
    "structured_schema_valid": true,
    "model_latency_ms": 138.4,
    "unsupported_claims_rejected": 0,
    "provider_type": "OLLAMA"
  },
  "model_name": "deepseek-r1:1.5b",
  "timestamp": "2026-10-02T10:00:00Z"
}
```

---

## 5. Broker Integration — Zerodha Kite Connect Personal (Free)

### `GET /api/broker/zerodha/status`
Returns connection status, user ID, account name, margin, and operating mode (`READ_ONLY_AUTH`).

### `GET /api/broker/zerodha/login-url`
Generates the Zerodha Kite OAuth login URL for user authentication.

### `POST /api/broker/zerodha/callback`
Receives authentication callback with `request_token` and binds the user session.

### `POST /api/broker/zerodha/disconnect`
Clears the active broker session.

### `POST /api/broker/zerodha/orders` — **FAIL-CLOSED LIVE ORDER BARRIER**
- **STRICTLY BLOCKED**: Always returns **HTTP 403 Forbidden**.
- **Audit Action**: Logs a security event to `AuditLog`.
- **Response**:
```json
{
  "detail": "Live broker order execution is strictly disabled (Fail-Closed Safety Policy). Use Paper Trading Engine."
}
```

---

## 6. Market Data & CSV Provider

### `POST /api/market/csv/upload`
Uploads and validates custom historical OHLCV CSV content.
- **Validations Enforced**:
  - Required headers: `date/time, open, high, low, close, volume`
  - Timestamp monotonicity (strictly chronological)
  - Price consistency: `high >= low`, `high >= open`, `high >= close`
  - Non-negative volume and prices

### `GET /api/market/csv/datasets`
Lists all validated and ingested custom CSV datasets.

---

## 7. Autonomous Proposals & User Approval

### `GET /api/proposals`
Retrieves generated BUY proposals filtered by status (`PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`).

### `POST /api/proposals/{proposal_id}/approve`
**Mandatory Human Confirmation**: User approves a pending proposal. Triggers deterministic Risk Guardian checks and executes virtual paper trade.

### `POST /api/proposals/{proposal_id}/reject`
User explicitly rejects a proposal with optional feedback notes.

---

## 8. Risk Management Controls

### `GET /api/risk/settings`
Returns current risk settings.

### `PUT /api/risk/settings`
Updates risk parameters (max risk per trade %, max open positions, daily loss limit).

### `POST /api/risk/reset-defaults`
Resets risk limits to the Indian market demo standard:
- Simulated Balance: ₹2,000.00
- Max Risk Per Trade: 0.5% (₹10.00)
- Max Daily Loss: ₹40.00
- Max Concurrent Positions: 1
- Emergency Stop: Inactive
