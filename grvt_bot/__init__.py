"""
GRVT Bot - Modular Trading Bot for GRVT Exchange

A professional trading bot package for the GRVT exchange (Testnet/Prod).
Designed for easy extension with custom trading strategies.
"""

from grvt_bot.core.executor import GRVTExecutor
from grvt_bot.strategies.base import BaseStrategy
from grvt_bot.strategies.random_strategy import RandomStrategy

__version__ = "1.0.0"
__author__ = "GRVT Bot Team"

__all__ = [
    "GRVTExecutor",
    "BaseStrategy", 
    "RandomStrategy",
]
