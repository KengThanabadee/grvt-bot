import shutil
import uuid
from pathlib import Path

from grvt_bot.core.state import StateStore


class DummyExecutor:
    def __init__(self, position):
        self.position = position

    def get_open_position(self, symbol):
        return self.position


def test_state_persistence_and_recovery():
    tmp_dir = Path(f".state_test_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        state_path = tmp_dir / "runtime_state.json"
        store = StateStore(str(state_path))

        state = store.load()
        assert state["open_position"] is None
        assert state["halted"] is False
        assert state["pending_action"] is None
        assert state["close_attempt_count"] == 0
        assert state["last_close_reason"] == ""

        state["open_position"] = {
            "side": "buy",
            "amount_base": 0.123,
            "entry_price": 2000.0,
        }
        store.save(state)

        # Simulate process restart.
        recovered = StateStore(str(state_path)).load()
        assert recovered["open_position"]["side"] == "buy"
        assert recovered["open_position"]["amount_base"] == 0.123
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_reconcile_updates_state_from_exchange():
    tmp_dir = Path(f".state_test_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        state_path = tmp_dir / "runtime_state.json"
        store = StateStore(str(state_path))

        state = store.load()
        state["open_position"] = None
        store.save(state)

        exchange_position = {
            "symbol": "PAXG_USDT_Perp",
            "side": "sell",
            "amount_base": 0.5,
        }
        result = store.reconcile(DummyExecutor(exchange_position), "PAXG_USDT_Perp")

        assert result.mismatch is True
        assert result.state["open_position"]["side"] == "sell"
        assert result.state["open_position"]["amount_base"] == 0.5
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
