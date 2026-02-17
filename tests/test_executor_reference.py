from grvt_bot.core.executor import GRVTExecutor


class DummyConfig:
    GRVT_API_KEY = "k"
    GRVT_PRIVATE_KEY = "p"
    GRVT_TRADING_ACCOUNT_ID = "a"
    GRVT_SUB_ACCOUNT_ID = "0"
    GRVT_ENV = "testnet"


class DummyClient:
    def __init__(self):
        self.ticker_payload = {}
        self.order_book_payload = {"bids": [[99.5, 1.2]], "asks": [[100.5, 0.8]]}
        self.markets_payload = {
            "PAXG_USDT_Perp": {
                "instrument": "PAXG_USDT_Perp",
                "min_size": "0.01",
                "tick_size": "0.1",
                "base_decimals": 3,
            }
        }

    def fetch_ticker(self, symbol):
        return self.ticker_payload

    def load_markets(self):
        return self.markets_payload

    def fetch_markets(self):
        return list(self.markets_payload.values())

    def fetch_order_book(self, symbol, limit=None):
        return self.order_book_payload


def build_executor(monkeypatch):
    monkeypatch.setattr(GRVTExecutor, "initialize_client", lambda self: None)
    executor = GRVTExecutor(DummyConfig())
    executor.client = DummyClient()
    return executor


def test_reference_price_fallback_chain(monkeypatch):
    executor = build_executor(monkeypatch)

    executor.client.ticker_payload = {"best_ask_price": "101.5", "last_price": "100"}
    assert executor.get_reference_price("PAXG_USDT_Perp", "buy") == 101.5

    executor.client.ticker_payload = {"best_bid_price": "99.5", "last_price": "100"}
    assert executor.get_reference_price("PAXG_USDT_Perp", "sell") == 99.5

    executor.client.ticker_payload = {"last_price": "100.1", "mark_price": "99.9"}
    assert executor.get_reference_price("PAXG_USDT_Perp", "buy") == 100.1

    executor.client.ticker_payload = {"mark_price": "99.7"}
    assert executor.get_reference_price("PAXG_USDT_Perp", "buy") == 99.7


def test_get_market_limits_reads_min_size(monkeypatch):
    executor = build_executor(monkeypatch)
    limits = executor.get_market_limits("PAXG_USDT_Perp")
    assert limits is not None
    assert limits["min_qty"] == 0.01
    assert limits["tick_size"] == 0.1
    assert limits["base_decimals"] == 3


def test_get_order_book_normalizes_levels(monkeypatch):
    executor = build_executor(monkeypatch)
    order_book = executor.get_order_book("PAXG_USDT_Perp", limit=20)
    assert order_book is not None
    assert order_book["bids"][0] == (99.5, 1.2)
    assert order_book["asks"][0] == (100.5, 0.8)
