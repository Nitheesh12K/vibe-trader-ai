"""Market Session Calendar and Trading Schedule Evaluator.
Evaluates time-zone aware sessions for FOREX, NSE, and MCX markets,
including pre-open, normal trading hours, post-close, weekends, and official holidays.
"""
from datetime import datetime, time as dtime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.schemas.market import MarketStatusItem

# Standard fixed Indian national & exchange holidays (YYYY-MM-DD format)
NSE_MCX_HOLIDAYS = {
    "2025-01-26", "2025-03-14", "2025-03-31", "2025-04-14", "2025-04-18",
    "2025-05-01", "2025-08-15", "2025-10-02", "2025-10-21", "2025-11-01",
    "2025-12-25",
    "2026-01-26", "2026-03-03", "2026-03-25", "2026-04-03", "2026-04-14",
    "2026-05-01", "2026-08-15", "2026-10-02", "2026-10-20", "2026-11-08",
    "2026-12-25",
}

# Fixed Indian Standard Time (IST) offset: UTC+05:30
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="IST")


class MarketSessionStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_OPEN = "PRE_OPEN"
    POST_CLOSE = "POST_CLOSE"
    HOLIDAY = "HOLIDAY"


class MarketSessionCalendar:
    """Evaluates session state for financial market segments."""

    @classmethod
    def evaluate_nse(cls, dt_utc: datetime) -> MarketStatusItem:
        """
        Evaluate NSE India trading status.
        Schedule (IST):
          09:00 - 09:15: PRE_OPEN
          09:15 - 15:30: OPEN (Regular market session)
          15:30 - 16:00: POST_CLOSE
          Other hours / Weekends / Holidays: CLOSED / HOLIDAY
        """
        dt_ist = dt_utc.astimezone(IST_TZ)
        date_str = dt_ist.strftime("%Y-%m-%d")
        weekday = dt_ist.weekday()  # Monday is 0, Sunday is 6
        current_time = dt_ist.time()

        session_hours = "09:15 - 15:30 IST (Pre-open 09:00 - 09:15)"
        tz_str = "IST (UTC+05:30)"

        if date_str in NSE_MCX_HOLIDAYS:
            return MarketStatusItem(
                market="NSE",
                label="NSE India",
                status="HOLIDAY",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason=f"Official exchange holiday ({date_str})",
                source="EXCHANGE_SESSION_CALENDAR",
            )

        if weekday >= 5:
            day_name = "Saturday" if weekday == 5 else "Sunday"
            return MarketStatusItem(
                market="NSE",
                label="NSE India",
                status="CLOSED",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason=f"Weekend - Exchange closed ({day_name})",
                source="EXCHANGE_SESSION_CALENDAR",
            )

        if dtime(9, 0) <= current_time < dtime(9, 15):
            return MarketStatusItem(
                market="NSE",
                label="NSE India",
                status="PRE_OPEN",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason="Pre-market order collection & price discovery session",
                source="EXCHANGE_SESSION_CALENDAR",
            )
        elif dtime(9, 15) <= current_time < dtime(15, 30):
            return MarketStatusItem(
                market="NSE",
                label="NSE India",
                status="OPEN",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason="Normal regular market trading session active",
                source="EXCHANGE_SESSION_CALENDAR",
            )
        elif dtime(15, 30) <= current_time < dtime(16, 0):
            return MarketStatusItem(
                market="NSE",
                label="NSE India",
                status="POST_CLOSE",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason="Post-closing session & weighted average settlement",
                source="EXCHANGE_SESSION_CALENDAR",
            )
        else:
            return MarketStatusItem(
                market="NSE",
                label="NSE India",
                status="CLOSED",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason="Outside exchange operating hours (09:15 - 15:30 IST)",
                source="EXCHANGE_SESSION_CALENDAR",
            )

    @classmethod
    def evaluate_mcx(cls, dt_utc: datetime) -> MarketStatusItem:
        """
        Evaluate MCX India Commodity trading status.
        Schedule (IST):
          09:00 - 23:30 (Monday - Friday)
          Weekends: CLOSED
        """
        dt_ist = dt_utc.astimezone(IST_TZ)
        date_str = dt_ist.strftime("%Y-%m-%d")
        weekday = dt_ist.weekday()
        current_time = dt_ist.time()

        session_hours = "09:00 - 23:30 IST (Mon-Fri)"
        tz_str = "IST (UTC+05:30)"

        if date_str in NSE_MCX_HOLIDAYS:
            # On certain national holidays (like Independence Day, Gandhi Jayanti), full day closure
            return MarketStatusItem(
                market="MCX",
                label="MCX India",
                status="HOLIDAY",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason=f"Commodity exchange holiday ({date_str})",
                source="EXCHANGE_SESSION_CALENDAR",
            )

        if weekday >= 5:
            day_name = "Saturday" if weekday == 5 else "Sunday"
            return MarketStatusItem(
                market="MCX",
                label="MCX India",
                status="CLOSED",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason=f"Weekend - Commodity exchange closed ({day_name})",
                source="EXCHANGE_SESSION_CALENDAR",
            )

        if dtime(9, 0) <= current_time < dtime(23, 30):
            return MarketStatusItem(
                market="MCX",
                label="MCX India",
                status="OPEN",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason="Active commodity futures trading session",
                source="EXCHANGE_SESSION_CALENDAR",
            )
        else:
            return MarketStatusItem(
                market="MCX",
                label="MCX India",
                status="CLOSED",
                session_hours=session_hours,
                timezone=tz_str,
                is_demo=True,
                evaluated_at=dt_ist.isoformat(),
                reason="Outside commodity trading hours (09:00 - 23:30 IST)",
                source="EXCHANGE_SESSION_CALENDAR",
            )

    @classmethod
    def evaluate_forex(cls, dt_utc: datetime) -> MarketStatusItem:
        """
        Evaluate Global Forex currency market status.
        Schedule (UTC):
          Continuous 24-hour trading from Sunday 22:00 UTC through Friday 22:00 UTC.
          Closed Friday 22:00 UTC to Sunday 22:00 UTC.
        """
        weekday = dt_utc.weekday()  # Mon 0 ... Sun 6
        current_time = dt_utc.time()

        session_hours = "24 Hours (Sun 22:00 UTC - Fri 22:00 UTC)"
        tz_str = "UTC / Global"

        # Check weekend: Friday 22:00 UTC to Sunday 22:00 UTC
        is_closed = False
        reason = "Continuous 24/5 global interbank trading active"

        if weekday == 4 and current_time >= dtime(22, 0):  # Friday night
            is_closed = True
            reason = "Weekend: Global FX markets closed until Sunday 22:00 UTC"
        elif weekday == 5:  # Saturday full day
            is_closed = True
            reason = "Weekend: Saturday interbank FX closure"
        elif weekday == 6 and current_time < dtime(22, 0):  # Sunday daytime
            is_closed = True
            reason = "Weekend: FX markets open at Sunday 22:00 UTC (Tokyo/Sydney pre-market)"

        return MarketStatusItem(
            market="FOREX",
            label="Forex Global",
            status="CLOSED" if is_closed else "OPEN",
            session_hours=session_hours,
            timezone=tz_str,
            is_demo=True,
            evaluated_at=dt_utc.isoformat(),
            reason=reason,
            source="EXCHANGE_SESSION_CALENDAR",
        )

    @classmethod
    def get_market_status(cls, market: str, current_dt: Optional[datetime] = None) -> MarketStatusItem:
        """Evaluate status for a specific market: NSE, MCX, or FOREX."""
        dt_utc = current_dt.astimezone(timezone.utc) if current_dt else datetime.now(timezone.utc)
        m = market.strip().upper()
        if m == "NSE":
            return cls.evaluate_nse(dt_utc)
        elif m == "MCX":
            return cls.evaluate_mcx(dt_utc)
        elif m in ["FOREX", "FX"]:
            return cls.evaluate_forex(dt_utc)
        else:
            return cls.evaluate_forex(dt_utc)

    @classmethod
    def get_all_market_statuses(cls, current_dt: Optional[datetime] = None) -> List[MarketStatusItem]:
        """
        Returns evaluated market status items for FOREX, NSE, and MCX.
        Accepts optional current_dt parameter for testing deterministic timestamps.
        """
        dt_utc = current_dt.astimezone(timezone.utc) if current_dt else datetime.now(timezone.utc)
        return [
            cls.evaluate_forex(dt_utc),
            cls.evaluate_nse(dt_utc),
            cls.evaluate_mcx(dt_utc),
        ]

