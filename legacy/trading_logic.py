import random
import time
from typing import Optional, Dict
import config

class TradingLogic:
    def __init__(self):
        self.last_signal_time = 0
        self.signal_interval = 60 # Seconds between signals

    def get_signal(self) -> Optional[Dict]:
        """
        Generates a trading signal.
        Returns None if no signal, or a dict: {'side': 'buy'/'sell', 'amount_usdt': float}
        """
        current_time = time.time()
        
        # Simple throttling
        if current_time - self.last_signal_time < self.signal_interval:
            return None

        # Random signal generation for DEMO purposes
        # In a real bot, this would check indicators, price action, etc.
        self.last_signal_time = current_time
        
        chance = random.random()
        if chance < 0.3:
            return {'side': 'buy', 'amount_usdt': config.ORDER_SIZE_USDT}
        elif chance > 0.7:
            return {'side': 'sell', 'amount_usdt': config.ORDER_SIZE_USDT}
        
        return None
