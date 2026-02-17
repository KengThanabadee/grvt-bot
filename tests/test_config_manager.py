from grvt_bot.core.config import ConfigManager


def test_repr_masks_without_mutating_config_values():
    config = ConfigManager(
        config_dict={
            "grvt": {
                "api_key": "real_api_key",
                "private_key": "real_private_key",
                "trading_account_id": "12345",
            }
        }
    )

    assert config.GRVT_API_KEY == "real_api_key"
    assert config.GRVT_PRIVATE_KEY == "real_private_key"

    rendered = repr(config)
    assert "***MASKED***" in rendered

    # repr() must not overwrite runtime values.
    assert config.GRVT_API_KEY == "real_api_key"
    assert config.GRVT_PRIVATE_KEY == "real_private_key"


def test_default_config_isolation_between_instances():
    first = ConfigManager()
    first.set("trading", "symbol", "ETH_USDT_Perp")

    second = ConfigManager()
    assert second.SYMBOL == "BTC_USDT_Perp"


def test_recursive_merge_preserves_nested_defaults():
    config = ConfigManager(
        config_dict={
            "risk": {
                "tracks": {
                    "normal": {
                        "max_drawdown_pct": 4.0,
                    }
                }
            }
        }
    )

    assert config.get("risk", "tracks")["normal"]["max_drawdown_pct"] == 4.0
    # Ensure sibling nested default value still exists after recursive merge.
    assert config.get("risk", "tracks")["normal"]["profit_target_pct"] == 5.0


def test_ops_runtime_guard_defaults_present():
    config = ConfigManager()
    assert config.LOCK_FILE == "state/runtime.lock"
    assert config.ERROR_BACKOFF_SECONDS == 2
    assert config.MAX_REPEATED_ERRORS == 20
    assert config.REPEATED_ERROR_WINDOW_SECONDS == 300
    assert config.STARTUP_MISMATCH_POLICY == "adopt_continue"
    assert config.EXECUTION_CLOSE_MODE == "reduce_only_twap_slice"
    assert config.EXECUTION_LIQUIDITY_USAGE_PCT == 0.20
