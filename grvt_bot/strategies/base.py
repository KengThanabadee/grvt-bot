"""
Base Strategy Class

All trading strategies should inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Subclasses must implement the get_signal() method at minimum.
    """
    
    def __init__(self, config: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the strategy.
        
        Args:
            config: Configuration object or dict
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.name = self.__class__.__name__
        
    @abstractmethod
    def get_signal(self) -> Optional[Dict[str, Any]]:
        """
        Generate a trading signal.
        
        Returns:
            None if no signal, or a dict with:
                - 'side': 'buy' or 'sell'
                - 'amount_usdt': float (optional, uses default if not provided)
                - 'confidence': float 0-1 (optional)
                - 'reason': str (optional, for logging)
        
        Example:
            {
                'side': 'buy',
                'amount_usdt': 500,
                'confidence': 0.85,
                'reason': 'MA crossover detected'
            }
        """
        pass
    
    def on_order_placed(self, order: Dict[str, Any]) -> None:
        """
        Called after an order is successfully placed.
        
        Args:
            order: Order details from exchange
        """
        self.logger.info(f"[{self.name}] Order placed: {order.get('id', 'N/A')}")
    
    def on_order_filled(self, order: Dict[str, Any]) -> None:
        """
        Called when an order is filled.
        
        Args:
            order: Filled order details
        """
        self.logger.info(f"[{self.name}] Order filled: {order.get('id', 'N/A')}")
    
    def on_error(self, error: Exception) -> None:
        """
        Called when an error occurs during strategy execution.
        
        Args:
            error: The exception that occurred
        """
        self.logger.error(f"[{self.name}] Strategy error: {error}")
    
    def initialize(self) -> None:
        """
        Initialize strategy (load data, setup indicators, etc.).
        Called once before the main loop starts.
        """
        self.logger.info(f"[{self.name}] Strategy initialized")
    
    def cleanup(self) -> None:
        """
        Cleanup resources before strategy stops.
        Called once when bot is shutting down.
        """
        self.logger.info(f"[{self.name}] Strategy cleanup")
    
    def __repr__(self) -> str:
        return f"{self.name}()"
