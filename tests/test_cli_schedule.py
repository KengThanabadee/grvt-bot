from datetime import datetime

from grvt_bot.cli.main import (
    resolve_startup_mismatch_policy,
    seconds_until_data_fetch,
    seconds_until_next_run,
    should_close_on_opposite_signal,
)
from grvt_bot.core.config import ConfigManager


def test_seconds_until_next_run_mid_cycle_interval_1():
    now = datetime(2026, 2, 16, 12, 34, 30, 0)
    sleep_seconds = seconds_until_next_run(1, now)
    assert 30.0 <= sleep_seconds <= 30.1


def test_seconds_until_next_run_on_boundary_interval_1():
    now = datetime(2026, 2, 16, 12, 34, 0, 0)
    sleep_seconds = seconds_until_next_run(1, now)
    # On exact boundary, run immediately (small buffer only).
    assert 0.0 <= sleep_seconds <= 0.1


def test_seconds_until_next_run_interval_5():
    now = datetime(2026, 2, 16, 12, 34, 10, 0)
    sleep_seconds = seconds_until_next_run(5, now)
    # Next run should be 12:35:00
    assert 50.0 <= sleep_seconds <= 50.1


def test_seconds_until_next_run_interval_15():
    now = datetime(2026, 2, 16, 12, 34, 10, 0)
    sleep_seconds = seconds_until_next_run(15, now)
    # Next run should be 12:45:00
    assert 650.0 <= sleep_seconds <= 650.1


def test_seconds_until_data_fetch_applies_close_buffer():
    now = datetime(2026, 2, 16, 12, 34, 58, 0)
    sleep_seconds = seconds_until_data_fetch(1, 2, now)
    # Boundary wait (~2.05s) + 2s close buffer.
    assert 4.0 <= sleep_seconds <= 4.2


def test_startup_mismatch_policy_defaults_to_adopt_continue():
    config = ConfigManager(config_dict={"ops": {"startup_mismatch_policy": "adopt_continue"}})
    assert resolve_startup_mismatch_policy(config) == "adopt_continue"


def test_startup_mismatch_policy_falls_back_from_legacy_flag():
    config = ConfigManager(config_dict={"ops": {"startup_mismatch_policy": "", "halt_on_reconcile_mismatch": True}})
    assert resolve_startup_mismatch_policy(config) == "halt_only"


def test_should_close_on_opposite_signal_true_for_opposite_side():
    open_position = {"side": "buy", "amount_base": 1.0}
    signal = {"side": "sell", "amount_usdt": 100}
    assert should_close_on_opposite_signal(open_position, signal) is True


def test_should_close_on_opposite_signal_false_for_same_side():
    open_position = {"side": "buy", "amount_base": 1.0}
    signal = {"side": "long", "amount_usdt": 100}
    assert should_close_on_opposite_signal(open_position, signal) is False


def test_should_close_on_opposite_signal_false_for_invalid_payload():
    assert should_close_on_opposite_signal(None, {"side": "sell"}) is False
    assert should_close_on_opposite_signal({"side": "buy"}, None) is False
