"""
Random Strategy - Demo Trading Strategy

Generates random buy/sell signals for demonstration purposes.
This should be replaced with a real strategy for production use.
"""

import random
import time
from typing import Optional, Dict, Any

from grvt_bot.strategies.base import BaseStrategy


class RandomStrategy(BaseStrategy):
    """
    Random signal generator for demonstration.
    
    Generates random buy/sell signals with throttling to avoid
    excessive trading. This is for DEMO purposes only!
    """
    
    def __init__(self, config: Optional[Any] = None, logger: Optional[Any] = None):
        """
        Initialize random strategy.
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        super().__init__(config, logger)
        self.last_signal_time = 0
        
        # Get signal interval from config or use default
        if config and hasattr(config, 'MAIN_LOOP_INTERVAL'):
            self.signal_interval = config.MAIN_LOOP_INTERVAL
        elif config and hasattr(config, 'get'):
            self.signal_interval = config.get('trading', 'loop_interval', 60)
        else:
            self.signal_interval = 60
        
        self.logger.info(f"RandomStrategy initialized with {self.signal_interval}s interval")
    
    def get_signal(self) -> Optional[Dict[str, Any]]:
        """
        Generate a random trading signal.
        
        Returns:
            None if no signal, or dict with 'side' and 'amount_usdt'
        """
        current_time = time.time()
        
        # Throttling: don't generate signals too frequently
        if current_time - self.last_signal_time < self.signal_interval:
            return None
        
        # Random signal generation for DEMO purposes
        # In a real bot, this would check indicators, price action, etc.
        self.last_signal_time = current_time
        
        chance = random.random()
        
        # Get order size from config
        if self.config:
            if hasattr(self.config, 'ORDER_SIZE_USDT'):
                order_size = self.config.ORDER_SIZE_USDT
            elif hasattr(self.config, 'get'):
                order_size = self.config.get('trading', 'order_size_usdt', 500)
            else:
                order_size = 500
        else:
            order_size = 500
        
        # 30% chance to buy
        if chance < 0.3:
            self.logger.info(f"[RandomStrategy] Generated BUY signal (chance: {chance:.2f})")
            return {
                'side': 'buy',
                'amount_usdt': order_size,
                'confidence': 0.5,
                'reason': f'Random signal (chance: {chance:.2f})'
            }
        
        # 30% chance to sell
        elif chance > 0.7:
            self.logger.info(f"[RandomStrategy] Generated SELL signal (chance: {chance:.2f})")
            return {
                'side': 'sell',
                'amount_usdt': order_size,
                'confidence': 0.5,
                'reason': f'Random signal (chance: {chance:.2f})'
            }
        
        # 40% chance: no signal
        return None
    
    def initialize(self) -> None:
        """Initialize the random strategy."""
        super().initialize()
        self.logger.info("RandomStrategy: Ready to generate random signals")
        self.logger.warning(
            "⚠️  RandomStrategy is for DEMO only! "
            "Replace with a real strategy for production use."
        )
