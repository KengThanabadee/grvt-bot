from grvt_bot.core.risk import RiskEngine


class DummyConfig:
    def __init__(self, values):
        self.values = values

    def get(self, section, key, default=None):
        return self.values.get(section, {}).get(key, default)


def build_config(kill_switch=False):
    return DummyConfig(
        {
            "risk": {
                "active_track": "normal",
                "fail_closed": True,
                "kill_switch": kill_switch,
                "threshold_action": "flatten_halt",
                "risk_per_trade_pct": 0.25,
                "min_notional_safety_factor": 1.05,
                "tracks": {
                    "normal": {"max_drawdown_pct": 5.0, "profit_target_pct": 5.0},
                    "low_vol": {"max_drawdown_pct": 2.0, "profit_target_pct": 2.0},
                },
            }
        }
    )


def test_kill_switch_blocks_entry():
    engine = RiskEngine(build_config(kill_switch=True))
    decision = engine.evaluate_entry(
        side="buy",
        amount_usdt=100.0,
        reference_price=1000.0,
        market_limits={"min_qty": 0.001},
        is_halted=False,
    )
    assert decision.allowed is False
    assert decision.code == "KILL_SWITCH"


def test_min_qty_violation_rejects_entry():
    engine = RiskEngine(build_config())
    decision = engine.evaluate_entry(
        side="buy",
        amount_usdt=10.0,  # qty=0.01
        reference_price=1000.0,
        market_limits={"min_qty": 0.02, "base_decimals": 4},
        is_halted=False,
    )
    assert decision.allowed is False
    assert decision.code == "MIN_QTY_VIOLATION"


def test_derived_min_notional_violation_rejects_entry():
    engine = RiskEngine(build_config())
    decision = engine.evaluate_entry(
        side="buy",
        amount_usdt=20.0,  # below derived min_notional (0.02*1000*1.05=21)
        reference_price=1000.0,
        market_limits={"min_qty": 0.02, "base_decimals": 4},
        is_halted=False,
    )
    assert decision.allowed is False
    assert decision.code == "MIN_NOTIONAL_VIOLATION"
    assert decision.derived_min_notional_usdt == 21.0


def test_drawdown_threshold_triggers_flatten_halt():
    engine = RiskEngine(build_config())
    decision = engine.evaluate_thresholds(current_equity_usdt=940.0, baseline_equity_usdt=1000.0)
    assert decision.allowed is False
    assert decision.code == "MAX_DRAWDOWN_HIT"
    assert decision.action == "flatten_halt"


def test_profit_threshold_triggers_flatten_halt():
    engine = RiskEngine(build_config())
    decision = engine.evaluate_thresholds(current_equity_usdt=1060.0, baseline_equity_usdt=1000.0)
    assert decision.allowed is False
    assert decision.code == "PROFIT_TARGET_HIT"
    assert decision.action == "flatten_halt"
