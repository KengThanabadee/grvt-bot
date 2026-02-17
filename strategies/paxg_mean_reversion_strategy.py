"""
Backward-compatibility shim for the PAXG strategy import path.

Prefer importing from:
    grvt_bot.strategies.paxg_mean_reversion_strategy
"""

from grvt_bot.strategies.paxg_mean_reversion_strategy import PAXGMeanReversionStrategy

__all__ = ["PAXGMeanReversionStrategy"]
