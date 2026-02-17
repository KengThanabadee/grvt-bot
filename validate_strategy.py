import numpy as np
import pandas as pd

from grvt_bot.strategies.paxg_mean_reversion_strategy import PAXGMeanReversionStrategy


class MockConfig:
    def __init__(self):
        self.config = {
            "strategy": {
                "timeframe": "15m",
                "symbol": "PAXG_USDT_Perp",
                "bb_window": 20,
                "bb_std": 2.0,
                "atr_window": 14,
                "sl_atr_multiplier": 1.5,
                "capital": 100000.0,
                "risk_per_trade_pct": 0.25,
            },
            "trading": {"order_size_usdt": 500},
        }

    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)


def generate_data(n=100):
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=n, freq="15min")
    close = np.random.normal(2000, 10, n).cumsum()
    close = close + np.sin(np.linspace(0, 10, n)) * 20

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": close + np.random.normal(0, 2, n),
            "high": close + np.abs(np.random.normal(0, 5, n)),
            "low": close - np.abs(np.random.normal(0, 5, n)),
            "close": close,
            "volume": np.random.randint(100, 1000, n),
        }
    )
    return df


def test_strategy():
    print("Testing PAXG Mean Reversion Strategy logic...")
    config = MockConfig()
    strategy = PAXGMeanReversionStrategy(config)

    data = generate_data(100)
    strategy.update_market_data(data)
    print("Indicators calculated successfully.")

    idx = -2

    # Force BUY condition
    lower_band = strategy.price_data.iloc[idx]["bb_low"]
    strategy.price_data.at[strategy.price_data.index[idx], "close"] = lower_band - 10
    signal = strategy.get_signal()
    if signal and signal["side"] == "buy":
        print("[PASS] BUY signal generated correctly")
    else:
        print(f"[FAIL] BUY signal failed. Got: {signal}")

    # Force SELL condition
    upper_band = strategy.price_data.iloc[idx]["bb_high"]
    strategy.price_data.at[strategy.price_data.index[idx], "close"] = upper_band + 10
    strategy.current_position = None
    signal = strategy.get_signal()
    if signal and signal["side"] == "sell":
        print("[PASS] SELL signal generated correctly")
    else:
        print(f"[FAIL] SELL signal failed. Got: {signal}")

    # Exit check using buy side convention used by main loop
    mid_band = strategy.price_data.iloc[-1]["bb_mid"]
    position = {"side": "buy", "entry_price": 2000}
    exit_signal = strategy.check_exit(mid_band + 5, position)
    if exit_signal and exit_signal["action"] == "close":
        print("[PASS] Exit signal triggered correctly")
    else:
        print(f"[FAIL] Exit signal failed. Mid: {mid_band}, Price: {mid_band + 5}")


if __name__ == "__main__":
    test_strategy()
