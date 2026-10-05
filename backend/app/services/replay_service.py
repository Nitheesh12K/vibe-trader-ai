"""Historical Market Replay Simulator Service for Vibe Trader AI.

Enables step-by-step chronological paper trading on historical candle data.
Guarantees NO future leakage (strictly causal indicators and signals).
Runs entirely isolated from live/standard paper trading state.
"""
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.entities import ReplaySession, CustomDataset, utcnow
from app.market_data.generator import generate_ohlc_history
from app.services.indicators_service import calculate_indicators

logger = logging.getLogger("vibe-trader-ai.replay")


class ReplayService:
    """Service managing chronological market replay simulations."""

    def __init__(self):
        pass

    def create_session(
        self,
        db: Session,
        symbol: str,
        market: str = "NSE",
        dataset_id: Optional[str] = None,
        timeframe: str = "1D",
        initial_capital: float = 100000.0,
        name: str = "Replay Session",
    ) -> ReplaySession:
        """Initialize a new replay session with historical candles."""
        session_id = f"REPLAY-{uuid.uuid4().hex[:8].upper()}"

        candles: List[Dict[str, Any]] = []
        if dataset_id:
            ds = db.query(CustomDataset).filter(CustomDataset.dataset_id == dataset_id).first()
            if ds:
                try:
                    candles = json.loads(ds.candles_json)
                except Exception:
                    candles = []
        
        if not candles:
            # Generate deterministic calibrated historical replay series
            raw_candles = generate_ohlc_history(symbol, market, timeframe=timeframe, count=150)
            candles = [
                {
                    "time": c["time"],
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                    "volume": float(c.get("volume", 1000)),
                }
                for c in raw_candles
            ]

        # Minimum 20 warmup candles required for initial indicators
        initial_idx = min(20, len(candles) - 1) if len(candles) > 20 else 0

        initial_state = {
            "all_candles": candles,
            "open_positions": [],
            "closed_trades": [],
            "pending_proposal": None,
            "current_signal": None,
            "equity_history": [{"index": initial_idx, "equity": initial_capital, "pnl": 0.0}],
        }

        session = ReplaySession(
            session_id=session_id,
            name=name,
            symbol=symbol.strip().upper(),
            market=market.strip().upper(),
            dataset_id=dataset_id,
            timeframe=timeframe,
            initial_capital=initial_capital,
            virtual_balance=initial_capital,
            realized_pnl=0.0,
            total_candles=len(candles),
            current_index=initial_idx,
            status="PAUSED",
            speed_ms=1000,
            state_json=json.dumps(initial_state),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info(f"Initialized replay session {session_id} for {symbol} ({len(candles)} candles)")
        return session

    def get_session(self, db: Session, session_id: str) -> Optional[ReplaySession]:
        """Fetch replay session by session_id."""
        return db.query(ReplaySession).filter(
            (ReplaySession.session_id == session_id) | (ReplaySession.id == int(session_id) if session_id.isdigit() else False)
        ).first()

    def step(self, db: Session, session_id: str, step_count: int = 1) -> Optional[Dict[str, Any]]:
        """
        Advance replay by `step_count` candles chronologically.
        Computes causal indicators, evaluates strategy signals, updates open positions,
        and triggers stop-loss / take-profit exits.
        """
        session = self.get_session(db, session_id)
        if not session:
            return None

        state = json.loads(session.state_json)
        all_candles = state.get("all_candles", [])
        total = len(all_candles)
        if total == 0:
            return None

        new_idx = min(session.current_index + step_count, total - 1)
        session.current_index = new_idx
        if new_idx >= total - 1:
            session.status = "COMPLETED"

        # 1. Strictly causal candle slice (NO future data leakage!)
        visible_candles = all_candles[: new_idx + 1]
        current_candle = visible_candles[-1]
        current_price = current_candle["close"]

        # 2. Check and update open positions
        open_positions = state.get("open_positions", [])
        closed_trades = state.get("closed_trades", [])
        unrealized_pnl = 0.0
        remaining_positions = []

        for pos in open_positions:
            entry = pos["entry_price"]
            qty = pos["quantity"]
            side = pos.get("side", "LONG")
            sl = pos.get("stop_loss", entry * 0.98)
            tp = pos.get("target", entry * 1.04)

            # High/Low during current candle
            c_high = current_candle["high"]
            c_low = current_candle["low"]

            # Exit checks
            exited = False
            exit_price = current_price
            exit_reason = ""

            if side == "LONG":
                if c_low <= sl:
                    exited = True
                    exit_price = sl
                    exit_reason = "STOP_LOSS"
                elif c_high >= tp:
                    exited = True
                    exit_price = tp
                    exit_reason = "TAKE_PROFIT"
                pos_pnl = (exit_price - entry) * qty
            else:
                if c_high >= sl:
                    exited = True
                    exit_price = sl
                    exit_reason = "STOP_LOSS"
                elif c_low <= tp:
                    exited = True
                    exit_price = tp
                    exit_reason = "TAKE_PROFIT"
                pos_pnl = (entry - exit_price) * qty

            if exited:
                commission = exit_price * qty * 0.0003
                net_pnl = pos_pnl - commission
                session.realized_pnl += net_pnl
                session.virtual_balance += (entry * qty) + net_pnl
                closed_trades.append({
                    "position_id": pos["position_id"],
                    "symbol": pos["symbol"],
                    "side": side,
                    "entry_price": entry,
                    "exit_price": exit_price,
                    "quantity": qty,
                    "pnl": round(net_pnl, 2),
                    "exit_reason": exit_reason,
                    "candle_index": new_idx,
                })
            else:
                cur_pos_pnl = (current_price - entry) * qty if side == "LONG" else (entry - current_price) * qty
                pos["current_price"] = current_price
                pos["unrealized_pnl"] = round(cur_pos_pnl, 2)
                unrealized_pnl += cur_pos_pnl
                remaining_positions.append(pos)

        state["open_positions"] = remaining_positions
        state["closed_trades"] = closed_trades

        # 3. Evaluate causal strategy signal on visible history
        current_signal = None
        pending_prop = state.get("pending_proposal")

        if len(visible_candles) >= 20:
            try:
                inds = calculate_indicators(visible_candles, session.symbol, "1D")
                ema_9 = next((p.value for p in reversed(inds.ema_9) if p.value is not None), None)
                ema_21 = next((p.value for p in reversed(inds.ema_21) if p.value is not None), None)
                if ema_9 and ema_21:
                    if ema_9 > ema_21 and current_price > ema_9:
                        current_signal = "BUY_CANDIDATE"
                        # Generate pending proposal if no open position for this symbol
                        if not remaining_positions and not pending_prop:
                            alloc = min(session.virtual_balance * 0.1, 20000.0)
                            qty = max(1, int(alloc / current_price))
                            pending_prop = {
                                "proposal_id": f"PROP-REPLAY-{new_idx}",
                                "symbol": session.symbol,
                                "side": "LONG",
                                "entry_price": current_price,
                                "quantity": qty,
                                "stop_loss": round(current_price * 0.98, 2),
                                "target": round(current_price * 1.04, 2),
                                "risk_amount": round((current_price * 0.02) * qty, 2),
                                "rationale": f"Causal EMA crossover detected (EMA9: {ema_9:.2f} > EMA21: {ema_21:.2f}) during replay step.",
                                "candle_index": new_idx,
                            }
                    elif ema_9 < ema_21:
                        current_signal = "SELL_CANDIDATE"
                    else:
                        current_signal = "HOLD"
            except Exception as e:
                logger.debug(f"Replay strategy evaluation note: {e}")

        state["current_signal"] = current_signal
        state["pending_proposal"] = pending_prop

        # Record equity curve
        total_equity = session.virtual_balance + unrealized_pnl
        equity_hist = state.get("equity_history", [])
        equity_hist.append({
            "index": new_idx,
            "equity": round(total_equity, 2),
            "pnl": round(session.realized_pnl + unrealized_pnl, 2),
        })
        state["equity_history"] = equity_hist

        session.state_json = json.dumps(state)
        session.updated_at = utcnow()
        db.commit()

        return {
            "session_id": session.session_id,
            "current_index": new_idx,
            "total_candles": total,
            "status": session.status,
            "current_candle": current_candle,
            "current_price": current_price,
            "current_signal": current_signal,
            "virtual_balance": round(session.virtual_balance, 2),
            "realized_pnl": round(session.realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_equity": round(total_equity, 2),
            "open_positions": remaining_positions,
            "closed_trades": closed_trades[-5:],
            "pending_proposal": pending_prop,
        }

    def approve_proposal(self, db: Session, session_id: str, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Approve and execute a proposal inside the replay session."""
        session = self.get_session(db, session_id)
        if not session:
            return None

        state = json.loads(session.state_json)
        pending = state.get("pending_proposal")
        if not pending or pending.get("proposal_id") != proposal_id:
            return None

        cost = pending["entry_price"] * pending["quantity"]
        if cost > session.virtual_balance:
            return {"error": "Insufficient virtual replay capital."}

        session.virtual_balance -= cost
        new_pos = {
            "position_id": f"POS-REPLAY-{uuid.uuid4().hex[:6].upper()}",
            "symbol": pending["symbol"],
            "side": pending["side"],
            "entry_price": pending["entry_price"],
            "current_price": pending["entry_price"],
            "quantity": pending["quantity"],
            "stop_loss": pending["stop_loss"],
            "target": pending["target"],
            "unrealized_pnl": 0.0,
            "entry_index": session.current_index,
        }
        state["open_positions"].append(new_pos)
        state["pending_proposal"] = None
        session.state_json = json.dumps(state)
        db.commit()

        return {"message": "Replay paper trade executed successfully.", "position": new_pos}

    def close_position(self, db: Session, session_id: str, position_id: str) -> Optional[Dict[str, Any]]:
        """Manually close an open position in replay."""
        session = self.get_session(db, session_id)
        if not session:
            return None

        state = json.loads(session.state_json)
        open_pos = state.get("open_positions", [])
        closed = state.get("closed_trades", [])
        all_candles = state.get("all_candles", [])
        current_price = all_candles[session.current_index]["close"]

        target_pos = None
        remaining = []
        for pos in open_pos:
            if pos["position_id"] == position_id:
                target_pos = pos
            else:
                remaining.append(pos)

        if not target_pos:
            return None

        entry = target_pos["entry_price"]
        qty = target_pos["quantity"]
        pnl = (current_price - entry) * qty if target_pos["side"] == "LONG" else (entry - current_price) * qty
        commission = current_price * qty * 0.0003
        net_pnl = pnl - commission

        session.realized_pnl += net_pnl
        session.virtual_balance += (entry * qty) + net_pnl

        closed.append({
            "position_id": target_pos["position_id"],
            "symbol": target_pos["symbol"],
            "side": target_pos["side"],
            "entry_price": entry,
            "exit_price": current_price,
            "quantity": qty,
            "pnl": round(net_pnl, 2),
            "exit_reason": "MANUAL_CLOSE",
            "candle_index": session.current_index,
        })

        state["open_positions"] = remaining
        state["closed_trades"] = closed
        session.state_json = json.dumps(state)
        db.commit()

        return {"message": "Position closed.", "realized_pnl": round(net_pnl, 2)}

    def reset_session(self, db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """Reset replay session back to start."""
        session = self.get_session(db, session_id)
        if not session:
            return None

        state = json.loads(session.state_json)
        all_candles = state.get("all_candles", [])
        initial_idx = min(20, len(all_candles) - 1) if len(all_candles) > 20 else 0

        state["open_positions"] = []
        state["closed_trades"] = []
        state["pending_proposal"] = None
        state["current_signal"] = None
        state["equity_history"] = [{"index": initial_idx, "equity": session.initial_capital, "pnl": 0.0}]

        session.virtual_balance = session.initial_capital
        session.realized_pnl = 0.0
        session.current_index = initial_idx
        session.status = "PAUSED"
        session.state_json = json.dumps(state)
        session.updated_at = utcnow()
        db.commit()

        return {"message": "Replay session reset to initial candle."}


replay_service = ReplayService()
