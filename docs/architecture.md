# Vibe Trader AI — Architecture & Multi-Market Design

## Overview
**Vibe Trader AI** is a private, local-first trading research and analysis platform designed for:
1. **Forex**: Global 24/5 currency pairs (e.g., EUR/USD, GBP/USD, USD/JPY, USD/INR).
2. **NSE**: National Stock Exchange of India (NIFTY 50, BANKNIFTY, large-cap equities).
3. **MCX**: Multi Commodity Exchange of India (Gold, Silver, Crude Oil, Natural Gas).

The platform prioritizes local privacy, low latency, robust data isolation, and safety: **AI text and research outputs are strictly decoupled from order routing and can never trigger live trades without human authorization.**

---

## Architectural Layers

```
┌────────────────────────────────────────────────────────┐
│                   React 18 Frontend                    │
│   Tailwind CSS Dark Theme • Lucide • Lightweight Charts │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP / JSON (Future: WS)
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Backend                     │
│  - /api/health (System status & DB check)              │
│  - /api/market/demo (Consolidated dashboard metrics)   │
│  - /api/market/instruments (Segment-filtered catalog)   │
│  - /api/market/ohlc/{symbol} (Candlestick data feed)   │
└───────────────────────────▲────────────────────────────┘
                            │ SQLAlchemy 2.0 ORM
┌───────────────────────────▼────────────────────────────┐
│                  Local SQLite Database                 │
│  data/vibe_trader.db                                   │
│  - user_settings                                       │
│  - watchlist_instruments                               │
│  - strategies                                          │
│  - paper_trades                                        │
│  - trade_journal_entries                               │
└────────────────────────────────────────────────────────┘
```

---

## Multi-Market Data Model

### Data Provider Adapter Pattern
In Phase 1, data is provided through the internal `MarketDataService` and deterministic generator. The architecture is prepared for future modular plug-ins:
- `ForexAdapter`: Real-time FX feeds / tick aggregation
- `NSEAdapter`: Indian market feeds (market hours 09:15 - 15:30 IST)
- `MCXAdapter`: Commodities session (market hours 09:00 - 23:30/23:55 IST)

Each instrument conforms to the unified `InstrumentItem` schema:
```json
{
  "symbol": "NIFTY 50",
  "name": "Nifty 50 Index",
  "market": "NSE",
  "category": "Indices",
  "last_price": 24850.20,
  "change": 142.50,
  "change_percent": 0.58,
  "high_24h": 24900.00,
  "low_24h": 24700.00,
  "volume": "150.2K",
  "currency_symbol": "₹",
  "is_mock": true
}
```

---

## Safety & Security Principles

1. **Local-First Boundary**: Backend binds strictly to `127.0.0.1` and restricts CORS to local Vite ports.
2. **AI Order Decoupling**: AI explanations are informational only. There is no automated execution bridge between LLM outputs and broker APIs.
3. **Explicit Demo Labelling**: All synthetic data, virtual paper trades, and calculated metrics are prominently labelled with `DEMO DATA` / `SIMULATED` badges.
4. **Environment Isolation**: API keys and environment variables are excluded from client code and committed repositories.
