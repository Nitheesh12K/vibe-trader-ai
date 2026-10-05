"""Continuous Market Monitoring Service for Vibe Trader AI."""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.models.entities import (
    WatchlistInstrument,
    BuyProposal,
    Position,
    Strategy,
    RiskSettings,
    utcnow,
)
from app.services.market_data_service import MarketDataService
from app.services.indicators_service import IndicatorsService
from app.services.pattern_service import PatternService
from app.services.support_resistance_service import SupportResistanceService
from app.services.strategy_engine import StrategyEngine
from app.services.position_monitor import PositionMonitorService
from app.services.audit_service import AuditService

logger = logging.getLogger("vibe-trader-ai.monitoring")


class ContinuousMonitoringService:
    _is_active: bool = True
    _last_scan_timestamp: Optional[datetime] = None

    @classmethod
    def is_active(cls) -> bool:
        return cls._is_active

    @classmethod
    def set_active(cls, active: bool):
        cls._is_active = active

    @classmethod
    def get_last_scan_timestamp(cls) -> Optional[datetime]:
        return cls._last_scan_timestamp

    @classmethod
    def run_market_scan(cls, db: Session) -> Dict[str, Any]:
        """
        Executes a complete scanning cycle:
        1. Updates open positions and evaluates pre-authorized exits.
        2. Expires stale proposals.
        3. Evaluates active watchlist instruments for BUY opportunities.
        """
        cls._last_scan_timestamp = utcnow()
        market_service = MarketDataService(db=db)

        # 1. Fetch current price feed across all instruments
        instruments = market_service.get_instruments()
        price_feed: Dict[str, float] = {inst.symbol: inst.last_price for inst in instruments}

        # 2. Update positions and trigger autonomous SELLs
        exit_actions = PositionMonitorService.update_position_prices_and_evaluate_exits(db, price_feed)

        # 3. Clean up expired proposals
        now = utcnow()
        expired_proposals = db.query(BuyProposal).filter(
            BuyProposal.status == "PENDING",
            BuyProposal.expires_at <= now
        ).all()
        for p in expired_proposals:
            p.status = "EXPIRED"
            AuditService.log_event(
                db=db,
                event_type="PROPOSAL_EXPIRED",
                action=f"Proposal {p.proposal_id} ({p.symbol}) expired without user approval.",
                actor="MONITORING_ENGINE",
                symbol=p.symbol,
                market=p.market,
                proposal_id=p.proposal_id,
            )
        if expired_proposals:
            db.commit()

        # 4. Scan active instruments for new BUY opportunities
        risk_settings = db.query(RiskSettings).first()
        proposals_generated: List[str] = []

        # If emergency stop is active, do not generate new BUY proposals
        if risk_settings and risk_settings.emergency_stop_active:
            logger.info("Emergency Stop active: Skipping opportunity detection.")
            return {
                "scanned_instruments": len(instruments),
                "proposals_generated": 0,
                "exits_evaluated": len(exit_actions),
                "emergency_stop": True,
            }

        active_strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
        primary_strategy = active_strategies[0] if active_strategies else None

        # Sample up to 6 instruments per cycle to ensure snappy response
        sample_instruments = instruments[:6]
        for inst in sample_instruments:
            try:
                ohlc = market_service.get_ohlc(symbol=inst.symbol, timeframe="1D")
                if not ohlc.candles or len(ohlc.candles) < 20:
                    continue

                indicators = IndicatorsService.compute_all_indicators(
                    candles=ohlc.candles,
                    symbol=inst.symbol,
                    timeframe="1D"
                )
                patterns = PatternService.detect_patterns(
                    candles=ohlc.candles,
                    symbol=inst.symbol,
                    timeframe="1D"
                )
                sr = SupportResistanceService.calculate_zones(
                    candles=ohlc.candles,
                    symbol=inst.symbol,
                    timeframe="1D"
                )

                proposal = StrategyEngine.evaluate_opportunity(
                    db=db,
                    symbol=inst.symbol,
                    market=inst.market,
                    timeframe="1D",
                    candles=ohlc.candles,
                    indicators=indicators,
                    patterns=patterns,
                    sr=sr,
                    strategy=primary_strategy,
                )
                if proposal:
                    proposals_generated.append(proposal.proposal_id)
            except Exception as e:
                logger.error(f"Error evaluating opportunities for {inst.symbol}: {e}")

        return {
            "scanned_instruments": len(sample_instruments),
            "proposals_generated": len(proposals_generated),
            "proposal_ids": proposals_generated,
            "exits_evaluated": len(exit_actions),
            "exit_details": exit_actions,
            "timestamp": cls._last_scan_timestamp.isoformat(),
        }
