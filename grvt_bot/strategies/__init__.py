"""
Strategies module containing trading strategy implementations.
"""

from grvt_bot.strategies.base import BaseStrategy
from grvt_bot.strategies.random_strategy import RandomStrategy

try:
    from grvt_bot.strategies.paxg_mean_reversion_strategy import PAXGMeanReversionStrategy
except Exception:  # pragma: no cover - optional strategy dependencies may be missing
    PAXGMeanReversionStrategy = None

__all__ = ["BaseStrategy", "RandomStrategy", "PAXGMeanReversionStrategy"]
