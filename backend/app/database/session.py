"""Database engine, session management, and safe schema migration."""
import os
import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.database.base import Base

logger = logging.getLogger("vibe-trader-ai.database")

# Ensure the database directory exists if using SQLite file
if settings.DATABASE_URL.startswith("sqlite"):
    db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")
    db_path = Path(db_path_str)
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Create SQLite engine with thread safety for FastAPI async endpoints
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_sqlite_schema() -> None:
    """Safely apply non-destructive column additions to existing SQLite tables."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    migrations = [
        # Table, Column, Type, Default
        ("user_settings", "default_timeframe", "VARCHAR(20)", "'1D'"),
        ("user_settings", "risk_percentage", "FLOAT", "1.0"),
        ("watchlist_instruments", "exchange", "VARCHAR(50)", "NULL"),
        ("watchlist_instruments", "order_index", "INTEGER", "0"),
        ("watchlist_instruments", "notes", "TEXT", "NULL"),
        ("watchlist_instruments", "group_name", "VARCHAR(100)", "'Default Watchlist'"),
        ("paper_trades", "stop_loss", "FLOAT", "NULL"),
        ("paper_trades", "take_profit", "FLOAT", "NULL"),
        ("paper_trades", "notes", "TEXT", "NULL"),
        ("trade_journal_entries", "symbol", "VARCHAR(50)", "NULL"),
        ("trade_journal_entries", "lessons_learned", "TEXT", "NULL"),
        ("chat_message_records", "detected_language", "VARCHAR(20)", "'english'"),
        ("chat_message_records", "detected_intent", "VARCHAR(50)", "'GENERAL_CHAT'"),
        ("chat_message_records", "routing_time_ms", "FLOAT", "0.0"),
        ("chat_message_records", "tool_latency_ms", "FLOAT", "0.0"),
        ("chat_message_records", "inference_latency_ms", "FLOAT", "0.0"),
        ("chat_message_records", "total_latency_ms", "FLOAT", "0.0"),
    ]

    with engine.connect() as conn:
        for table, col, col_type, default_val in migrations:
            try:
                # Check if table exists
                tbl_check = conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                ).fetchone()
                if not tbl_check:
                    continue

                # Check existing columns
                cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                existing_col_names = [c[1] for c in cols]
                if col not in existing_col_names:
                    logger.info(f"Applying SQLite migration: Adding column {col} to {table}")
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default_val}")
                    )
                    conn.commit()
            except Exception as e:
                logger.warning(f"Column migration warning for {table}.{col}: {e}")


def seed_defaults(db: Session) -> None:
    """Ensure essential default records exist (e.g. user settings, sample strategy)."""
    from app.models.entities import UserSettings, Strategy, WatchlistInstrument
    from app.market_data.generator import INSTRUMENT_CATALOG

    # 1. Default user settings
    settings_count = db.query(UserSettings).count()
    if settings_count == 0:
        logger.info("Seeding default user settings...")
        default_settings = UserSettings(
            theme="dark",
            default_market="ALL",
            default_timeframe="1D",
            risk_percentage=1.0,
            notifications_enabled=True,
        )
        db.add(default_settings)
        db.commit()

    # 2. Initial watchlist instruments if empty
    wl_count = db.query(WatchlistInstrument).count()
    if wl_count == 0:
        logger.info("Seeding initial watchlist instruments...")
        for item in INSTRUMENT_CATALOG:
            db.add(
                WatchlistInstrument(
                    symbol=item["symbol"],
                    name=item["name"],
                    market=item["market"],
                    category=item["category"],
                    exchange=item["market"],
                    is_active=True,
                )
            )
        db.commit()

    # 3. Initial sample strategies if empty
    strat_count = db.query(Strategy).count()
    if strat_count == 0:
        logger.info("Seeding initial strategies...")
        db.add(
            Strategy(
                name="EMA Momentum Trend Following",
                description="20/50 Exponential Moving Average breakout strategy with dynamic ATR trailing stop.",
                market="ALL",
                timeframe="1D",
                parameters_json='{"fast_ema": 20, "slow_ema": 50, "atr_period": 14, "risk_reward": 2.0}',
                is_active=True,
            )
        )
        db.add(
            Strategy(
                name="NIFTY Mean Reversion RSI",
                description="RSI divergence and Bollinger Band touch setup for Indian benchmark index.",
                market="NSE",
                timeframe="15m",
                parameters_json='{"rsi_period": 14, "oversold": 30, "overbought": 70, "bb_period": 20}',
                is_active=True,
            )
        )
        db.add(
            Strategy(
                name="MCX Crude Oil Breakout",
                description="Intraday opening range breakout (ORB) on commodities session open.",
                market="MCX",
                timeframe="5m",
                parameters_json='{"orb_minutes": 30, "breakout_buffer_pct": 0.15}',
                is_active=False,
            )
        )
        db.commit()

    # 4. Default Risk Settings if empty
    from app.models.entities import RiskSettings, AutonomousExitPermission
    risk_count = db.query(RiskSettings).count()
    if risk_count == 0:
        logger.info("Seeding default risk settings...")
        db.add(
            RiskSettings(
                simulated_balance=100000.0,
                max_risk_per_trade_pct=2.0,
                max_daily_loss=5000.0,
                max_open_positions=5,
                max_position_size_pct=20.0,
                emergency_stop_active=False,
            )
        )
        db.commit()

    # 5. Default Autonomous Exit Permissions if empty
    perm_count = db.query(AutonomousExitPermission).count()
    if perm_count == 0:
        logger.info("Seeding default autonomous exit permissions...")
        db.add(
            AutonomousExitPermission(
                is_enabled=True,
                allow_stop_loss=True,
                allow_take_profit=True,
                allow_strategy_exit=True,
                allow_max_drawdown=True,
                max_position_scope="ALL",
                emergency_risk_limit_pct=5.0,
            )
        )
        db.commit()

    # 6. Default Strategy Candidates for Controlled Lifecycle
    from app.models.entities import StrategyCandidate
    cand_count = db.query(StrategyCandidate).count()
    if cand_count == 0:
        logger.info("Seeding initial strategy candidates...")
        db.add(
            StrategyCandidate(
                candidate_id="CAND-EMA-ADAPT-01",
                name="Adaptive Volatility EMA Trend",
                version="v1.1.0-rc1",
                market="FOREX",
                timeframe="1D",
                parameters_json='{"fast_ema": 12, "slow_ema": 26, "atr_multiplier": 1.75, "risk_reward": 2.2}',
                rationale="Learning Agent detected that narrowing fast EMA from 20 to 12 improves early entry responsiveness during high momentum regimes without degrading win rate.",
                lifecycle_stage="SANDBOX",
                validation_metrics_json='{"backtest_win_rate": 62.5, "profit_factor": 1.85, "expectancy": 240.50, "max_drawdown_pct": 3.4}',
                is_active=False,
            )
        )
        db.add(
            StrategyCandidate(
                candidate_id="CAND-NIFTY-RSI-02",
                name="NIFTY Dynamic RSI Reversal",
                version="v2.0.0-beta",
                market="NSE",
                timeframe="15m",
                parameters_json='{"rsi_period": 10, "oversold": 28, "overbought": 72, "bb_period": 20}',
                rationale="Proposal to tighten RSI bands from 30/70 to 28/72 to filter out premature reversals during strong institutional trends.",
                lifecycle_stage="CANDIDATE",
                validation_metrics_json='{"backtest_win_rate": 58.0, "profit_factor": 1.60, "expectancy": 180.00, "max_drawdown_pct": 4.1}',
                is_active=False,
            )
        )
        db.commit()

    # 7. Default Watchlist Group
    from app.models.entities import WatchlistGroup, AlertRule
    grp_count = db.query(WatchlistGroup).count()
    if grp_count == 0:
        db.add(WatchlistGroup(name="Default Watchlist", description="Core multi-market research list", is_default=True))
        db.add(WatchlistGroup(name="High Momentum", description="Equities exhibiting strong breakout trends", is_default=False))
        db.commit()

    # 8. Default Alert Rules
    alert_count = db.query(AlertRule).count()
    if alert_count == 0:
        db.add(
            AlertRule(
                alert_id="ALERT-REL-01",
                symbol="RELIANCE",
                market="NSE",
                alert_type="PRICE_ABOVE",
                condition=">",
                threshold=3000.0,
                notes="Alert if RELIANCE breaks above psychological level of 3000.",
                is_enabled=True,
            )
        )
        db.add(
            AlertRule(
                alert_id="ALERT-RSI-02",
                symbol="EUR/USD",
                market="FOREX",
                alert_type="RSI_THRESHOLD",
                condition="<",
                threshold=30.0,
                notes="Oversold RSI condition on EUR/USD.",
                is_enabled=True,
            )
        )
        db.add(
            AlertRule(
                alert_id="ALERT-RISK-03",
                symbol="GLOBAL",
                market="ALL",
                alert_type="DAILY_LOSS_LIMIT",
                condition="TRIGGERED",
                threshold=5000.0,
                notes="Safety notification if daily loss ceiling is approached.",
                is_enabled=True,
            )
        )
        db.commit()



def init_db() -> None:
    """Initialize database tables according to declared models and run safe migrations."""
    import app.models.entities  # Ensure models are imported
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema()

    with SessionLocal() as db:
        seed_defaults(db)
