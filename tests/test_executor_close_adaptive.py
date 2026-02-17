from grvt_bot.core.executor import GRVTExecutor


class DummyConfig:
    GRVT_API_KEY = "k"
    GRVT_PRIVATE_KEY = "p"
    GRVT_TRADING_ACCOUNT_ID = "a"
    GRVT_SUB_ACCOUNT_ID = "0"
    GRVT_ENV = "testnet"

    def __init__(self, values=None):
        self.values = values or {}

    def get(self, section, key, default=None):
        return self.values.get(section, {}).get(key, default)


def build_executor(monkeypatch, config_values=None):
    monkeypatch.setattr(GRVTExecutor, "initialize_client", lambda self: None)
    cfg = DummyConfig(config_values)
    executor = GRVTExecutor(cfg)
    return executor, cfg


def test_close_position_adaptive_single_shot_on_good_liquidity(monkeypatch):
    executor, cfg = build_executor(monkeypatch)
    monkeypatch.setattr("grvt_bot.core.executor.time.sleep", lambda _: None)

    positions = [
        {"symbol": "PAXG_USDT_Perp", "side": "sell", "amount_base": 1.0},
        None,
    ]
    monkeypatch.setattr(
        executor,
        "get_open_position",
        lambda _symbol: positions.pop(0) if positions else None,
    )
    monkeypatch.setattr(executor, "get_reference_price", lambda _symbol, _side: 100.0)
    monkeypatch.setattr(
        executor,
        "get_order_book",
        lambda _symbol, limit=20: {"asks": [(100.0, 3.0)], "bids": [(99.9, 2.0)]},
    )
    monkeypatch.setattr(executor, "get_market_limits", lambda _symbol: {"min_qty": 0.01, "base_decimals": 3})

    calls = []

    def fake_place_market_order(**kwargs):
        calls.append(kwargs)
        return {"id": f"ord-{len(calls)}"}

    monkeypatch.setattr(executor, "place_market_order", fake_place_market_order)

    result = executor.close_position_adaptive(
        symbol="PAXG_USDT_Perp",
        side="buy",
        remaining_qty=1.0,
        config=cfg,
        client_order_id_seed=1,
    )
    assert result["success"] is True
    assert result["code"] == "CLOSE_SUCCESS"
    assert len(calls) == 1
    assert calls[0]["side"] == "buy"
    assert calls[0]["params"]["reduce_only"] is True
    assert abs(float(calls[0]["amount"]) - 1.0) < 1e-9


def test_close_position_adaptive_slices_on_thin_liquidity(monkeypatch):
    executor, cfg = build_executor(monkeypatch)
    monkeypatch.setattr("grvt_bot.core.executor.time.sleep", lambda _: None)

    positions = [
        {"symbol": "PAXG_USDT_Perp", "side": "sell", "amount_base": 1.0},
        {"symbol": "PAXG_USDT_Perp", "side": "sell", "amount_base": 0.8},
        {"symbol": "PAXG_USDT_Perp", "side": "sell", "amount_base": 0.8},
        None,
    ]
    monkeypatch.setattr(
        executor,
        "get_open_position",
        lambda _symbol: positions.pop(0) if positions else None,
    )
    monkeypatch.setattr(executor, "get_reference_price", lambda _symbol, _side: 100.0)

    books = [
        {"asks": [(100.0, 0.3)], "bids": [(99.9, 0.3)]},
        {"asks": [(100.0, 5.0)], "bids": [(99.9, 5.0)]},
    ]
    monkeypatch.setattr(
        executor,
        "get_order_book",
        lambda _symbol, limit=20: books.pop(0) if books else {"asks": [(100.0, 5.0)], "bids": [(99.9, 5.0)]},
    )
    monkeypatch.setattr(executor, "get_market_limits", lambda _symbol: {"min_qty": 0.01, "base_decimals": 3})

    calls = []

    def fake_place_market_order(**kwargs):
        calls.append(kwargs)
        return {"id": f"ord-{len(calls)}"}

    monkeypatch.setattr(executor, "place_market_order", fake_place_market_order)

    result = executor.close_position_adaptive(
        symbol="PAXG_USDT_Perp",
        side="buy",
        remaining_qty=1.0,
        config=cfg,
        client_order_id_seed=100,
    )
    assert result["success"] is True
    assert len(calls) == 2
    assert float(calls[0]["amount"]) < 1.0
    assert calls[0]["params"]["reduce_only"] is True
    assert calls[1]["params"]["reduce_only"] is True


def test_close_position_adaptive_halts_on_no_progress(monkeypatch):
    executor, _cfg = build_executor(
        monkeypatch,
        config_values={"execution": {"close_no_progress_retries": 3, "close_max_retries": 20}},
    )
    monkeypatch.setattr("grvt_bot.core.executor.time.sleep", lambda _: None)
    monkeypatch.setattr(
        executor,
        "get_open_position",
        lambda _symbol: {"symbol": "PAXG_USDT_Perp", "side": "sell", "amount_base": 1.0},
    )
    monkeypatch.setattr(executor, "get_reference_price", lambda _symbol, _side: None)
    monkeypatch.setattr(executor, "get_order_book", lambda _symbol, limit=20: None)

    result = executor.close_position_adaptive(
        symbol="PAXG_USDT_Perp",
        side="buy",
        remaining_qty=1.0,
        config=executor.config,
        client_order_id_seed=1,
    )
    assert result["success"] is False
    assert result["code"] == "CLOSE_NO_PROGRESS"


def test_close_position_adaptive_stops_on_retry_cap(monkeypatch):
    executor, cfg = build_executor(
        monkeypatch,
        config_values={
            "execution": {
                "close_no_progress_retries": 50,
                "close_max_retries": 2,
                "close_max_duration_seconds": 120,
            }
        },
    )
    monkeypatch.setattr("grvt_bot.core.executor.time.sleep", lambda _: None)
    monkeypatch.setattr(
        executor,
        "get_open_position",
        lambda _symbol: {"symbol": "PAXG_USDT_Perp", "side": "sell", "amount_base": 1.0},
    )
    monkeypatch.setattr(executor, "get_reference_price", lambda _symbol, _side: None)
    monkeypatch.setattr(executor, "get_order_book", lambda _symbol, limit=20: None)

    result = executor.close_position_adaptive(
        symbol="PAXG_USDT_Perp",
        side="buy",
        remaining_qty=1.0,
        config=cfg,
        client_order_id_seed=1,
    )
    assert result["success"] is False
    assert result["code"] == "CLOSE_TIMEOUT"


def test_flatten_all_positions_uses_adaptive_close(monkeypatch):
    executor, cfg = build_executor(monkeypatch)
    monkeypatch.setattr(
        executor,
        "get_open_position",
        lambda _symbol: {"symbol": "PAXG_USDT_Perp", "side": "buy", "amount_base": 0.5},
    )

    calls = []

    def fake_close_position_adaptive(**kwargs):
        calls.append(kwargs)
        return {"success": True, "code": "CLOSE_SUCCESS", "remaining_qty": 0.0, "attempts": 1}

    monkeypatch.setattr(executor, "close_position_adaptive", fake_close_position_adaptive)

    ok = executor.flatten_all_positions("PAXG_USDT_Perp")
    assert ok is True
    assert len(calls) == 1
    assert calls[0]["side"] == "sell"
    assert calls[0]["remaining_qty"] == 0.5
    assert calls[0]["config"] is cfg
