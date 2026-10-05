"""Alert and notification service for Vibe Trader AI.

Evaluates user-configured alert rules against real-time/demo market data,
session schedules, and risk bounds. Handles cooldown debouncing and creates in-app notification events.

NOTE: Under NO circumstances do alert rules execute or place trades.
"""
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.entities import AlertRule, AlertEvent, utcnow
from app.market_data.generator import generate_ohlc_history, get_market_session_info
from app.services.indicators_service import calculate_indicators
from app.services.risk_service import risk_service

logger = logging.getLogger("vibe-trader-ai.alerts")


class AlertService:
    """Service evaluating alert rules and dispatching notifications."""

    def create_rule(
        self,
        db: Session,
        symbol: str,
        market: str,
        alert_type: str,
        condition: str = "TRIGGERED",
        threshold: Optional[float] = None,
        threshold_str: Optional[str] = None,
        cooldown_seconds: int = 60,
        notes: Optional[str] = None,
    ) -> AlertRule:
        """Create a new alert rule."""
        alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
        rule = AlertRule(
            alert_id=alert_id,
            symbol=symbol.strip().upper(),
            market=market.strip().upper(),
            alert_type=alert_type.strip().upper(),
            condition=condition,
            threshold=threshold,
            threshold_str=threshold_str,
            cooldown_seconds=cooldown_seconds,
            notes=notes,
            is_enabled=True,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        logger.info(f"Created alert rule {alert_id} ({alert_type} for {symbol})")
        return rule

    def update_rule(
        self,
        db: Session,
        alert_id: str,
        is_enabled: Optional[bool] = None,
        threshold: Optional[float] = None,
        threshold_str: Optional[str] = None,
        cooldown_seconds: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[AlertRule]:
        """Update existing alert rule."""
        rule = db.query(AlertRule).filter(
            (AlertRule.alert_id == alert_id) | (AlertRule.id == int(alert_id) if alert_id.isdigit() else False)
        ).first()
        if not rule:
            return None

        if is_enabled is not None:
            rule.is_enabled = is_enabled
        if threshold is not None:
            rule.threshold = threshold
        if threshold_str is not None:
            rule.threshold_str = threshold_str
        if cooldown_seconds is not None:
            rule.cooldown_seconds = cooldown_seconds
        if notes is not None:
            rule.notes = notes

        rule.updated_at = utcnow()
        db.commit()
        db.refresh(rule)
        return rule

    def delete_rule(self, db: Session, alert_id: str) -> bool:
        """Delete an alert rule and associated events."""
        rule = db.query(AlertRule).filter(
            (AlertRule.alert_id == alert_id) | (AlertRule.id == int(alert_id) if alert_id.isdigit() else False)
        ).first()
        if not rule:
            return False

        db.delete(rule)
        db.commit()
        return True

    def get_rules(self, db: Session, symbol: Optional[str] = None) -> List[AlertRule]:
        """Fetch all configured alert rules."""
        query = db.query(AlertRule)
        if symbol:
            query = query.filter(func.upper(AlertRule.symbol) == symbol.strip().upper())
        return query.order_by(AlertRule.created_at.desc()).all()

    def get_events(self, db: Session, unread_only: bool = False, limit: int = 50) -> List[AlertEvent]:
        """Fetch triggered alert events / notification history."""
        query = db.query(AlertEvent)
        if unread_only:
            query = query.filter(AlertEvent.is_read == False)
        return query.order_by(AlertEvent.triggered_at.desc()).limit(limit).all()

    def mark_event_read(self, db: Session, event_id: str) -> bool:
        """Mark an alert event notification as read."""
        event = db.query(AlertEvent).filter(
            (AlertEvent.event_id == event_id) | (AlertEvent.id == int(event_id) if event_id.isdigit() else False)
        ).first()
        if not event:
            return False
        event.is_read = True
        db.commit()
        return True

    def clear_all_events(self, db: Session) -> int:
        """Clear all notification events."""
        count = db.query(AlertEvent).delete()
        db.commit()
        return count

    def dispatch_event(
        self,
        db: Session,
        alert_type: str,
        title: str,
        message: str,
        symbol: Optional[str] = None,
        market: Optional[str] = None,
        severity: str = "INFO",
        details: Optional[Dict[str, Any]] = None,
        alert_rule_id: Optional[int] = None,
    ) -> AlertEvent:
        """Create and persist an in-app notification event."""
        event = AlertEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            alert_rule_id=alert_rule_id,
            alert_type=alert_type,
            symbol=symbol,
            market=market or "ALL",
            title=title,
            message=message,
            severity=severity,
            details_json=json.dumps(details or {}),
            is_read=False,
            triggered_at=utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def evaluate_active_rules(self, db: Session) -> List[AlertEvent]:
        """
        Evaluate all active rules against current market prices and state.
        Debounces triggers using cooldown_seconds.
        """
        rules = db.query(AlertRule).filter(AlertRule.is_enabled == True).all()
        now = utcnow()
        triggered_events: List[AlertEvent] = []

        for rule in rules:
            # Cooldown check
            if rule.last_triggered_at:
                elapsed = (now - rule.last_triggered_at).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    continue

            is_triggered = False
            title = ""
            msg = ""
            severity = "INFO"
            details: Dict[str, Any] = {}

            try:
                # 1. Price checks
                if rule.alert_type in {"PRICE_ABOVE", "PRICE_BELOW"}:
                    candles = generate_ohlc_history(rule.symbol, rule.market, timeframe="1D", count=5)
                    if candles:
                        curr_price = candles[-1]["close"]
                        details["current_price"] = curr_price
                        details["threshold"] = rule.threshold

                        if rule.alert_type == "PRICE_ABOVE" and rule.threshold is not None:
                            if curr_price >= rule.threshold:
                                is_triggered = True
                                title = f"Price Alert: {rule.symbol} crossed above {rule.threshold}"
                                msg = f"{rule.symbol} price reached ₹{curr_price:.2f} (above target ₹{rule.threshold:.2f})."
                        elif rule.alert_type == "PRICE_BELOW" and rule.threshold is not None:
                            if curr_price <= rule.threshold:
                                is_triggered = True
                                title = f"Price Alert: {rule.symbol} dropped below {rule.threshold}"
                                msg = f"{rule.symbol} price reached ₹{curr_price:.2f} (below target ₹{rule.threshold:.2f})."

                # 2. RSI Threshold check
                elif rule.alert_type == "RSI_THRESHOLD":
                    candles = generate_ohlc_history(rule.symbol, rule.market, timeframe="1D", count=60)
                    if len(candles) >= 15:
                        inds = calculate_indicators(candles, rule.symbol, "1D")
                        rsi_list = inds.rsi
                        if rsi_list:
                            pt = rsi_list[-1]
                            latest_rsi = getattr(pt, "value", None) if not isinstance(pt, dict) else pt.get("value")
                            if latest_rsi is not None:
                                details["latest_rsi"] = latest_rsi
                                details["threshold"] = rule.threshold
                                cond = rule.condition.strip()

                                if (cond in {"<", "BELOW"} and latest_rsi <= (rule.threshold or 30)) or \
                                   (cond in {">", "ABOVE"} and latest_rsi >= (rule.threshold or 70)):
                                    is_triggered = True
                                    title = f"RSI Indicator Alert: {rule.symbol}"
                                    msg = f"RSI(14) for {rule.symbol} hit {latest_rsi:.1f} (condition: {cond} {rule.threshold})."

                # 3. Market Session alerts
                elif rule.alert_type in {"MARKET_SESSION_OPEN", "MARKET_SESSION_CLOSE"}:
                    s_info = get_market_session_info(rule.market)
                    status_now = s_info.get("status")
                    if rule.alert_type == "MARKET_SESSION_OPEN" and status_now == "OPEN":
                        is_triggered = True
                        title = f"Market Session Open: {rule.market}"
                        msg = f"{rule.market} regular trading session is now OPEN ({s_info.get('session_hours')})."
                    elif rule.alert_type == "MARKET_SESSION_CLOSE" and status_now == "CLOSED":
                        is_triggered = True
                        title = f"Market Session Closed: {rule.market}"
                        msg = f"{rule.market} session is now CLOSED."

                # 4. Daily Loss Limit Alert
                elif rule.alert_type == "DAILY_LOSS_LIMIT":
                    risk_st = risk_service.get_risk_settings(db)
                    details["max_daily_loss"] = risk_st.max_daily_loss
                    # Check emergency stop or loss
                    if risk_st.emergency_stop_active:
                        is_triggered = True
                        severity = "CRITICAL"
                        title = "Emergency Stop Active"
                        msg = "Global emergency stop is engaged! All new paper order proposals are halted."

            except Exception as e:
                logger.debug(f"Rule evaluation check skipped for {rule.alert_id}: {e}")

            if is_triggered:
                rule.last_triggered_at = now
                rule.trigger_count += 1
                db.commit()

                event = self.dispatch_event(
                    db=db,
                    alert_type=rule.alert_type,
                    title=title,
                    message=msg,
                    symbol=rule.symbol,
                    market=rule.market,
                    severity=severity,
                    details=details,
                    alert_rule_id=rule.id,
                )
                triggered_events.append(event)

        return triggered_events


alert_service = AlertService()
