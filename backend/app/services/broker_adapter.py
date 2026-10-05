"""Broker Adapter Interface and Paper Trading Execution Engine for Vibe Trader AI."""
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.entities import utcnow

logger = logging.getLogger("vibe-trader-ai.broker")


class BrokerAdapterBase(ABC):
    """Abstract interface for multi-market order execution."""

    @abstractmethod
    def submit_buy_order(
        self,
        symbol: str,
        market: str,
        quantity: float,
        price: float,
        stop_loss: float,
        target: float,
    ) -> Dict[str, Any]:
        """Submit a BUY order."""
        pass

    @abstractmethod
    def submit_sell_order(
        self,
        symbol: str,
        market: str,
        quantity: float,
        price: float,
        reason: str,
    ) -> Dict[str, Any]:
        """Submit a SELL order."""
        pass


class PaperBrokerAdapter(BrokerAdapterBase):
    """
    Local virtual paper broker simulating realistic order execution,
    including estimated exchange fees, micro-slippage, and adverse failure states.
    Supports simulated failure, rejection, cancellation, and partial fills for stress testing.
    """

    def __init__(self, fee_rate: float = 0.0003, slippage_factor: float = 0.0002):
        self.fee_rate = fee_rate
        self.slippage_factor = slippage_factor
        self.simulated_failure_mode: Optional[str] = None
        self.partial_fill_ratio: float = 0.5

    def set_simulation_mode(self, mode: Optional[str] = None, partial_ratio: float = 0.5):
        """Configure simulation mode: None, 'FAIL', 'REJECT', 'CANCEL', 'PARTIAL'."""
        self.simulated_failure_mode = mode.upper() if mode else None
        self.partial_fill_ratio = max(0.01, min(0.99, partial_ratio))

    def reset_simulation_mode(self):
        """Reset simulation mode to normal execution."""
        self.simulated_failure_mode = None
        self.partial_fill_ratio = 0.5

    def submit_buy_order(
        self,
        symbol: str,
        market: str,
        quantity: float,
        price: float,
        stop_loss: float,
        target: float,
    ) -> Dict[str, Any]:
        order_id = f"PB-BUY-{uuid.uuid4().hex[:8].upper()}"

        if self.simulated_failure_mode == "FAIL":
            logger.warning(f"[PAPER BROKER] Simulated order failure for {quantity} {symbol}")
            return {
                "order_id": order_id,
                "broker": "PAPER_SIMULATOR",
                "side": "BUY",
                "symbol": symbol,
                "market": market,
                "status": "FAILED",
                "requested_price": price,
                "fill_price": 0.0,
                "quantity": 0.0,
                "slippage": 0.0,
                "fees": 0.0,
                "stop_loss": stop_loss,
                "target": target,
                "reason": "SIMULATED_BROKER_FAILURE",
                "executed_at": utcnow().isoformat(),
            }

        if self.simulated_failure_mode == "REJECT":
            logger.warning(f"[PAPER BROKER] Simulated order rejection for {quantity} {symbol}")
            return {
                "order_id": order_id,
                "broker": "PAPER_SIMULATOR",
                "side": "BUY",
                "symbol": symbol,
                "market": market,
                "status": "REJECTED",
                "requested_price": price,
                "fill_price": 0.0,
                "quantity": 0.0,
                "slippage": 0.0,
                "fees": 0.0,
                "stop_loss": stop_loss,
                "target": target,
                "reason": "SIMULATED_BROKER_REJECTION",
                "executed_at": utcnow().isoformat(),
            }

        if self.simulated_failure_mode == "CANCEL":
            logger.warning(f"[PAPER BROKER] Simulated order cancellation for {quantity} {symbol}")
            return {
                "order_id": order_id,
                "broker": "PAPER_SIMULATOR",
                "side": "BUY",
                "symbol": symbol,
                "market": market,
                "status": "CANCELLED",
                "requested_price": price,
                "fill_price": 0.0,
                "quantity": 0.0,
                "slippage": 0.0,
                "fees": 0.0,
                "stop_loss": stop_loss,
                "target": target,
                "reason": "SIMULATED_ORDER_CANCELLED",
                "executed_at": utcnow().isoformat(),
            }

        status_result = "FILLED"
        actual_qty = quantity
        if self.simulated_failure_mode == "PARTIAL":
            status_result = "PARTIAL"
            actual_qty = max(1.0, round(quantity * self.partial_fill_ratio, 2))

        # Simulate slight adverse slippage (+0.02%)
        slippage = round(price * self.slippage_factor, 4)
        fill_price = round(price + slippage, 4)
        gross_value = fill_price * actual_qty
        fees = round((gross_value * self.fee_rate) + 1.0, 2)

        logger.info(f"[PAPER BROKER] {status_result} BUY order {order_id} for {actual_qty} {symbol} @ {fill_price}")

        return {
            "order_id": order_id,
            "broker": "PAPER_SIMULATOR",
            "side": "BUY",
            "symbol": symbol,
            "market": market,
            "status": status_result,
            "requested_price": price,
            "fill_price": fill_price,
            "quantity": actual_qty,
            "slippage": slippage,
            "fees": fees,
            "stop_loss": stop_loss,
            "target": target,
            "executed_at": utcnow().isoformat(),
        }

    def submit_sell_order(
        self,
        symbol: str,
        market: str,
        quantity: float,
        price: float,
        reason: str,
    ) -> Dict[str, Any]:
        order_id = f"PB-SELL-{uuid.uuid4().hex[:8].upper()}"

        if self.simulated_failure_mode == "FAIL":
            logger.warning(f"[PAPER BROKER] Simulated SELL order failure for {quantity} {symbol}")
            return {
                "order_id": order_id,
                "broker": "PAPER_SIMULATOR",
                "side": "SELL",
                "symbol": symbol,
                "market": market,
                "status": "FAILED",
                "requested_price": price,
                "fill_price": 0.0,
                "quantity": 0.0,
                "slippage": 0.0,
                "fees": 0.0,
                "reason": "SIMULATED_BROKER_FAILURE",
                "executed_at": utcnow().isoformat(),
            }

        if self.simulated_failure_mode == "REJECT":
            logger.warning(f"[PAPER BROKER] Simulated SELL order rejection for {quantity} {symbol}")
            return {
                "order_id": order_id,
                "broker": "PAPER_SIMULATOR",
                "side": "SELL",
                "symbol": symbol,
                "market": market,
                "status": "REJECTED",
                "requested_price": price,
                "fill_price": 0.0,
                "quantity": 0.0,
                "slippage": 0.0,
                "fees": 0.0,
                "reason": "SIMULATED_BROKER_REJECTION",
                "executed_at": utcnow().isoformat(),
            }

        # Simulate slight adverse slippage (-0.02%)
        slippage = round(price * self.slippage_factor, 4)
        fill_price = round(price - slippage, 4)
        gross_value = fill_price * quantity
        fees = round((gross_value * self.fee_rate) + 1.0, 2)

        logger.info(f"[PAPER BROKER] Filled SELL order {order_id} for {quantity} {symbol} @ {fill_price} (Reason: {reason})")

        return {
            "order_id": order_id,
            "broker": "PAPER_SIMULATOR",
            "side": "SELL",
            "symbol": symbol,
            "market": market,
            "status": "FILLED",
            "requested_price": price,
            "fill_price": fill_price,
            "quantity": quantity,
            "slippage": slippage,
            "fees": fees,
            "reason": reason,
            "executed_at": utcnow().isoformat(),
        }


# Default local paper broker instance
paper_broker = PaperBrokerAdapter()
