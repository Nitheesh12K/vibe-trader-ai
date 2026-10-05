"""Market data generator and provider adapters."""
from app.market_data.generator import (
    generate_instruments,
    get_market_statuses,
    generate_ohlc_history,
    get_demo_portfolio,
    get_demo_activities,
    get_demo_ai_insight,
)

__all__ = [
    "generate_instruments",
    "get_market_statuses",
    "generate_ohlc_history",
    "get_demo_portfolio",
    "get_demo_activities",
    "get_demo_ai_insight",
]
