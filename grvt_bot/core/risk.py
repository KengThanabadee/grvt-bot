"""
Risk engine for entry gating and account-level threshold controls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import logging


@dataclass
class RiskDecision:
    """Result of a risk evaluation."""

    allowed: bool
    code: str
    reason: str
    action: str = "allow"
    order_qty: Optional[float] = None
    order_notional_usdt: Optional[float] = None
    derived_min_notional_usdt: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class RiskEngine:
    """Risk controls for bot runtime and order entry checks."""

    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def _get(self, section: str, key: str, default: Any = None) -> Any:
        if hasattr(self.config, "get"):
            return self.config.get(section, key, default)
        return default

    @property
    def fail_closed(self) -> bool:
        return bool(self._get("risk", "fail_closed", True))

    @property
    def kill_switch(self) -> bool:
        return bool(self._get("risk", "kill_switch", False))

    @property
    def active_track(self) -> str:
        return str(self._get("risk", "active_track", "normal"))

    @property
    def threshold_action(self) -> str:
        return str(self._get("risk", "threshold_action", "flatten_halt"))

    @property
    def risk_per_trade_pct(self) -> float:
        return float(self._get("risk", "risk_per_trade_pct", 0.25))

    @property
    def min_notional_safety_factor(self) -> float:
        return float(self._get("risk", "min_notional_safety_factor", 1.05))

    def _active_track_config(self) -> Dict[str, float]:
        tracks = self._get("risk", "tracks", {}) or {}
        active = tracks.get(self.active_track) or tracks.get("normal") or {}
        return {
            "max_drawdown_pct": float(active.get("max_drawdown_pct", 5.0)),
            "profit_target_pct": float(active.get("profit_target_pct", 5.0)),
        }

    def compute_notional_from_risk(
        self,
        account_equity_usdt: float,
        leverage: float,
        signal_amount_usdt: Optional[float] = None,
    ) -> float:
        """
        Compute order notional from risk-per-trade and leverage.

        If strategy provides its own amount, cap by the risk-derived notional.
        """
        leverage = max(1.0, float(leverage))
        equity = max(0.0, float(account_equity_usdt))
        risk_notional = equity * (self.risk_per_trade_pct / 100.0) * leverage

        if signal_amount_usdt is None:
            return risk_notional

        signal_amount_usdt = float(signal_amount_usdt)
        if signal_amount_usdt <= 0:
            return risk_notional

        # Conservative: strategy can request lower, but not higher than risk budget.
        return min(signal_amount_usdt, risk_notional)

    def evaluate_thresholds(
        self,
        current_equity_usdt: Optional[float],
        baseline_equity_usdt: Optional[float],
    ) -> RiskDecision:
        """Check drawdown/profit threshold for Flatten+Halt policy."""
        if current_equity_usdt is None or baseline_equity_usdt is None:
            if self.fail_closed:
                return RiskDecision(
                    allowed=False,
                    code="EQUITY_DATA_MISSING",
                    reason="Missing equity data for threshold checks",
                    action="halt",
                )
            return RiskDecision(allowed=True, code="EQUITY_DATA_MISSING", reason="skip")

        baseline = float(baseline_equity_usdt)
        current = float(current_equity_usdt)
        if baseline <= 0 or current <= 0:
            if self.fail_closed:
                return RiskDecision(
                    allowed=False,
                    code="EQUITY_DATA_INVALID",
                    reason=f"Invalid equity values baseline={baseline}, current={current}",
                    action="halt",
                )
            return RiskDecision(allowed=True, code="EQUITY_DATA_INVALID", reason="skip")

        track = self._active_track_config()
        max_drawdown_pct = float(track["max_drawdown_pct"])
        profit_target_pct = float(track["profit_target_pct"])
        pnl_pct = ((current - baseline) / baseline) * 100.0

        if pnl_pct <= -max_drawdown_pct:
            return RiskDecision(
                allowed=False,
                code="MAX_DRAWDOWN_HIT",
                reason=f"Drawdown {pnl_pct:.2f}% <= -{max_drawdown_pct:.2f}%",
                action=self.threshold_action,
                meta={"pnl_pct": pnl_pct, "baseline_equity_usdt": baseline, "current_equity_usdt": current},
            )

        if pnl_pct >= profit_target_pct:
            return RiskDecision(
                allowed=False,
                code="PROFIT_TARGET_HIT",
                reason=f"PnL {pnl_pct:.2f}% >= {profit_target_pct:.2f}%",
                action=self.threshold_action,
                meta={"pnl_pct": pnl_pct, "baseline_equity_usdt": baseline, "current_equity_usdt": current},
            )

        return RiskDecision(
            allowed=True,
            code="OK",
            reason="Threshold checks passed",
            meta={"pnl_pct": pnl_pct},
        )

    def evaluate_entry(
        self,
        side: str,
        amount_usdt: Optional[float],
        reference_price: Optional[float],
        market_limits: Optional[Dict[str, Any]],
        is_halted: bool,
        account_equity_usdt: Optional[float] = None,
        leverage: Optional[float] = None,
    ) -> RiskDecision:
        """Evaluate whether entry should proceed."""
        side = str(side).lower()
        if side not in {"buy", "sell"}:
            return RiskDecision(False, "INVALID_SIDE", f"Unsupported side: {side}", action="skip")

        if self.kill_switch:
            return RiskDecision(False, "KILL_SWITCH", "Risk kill-switch is enabled", action="skip")

        if is_halted:
            return RiskDecision(False, "HALTED", "Bot is halted", action="skip")

        if reference_price is None or float(reference_price) <= 0:
            return RiskDecision(
                False,
                "REFERENCE_PRICE_MISSING",
                "Reference price unavailable",
                action="skip",
            )

        if amount_usdt is None:
            if account_equity_usdt is None or leverage is None:
                return RiskDecision(
                    False,
                    "NOTIONAL_INPUT_MISSING",
                    "Missing amount_usdt and missing account_equity/leverage to derive it",
                    action="skip",
                )
            amount_usdt = self.compute_notional_from_risk(account_equity_usdt, leverage)
        amount_usdt = float(amount_usdt)

        if amount_usdt <= 0:
            return RiskDecision(False, "INVALID_NOTIONAL", f"amount_usdt={amount_usdt}", action="skip")

        if not market_limits:
            if self.fail_closed:
                return RiskDecision(
                    False,
                    "MARKET_LIMITS_MISSING",
                    "Market limits are missing and fail_closed is enabled",
                    action="skip",
                )
            return RiskDecision(True, "MARKET_LIMITS_MISSING", "Proceeding without market limits")

        min_qty_value = market_limits.get("min_qty")
        if min_qty_value in (None, "", 0):
            if self.fail_closed:
                return RiskDecision(
                    False,
                    "MIN_QTY_MISSING",
                    "min_qty missing from exchange metadata",
                    action="skip",
                )
            min_qty = 0.0
        else:
            min_qty = float(min_qty_value)
            if min_qty <= 0:
                if self.fail_closed:
                    return RiskDecision(
                        False,
                        "MIN_QTY_INVALID",
                        f"Invalid min_qty={min_qty}",
                        action="skip",
                    )
                min_qty = 0.0

        reference_price = float(reference_price)
        computed_qty = amount_usdt / reference_price
        if computed_qty <= 0:
            return RiskDecision(
                False,
                "COMPUTED_QTY_INVALID",
                f"computed_qty={computed_qty}",
                action="skip",
            )

        base_decimals = market_limits.get("base_decimals")
        if base_decimals is not None:
            try:
                precision = max(0, int(base_decimals))
                computed_qty = round(computed_qty, precision)
            except (TypeError, ValueError):
                pass

        if min_qty > 0 and computed_qty < min_qty:
            return RiskDecision(
                False,
                "MIN_QTY_VIOLATION",
                f"computed_qty={computed_qty:.12f} < min_qty={min_qty:.12f}",
                action="skip",
                order_qty=computed_qty,
            )

        derived_min_notional = min_qty * reference_price * self.min_notional_safety_factor if min_qty > 0 else 0.0
        if derived_min_notional > 0 and amount_usdt < derived_min_notional:
            return RiskDecision(
                False,
                "MIN_NOTIONAL_VIOLATION",
                f"amount_usdt={amount_usdt:.8f} < derived_min_notional={derived_min_notional:.8f}",
                action="skip",
                order_qty=computed_qty,
                derived_min_notional_usdt=derived_min_notional,
            )

        return RiskDecision(
            True,
            "OK",
            "Entry allowed",
            action="allow",
            order_qty=computed_qty,
            order_notional_usdt=amount_usdt,
            derived_min_notional_usdt=derived_min_notional,
            meta={"min_qty": min_qty, "reference_price": reference_price},
        )
