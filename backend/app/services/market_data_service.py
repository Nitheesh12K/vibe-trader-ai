"""Market data service providing business logic for market information."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.market_data.generator import (
    generate_instruments,
    get_market_statuses,
    generate_ohlc_history,
    get_demo_portfolio,
    get_demo_activities,
    get_demo_ai_insight,
)
from app.models.entities import WatchlistInstrument
from app.schemas.market import (
    DashboardSummaryResponse,
    InstrumentItem,
    MarketStatusItem,
    OHLCResponse,
)


class MarketDataService:
    """Service handling multi-market instruments and charts."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def seed_initial_instruments_if_needed(self) -> None:
        """Seed SQLite with initial watchlist items if table is empty."""
        if not self.db:
            return

        count = self.db.query(WatchlistInstrument).count()
        if count == 0:
            demo_items = generate_instruments()
            for item in demo_items:
                inst = WatchlistInstrument(
                    symbol=item.symbol,
                    name=item.name,
                    market=item.market,
                    category=item.category,
                    is_active=True,
                )
                self.db.add(inst)
            self.db.commit()

    def get_dashboard_summary(self) -> DashboardSummaryResponse:
        """Fetch consolidated demo dashboard data."""
        self.seed_initial_instruments_if_needed()
        return DashboardSummaryResponse(
            portfolio=get_demo_portfolio(),
            market_statuses=get_market_statuses(),
            instruments=generate_instruments(),
            recent_activity=get_demo_activities(),
            ai_insight=get_demo_ai_insight(),
            is_demo=True,
        )

    def get_instruments(self, market: Optional[str] = None) -> List[InstrumentItem]:
        """Fetch instruments filtered optionally by market (FOREX, NSE, MCX)."""
        instruments = generate_instruments()
        if market and market.upper() != "ALL":
            return [i for i in instruments if i.market.upper() == market.upper()]
        return instruments

    def get_ohlc(self, symbol: str, timeframe: str = "1D") -> OHLCResponse:
        """Fetch historical candlestick data for a symbol (custom dataset or generated market baseline)."""
        from app.services.csv_data_provider import CSVDataProvider
        custom_candles = CSVDataProvider.get_dataset(symbol=symbol, db=self.db)
        if custom_candles:
            market = "CUSTOM"
            dataset_timeframe = "1D"
            if self.db:
                rec = CSVDataProvider.get_dataset_record(self.db, symbol)
                if rec and rec.market:
                    market = rec.market
                if rec and rec.timeframe:
                    dataset_timeframe = rec.timeframe
            return OHLCResponse(
                symbol=symbol.upper(),
                market=market,
                timeframe=dataset_timeframe,
                is_mock=False,
                candles=custom_candles,
            )

        candles = generate_ohlc_history(symbol=symbol, count=120)
        # Determine market
        instruments = generate_instruments()
        matched = next((i for i in instruments if i.symbol.upper() == symbol.upper()), None)
        market = matched.market if matched else "FOREX"

        return OHLCResponse(
            symbol=symbol.upper(),
            market=market,
            timeframe=timeframe,
            is_mock=True,
            candles=candles,
        )

