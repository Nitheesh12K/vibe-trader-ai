"""Mock market data generator for Forex, NSE, and MCX instruments."""
import math
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.schemas.market import (
    InstrumentItem,
    MarketStatusItem,
    OHLCCandle,
    PortfolioSummary,
    ActivityItem,
    AIInsightSummary,
)

# Reference baseline instruments
INSTRUMENT_CATALOG: List[Dict[str, Any]] = [
    # Forex
    {
        "symbol": "EUR/USD",
        "name": "Euro / US Dollar",
        "market": "FOREX",
        "category": "Currencies",
        "base_price": 1.0850,
        "currency_symbol": "$",
        "volatility": 0.0008,
        "decimals": 4,
    },
    {
        "symbol": "GBP/USD",
        "name": "British Pound / US Dollar",
        "market": "FOREX",
        "category": "Currencies",
        "base_price": 1.2980,
        "currency_symbol": "$",
        "volatility": 0.0012,
        "decimals": 4,
    },
    {
        "symbol": "USD/JPY",
        "name": "US Dollar / Japanese Yen",
        "market": "FOREX",
        "category": "Currencies",
        "base_price": 151.40,
        "currency_symbol": "¥",
        "volatility": 0.15,
        "decimals": 2,
    },
    {
        "symbol": "USD/INR",
        "name": "US Dollar / Indian Rupee",
        "market": "FOREX",
        "category": "Currencies",
        "base_price": 83.75,
        "currency_symbol": "₹",
        "volatility": 0.08,
        "decimals": 2,
    },
    # NSE Equities & Indices
    {
        "symbol": "NIFTY 50",
        "name": "Nifty 50 Index",
        "market": "NSE",
        "category": "Indices",
        "base_price": 24850.20,
        "currency_symbol": "₹",
        "volatility": 45.0,
        "decimals": 2,
    },
    {
        "symbol": "BANKNIFTY",
        "name": "Nifty Bank Index",
        "market": "NSE",
        "category": "Indices",
        "base_price": 51200.75,
        "currency_symbol": "₹",
        "volatility": 85.0,
        "decimals": 2,
    },
    {
        "symbol": "RELIANCE",
        "name": "Reliance Industries Ltd",
        "market": "NSE",
        "category": "Equities",
        "base_price": 2960.50,
        "currency_symbol": "₹",
        "volatility": 12.0,
        "decimals": 2,
    },
    {
        "symbol": "TCS",
        "name": "Tata Consultancy Services",
        "market": "NSE",
        "category": "Equities",
        "base_price": 4210.00,
        "currency_symbol": "₹",
        "volatility": 15.0,
        "decimals": 2,
    },
    {
        "symbol": "INFY",
        "name": "Infosys Ltd",
        "market": "NSE",
        "category": "Equities",
        "base_price": 1895.80,
        "currency_symbol": "₹",
        "volatility": 8.5,
        "decimals": 2,
    },
    {
        "symbol": "HDFCBANK",
        "name": "HDFC Bank Ltd",
        "market": "NSE",
        "category": "Equities",
        "base_price": 1655.00,
        "currency_symbol": "₹",
        "volatility": 7.0,
        "decimals": 2,
    },
    # MCX Commodities
    {
        "symbol": "GOLD",
        "name": "Gold 1kg Futures",
        "market": "MCX",
        "category": "Commodities",
        "base_price": 74800.00,
        "currency_symbol": "₹",
        "volatility": 120.0,
        "decimals": 2,
    },
    {
        "symbol": "SILVER",
        "name": "Silver 1kg Futures",
        "market": "MCX",
        "category": "Commodities",
        "base_price": 89200.00,
        "currency_symbol": "₹",
        "volatility": 250.0,
        "decimals": 2,
    },
    {
        "symbol": "CRUDEOIL",
        "name": "Crude Oil 100 BBL Futures",
        "market": "MCX",
        "category": "Commodities",
        "base_price": 6250.00,
        "currency_symbol": "₹",
        "volatility": 35.0,
        "decimals": 2,
    },
    {
        "symbol": "NATURALGAS",
        "name": "Natural Gas Futures",
        "market": "MCX",
        "category": "Commodities",
        "base_price": 195.40,
        "currency_symbol": "₹",
        "volatility": 2.5,
        "decimals": 2,
    },
]


def generate_instruments() -> List[InstrumentItem]:
    """Generate realistic mock instruments with calculated 24h changes."""
    instruments = []
    # Seed based on current hour to have slight realistic variation
    rng = random.Random(42)

    for item in INSTRUMENT_CATALOG:
        delta_pct = rng.uniform(-1.8, 2.4)
        base = item["base_price"]
        dec = item["decimals"]
        change = round(base * (delta_pct / 100.0), dec)
        last_price = round(base + change, dec)
        spread = abs(change) * 1.5 + (base * 0.003)
        high = round(max(last_price, base) + spread * 0.6, dec)
        low = round(min(last_price, base) - spread * 0.4, dec)

        vol_val = rng.randint(12000, 950000)
        volume_str = f"{vol_val / 1000:.1f}K" if vol_val < 1000000 else f"{vol_val / 1000000:.2f}M"

        instruments.append(
            InstrumentItem(
                symbol=item["symbol"],
                name=item["name"],
                market=item["market"],
                category=item["category"],
                last_price=last_price,
                change=change,
                change_percent=round(delta_pct, 2),
                high_24h=high,
                low_24h=low,
                volume=volume_str,
                currency_symbol=item["currency_symbol"],
                is_mock=True,
            )
        )
    return instruments


def get_market_statuses(current_dt: Optional[datetime] = None) -> List[MarketStatusItem]:
    """Calculate market trading status based on real session hours, timezone, and calendar schedule."""
    from app.market_data.session_calendar import MarketSessionCalendar
    return MarketSessionCalendar.get_all_market_statuses(current_dt=current_dt)


def generate_ohlc_history(symbol: str, *args, **kwargs) -> List[OHLCCandle]:
    """Generate deterministic, smooth historical candlestick data for Lightweight Charts."""
    count = kwargs.get("count", 100)
    if "count" not in kwargs:
        for a in args:
            if isinstance(a, int):
                count = a
                break
    clean_sym = symbol.upper().replace("_", "/").strip()
    # Lookup base price
    item = next((x for x in INSTRUMENT_CATALOG if x["symbol"].upper() == clean_sym), None)
    if not item:
        # Fallback partial match
        item = next((x for x in INSTRUMENT_CATALOG if x["symbol"].upper().replace("/", "") == clean_sym.replace("/", "")), None)
    if not item:
        item = INSTRUMENT_CATALOG[0]

    base_price = item["base_price"]
    volatility = item["volatility"]
    decimals = item["decimals"]

    candles: List[OHLCCandle] = []
    # Work backwards from current day aligned to 86400 seconds
    interval = 86400
    current_time = (int(time.time()) // interval) * interval
    start_time = current_time - (count * interval)

    # Use a deterministic PRNG for the symbol
    seed = sum(ord(c) for c in symbol) + 1337
    rng = random.Random(seed)

    price = base_price * 0.95  # start slightly lower and trend
    for i in range(count):
        candle_time = start_time + (i * interval)
        # Random walk with mean reversion toward base_price
        drift = (base_price - price) * 0.05
        step = rng.gauss(0, volatility) + drift
        open_p = price
        close_p = open_p + step

        # High and Low wicks
        wick_high = abs(rng.gauss(0, volatility * 0.8))
        wick_low = abs(rng.gauss(0, volatility * 0.8))
        high_p = max(open_p, close_p) + wick_high
        low_p = min(open_p, close_p) - wick_low

        volume = round(rng.uniform(1000, 50000) * (base_price / 100))

        candles.append(
            OHLCCandle(
                time=candle_time,
                open=round(open_p, decimals),
                high=round(high_p, decimals),
                low=round(low_p, decimals),
                close=round(close_p, decimals),
                volume=volume,
            )
        )
        price = close_p

    return candles


def get_demo_portfolio() -> PortfolioSummary:
    """Return mock portfolio metrics clearly marked as demo."""
    return PortfolioSummary(
        total_value=28450.00,
        available_cash=11200.00,
        daily_pnl=420.50,
        daily_pnl_percent=1.50,
        open_positions_count=4,
        active_strategies_count=3,
        currency="USD",
        is_mock=True,
    )


def get_demo_activities() -> List[ActivityItem]:
    """Return simulated paper trades and activity entries."""
    return [
        ActivityItem(
            id="act-1",
            symbol="EUR/USD",
            market="FOREX",
            type="PAPER_TRADE",
            side="BUY",
            quantity=10000.0,
            price=1.0825,
            pnl=25.00,
            status="OPEN",
            timestamp="2026-09-30 14:15",
            is_mock=True,
        ),
        ActivityItem(
            id="act-2",
            symbol="RELIANCE",
            market="NSE",
            type="PAPER_TRADE",
            side="BUY",
            quantity=50.0,
            price=2940.00,
            pnl=1025.00,
            status="OPEN",
            timestamp="2026-09-30 11:30",
            is_mock=True,
        ),
        ActivityItem(
            id="act-3",
            symbol="GOLD",
            market="MCX",
            type="PAPER_TRADE",
            side="SELL",
            quantity=1.0,
            price=74950.00,
            pnl=-150.00,
            status="CLOSED",
            timestamp="2026-09-30 10:05",
            is_mock=True,
        ),
        ActivityItem(
            id="act-4",
            symbol="NIFTY 50",
            market="NSE",
            type="SIGNAL",
            side="INFO",
            quantity=0.0,
            price=24800.00,
            pnl=None,
            status="TRIGGERED",
            timestamp="2026-09-30 09:20",
            is_mock=True,
        ),
    ]


def get_demo_ai_insight() -> AIInsightSummary:
    """Return a demo AI research explanation snippet."""
    return AIInsightSummary(
        title="Multi-Market Liquidity & Momentum Overview",
        sentiment="Bullish",
        confidence=0.78,
        summary=(
            "Demo AI Analysis: Asian & Indian sessions (NSE) displayed steady accumulation in large-cap energy and "
            "banking sectors with NIFTY holding support above 24,750. Commodity markets (MCX Gold) consolidated in a tight "
            "range amid dollar index stabilization. Forex pairs EUR/USD and GBP/USD remain range-bound prior to upcoming central bank releases."
        ),
        timestamp="2026-09-30 15:00 UTC",
        disclaimer="DEMO DATA: Educational & research overview only. Never triggers automated or live trades.",
    )


def get_market_session_info(market: str) -> Dict[str, Any]:
    """Return dictionary session info for a given market (FOREX, NSE, MCX)."""
    from app.market_data.session_calendar import MarketSessionCalendar
    item = MarketSessionCalendar.get_market_status(market)
    return {
        "market": item.market,
        "label": item.label,
        "status": item.status,
        "session_hours": item.session_hours,
        "timezone": item.timezone,
        "reason": item.reason,
        "is_demo": item.is_demo,
        "evaluated_at": item.evaluated_at,
    }
