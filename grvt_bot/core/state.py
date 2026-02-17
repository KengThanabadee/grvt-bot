"""
State persistence and exchange reconciliation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReconcileResult:
    """Result of state reconciliation against exchange position."""

    mismatch: bool
    exchange_position: Optional[Dict[str, Any]]
    local_position: Optional[Dict[str, Any]]
    state: Dict[str, Any]
    reason: str


class StateStore:
    """Simple JSON-backed state for runtime recovery."""

    def __init__(self, state_path: str, logger: Optional[logging.Logger] = None):
        self.path = Path(state_path)
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def default_state() -> Dict[str, Any]:
        return {
            "version": 1,
            "halted": False,
            "halt_reason": "",
            "open_position": None,
            "pending_action": None,
            "last_close_attempt_at": None,
            "close_attempt_count": 0,
            "last_close_reason": "",
            "baseline_equity_usdt": None,
            "last_candle_open_time_ms": None,
            "last_loop_started_at": None,
            "updated_at": _utc_now_iso(),
        }

    def load(self) -> Dict[str, Any]:
        """Load state from disk or initialize default state."""
        if not self.path.exists():
            state = self.default_state()
            self.save(state)
            return state

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as exc:
            self.logger.error("Failed reading state file %s: %s", self.path, exc)
            state = self.default_state()
            self.save(state)
            return state

        default_state = self.default_state()
        default_state.update(state if isinstance(state, dict) else {})
        return default_state

    def save(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Persist state atomically."""
        data = dict(state)
        data["updated_at"] = _utc_now_iso()

        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True, indent=2, sort_keys=True)
        tmp_path.replace(self.path)
        return data

    def set_halted(self, halted: bool, reason: str = "") -> Dict[str, Any]:
        state = self.load()
        state["halted"] = bool(halted)
        state["halt_reason"] = str(reason or "")
        return self.save(state)

    def set_open_position(self, position: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        state = self.load()
        state["open_position"] = position
        return self.save(state)

    def set_last_candle_open_time_ms(self, ts_ms: Optional[int]) -> Dict[str, Any]:
        state = self.load()
        state["last_candle_open_time_ms"] = ts_ms
        return self.save(state)

    def set_baseline_equity(self, equity_usdt: Optional[float]) -> Dict[str, Any]:
        state = self.load()
        state["baseline_equity_usdt"] = equity_usdt
        return self.save(state)

    @staticmethod
    def _positions_mismatch(
        local_position: Optional[Dict[str, Any]],
        exchange_position: Optional[Dict[str, Any]],
        qty_tol: float = 1e-9,
    ) -> bool:
        if not local_position and not exchange_position:
            return False
        if bool(local_position) != bool(exchange_position):
            return True

        assert local_position is not None
        assert exchange_position is not None

        local_side = str(local_position.get("side", "")).lower()
        exchange_side = str(exchange_position.get("side", "")).lower()
        if local_side != exchange_side:
            return True

        local_qty = float(local_position.get("amount_base", 0.0))
        exchange_qty = float(exchange_position.get("amount_base", 0.0))
        return abs(local_qty - exchange_qty) > qty_tol

    def reconcile(self, executor: Any, symbol: str) -> ReconcileResult:
        """
        Reconcile local state with live exchange position.

        Exchange is treated as source of truth.
        """
        state = self.load()
        local_position = state.get("open_position")

        exchange_position = executor.get_open_position(symbol)
        mismatch = self._positions_mismatch(local_position, exchange_position)
        reason = "positions_match"

        if mismatch:
            reason = "position_mismatch_reconciled"
            state["open_position"] = exchange_position
            state = self.save(state)

        return ReconcileResult(
            mismatch=mismatch,
            exchange_position=exchange_position,
            local_position=local_position,
            state=state,
            reason=reason,
        )
