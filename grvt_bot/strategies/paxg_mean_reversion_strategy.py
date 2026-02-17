"""
PAXG mean reversion strategy.

Uses Bollinger Bands for entries and middle-band reversion for exits.
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd
import ta

from grvt_bot.strategies.base import BaseStrategy


class PAXGMeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy for PAXG perpetuals."""

    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)

        strategy_config = self._extract_strategy_config(config)

        self.timeframe = str(strategy_config.get("timeframe", "15m"))
        self.symbol = str(strategy_config.get("symbol", getattr(config, "SYMBOL", "PAXG_USDT_Perp")))

        # Indicator parameters
        self.bb_window = int(strategy_config.get("bb_window", 20))
        self.bb_std = float(strategy_config.get("bb_std", 2.0))
        self.atr_window = int(strategy_config.get("atr_window", 14))
        self.sl_atr_multiplier = float(strategy_config.get("sl_atr_multiplier", 1.5))

        # Risk parameters
        self.capital = float(strategy_config.get("capital", 100000.0))
        self.risk_per_trade_pct = float(strategy_config.get("risk_per_trade_pct", 0.25))
        self.risk_amount = self.capital * (self.risk_per_trade_pct / 100.0)

        # Strategy state
        self.price_data: pd.DataFrame = pd.DataFrame()
        self.current_position: Optional[Dict[str, Any]] = None

        self.logger.info(
            "Initialized %s for %s on %s (risk per trade: $%.2f)",
            self.__class__.__name__,
            self.symbol,
            self.timeframe,
            self.risk_amount,
        )

    @staticmethod
    def _extract_strategy_config(config: Any) -> Dict[str, Any]:
        if isinstance(config, dict):
            return dict(config.get("strategy", {}))

        if hasattr(config, "config") and isinstance(config.config, dict):
            return dict(config.config.get("strategy", {}))

        if hasattr(config, "strategy") and isinstance(config.strategy, dict):
            return dict(config.strategy)

        return {}

    def update_market_data(self, data: pd.DataFrame) -> None:
        """
        Update market data for indicator calculation.

        Expected columns: timestamp, open, high, low, close, volume
        """
        if data is None or data.empty:
            return

        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(data.columns):
            self.logger.warning("Market data missing required columns: %s", required_cols)
            return

        self.price_data = data.copy()
        self._calculate_indicators()

    def _calculate_indicators(self) -> None:
        if self.price_data.empty:
            return

        if len(self.price_data) < max(self.bb_window, self.atr_window):
            return

        indicator_bb = ta.volatility.BollingerBands(
            close=self.price_data["close"],
            window=self.bb_window,
            window_dev=self.bb_std,
        )
        self.price_data["bb_high"] = indicator_bb.bollinger_hband()
        self.price_data["bb_low"] = indicator_bb.bollinger_lband()
        self.price_data["bb_mid"] = indicator_bb.bollinger_mavg()

        indicator_atr = ta.volatility.AverageTrueRange(
            high=self.price_data["high"],
            low=self.price_data["low"],
            close=self.price_data["close"],
            window=self.atr_window,
        )
        self.price_data["atr"] = indicator_atr.average_true_range()

    @staticmethod
    def _normalize_side(raw_side: Any) -> Optional[str]:
        side = str(raw_side).lower()
        if side in {"buy", "long"}:
            return "buy"
        if side in {"sell", "short"}:
            return "sell"
        return None

    def get_signal(self) -> Optional[Dict[str, Any]]:
        """
        Generate entry signal from the latest candle.

        Entry is based on previous candle close crossing Bollinger Bands.
        """
        min_rows = max(self.bb_window, self.atr_window) + 1
        if len(self.price_data) < min_rows:
            return None

        current_candle = self.price_data.iloc[-1]
        previous_candle = self.price_data.iloc[-2]

        if self.current_position:
            return None

        for key in ("bb_low", "bb_high", "bb_mid", "atr"):
            value = current_candle.get(key) if key in current_candle else None
            if value is None or pd.isna(value):
                return None

        atr = float(current_candle["atr"])
        if atr <= 0:
            return None

        entry_price = float(current_candle["open"])
        sl_distance = atr * self.sl_atr_multiplier
        if sl_distance <= 0:
            return None

        position_size_units = self.risk_amount / sl_distance
        position_size_usdt = float(position_size_units * entry_price)
        if position_size_usdt <= 0:
            return None

        middle_band = float(current_candle["bb_mid"])

        if float(previous_candle["close"]) < float(previous_candle["bb_low"]):
            stop_loss = entry_price - sl_distance
            return {
                "side": "buy",
                "amount_usdt": position_size_usdt,
                "confidence": 1.0,
                "reason": f"Close < Lower BB ({float(previous_candle['bb_low']):.2f})",
                "sl_price": stop_loss,
                "tp_price": middle_band,
                "tp_condition": "middle_band",
            }

        if float(previous_candle["close"]) > float(previous_candle["bb_high"]):
            stop_loss = entry_price + sl_distance
            return {
                "side": "sell",
                "amount_usdt": position_size_usdt,
                "confidence": 1.0,
                "reason": f"Close > Upper BB ({float(previous_candle['bb_high']):.2f})",
                "sl_price": stop_loss,
                "tp_price": middle_band,
                "tp_condition": "middle_band",
            }

        return None

    def check_exit(self, current_price: float, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check dynamic exit conditions for an open position."""
        if not position or self.price_data.empty:
            return None

        side = self._normalize_side(position.get("side"))
        if side is None:
            return None

        middle_band = self.price_data.iloc[-1].get("bb_mid")
        if middle_band is None or pd.isna(middle_band):
            return None

        self.current_position = position
        middle_band = float(middle_band)

        if side == "buy" and current_price >= middle_band:
            return {
                "action": "close",
                "side": "sell",
                "reason": f"Touched middle band ({middle_band:.2f})",
                "type": "market",
            }

        if side == "sell" and current_price <= middle_band:
            return {
                "action": "close",
                "side": "buy",
                "reason": f"Touched middle band ({middle_band:.2f})",
                "type": "market",
            }

        return None
