"""
GRVT Executor - Order Execution and Exchange Interface

Handles connection to GRVT Exchange API, authentication, and order management.
"""

import logging
import sys
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any
from eth_account import Account

# Add parent directory to path to find pysdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import local pysdk
from pysdk.grvt_ccxt import GrvtCcxt
from pysdk.grvt_ccxt_env import GrvtEnv
from pysdk.grvt_raw_types import (
    Kind, 
    Order, 
    OrderLeg, 
    TimeInForce, 
    OrderMetadata, 
    Signature, 
    TriggerBy
)


class GRVTExecutor:
    """
    Executor for GRVT Exchange operations.
    
    Handles authentication, order placement, and position management.
    """
    
    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        """
        Initialize GRVT Executor.
        
        Args:
            config: Configuration object (ConfigManager or dict-like)
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Extract config values
        self.api_key = self._get_config('GRVT_API_KEY')
        self.private_key = self._get_config('GRVT_PRIVATE_KEY')
        self.trading_account_id = self._get_config('GRVT_TRADING_ACCOUNT_ID')
        self.sub_account_id = self._get_config('GRVT_SUB_ACCOUNT_ID')
        self.env_str = self._get_config('GRVT_ENV')
        
        self.client = None
        self.initialize_client()
    
    def _get_config(self, key: str) -> Any:
        """Get configuration value from config object."""
        if hasattr(self.config, key):
            return getattr(self.config, key)
        elif hasattr(self.config, 'get'):
            # Handle dict-like config
            return self.config.get(key)
        else:
            raise ValueError(f"Config missing required field: {key}")
    
    def initialize_client(self) -> None:
        """Initialize the GRVT CCXT client."""
        try:
            env = GrvtEnv(self.env_str)
            params = {
                "api_key": self.api_key,
                "trading_account_id": self.trading_account_id,
                "private_key": self.private_key,
            }
            # Initialize the CCXT-compatible client
            self.client = GrvtCcxt(env, self.logger, parameters=params)
            self.logger.info(f"Initialized GRVT client for env: {self.env_str}")
        except Exception as e:
            self.logger.error(f"Failed to initialize GRVT client: {e}")
            raise
    
    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """
        Fetch account summary for the sub-account.
        
        Returns:
            Account balance information or None on error
        """
        try:
            balance = self.client.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"Error fetching account summary: {e}")
            return None
    
    def get_market_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Current market price or 0.0 on error
        """
        try:
            ticker = self.client.fetch_ticker(symbol)
            
            # Check for standard CCXT 'last' or raw 'last_price'
            if 'last' in ticker:
                return float(ticker['last'])
            elif 'last_price' in ticker:
                return float(ticker['last_price'])
            elif 'result' in ticker and 'last_price' in ticker['result']:
                return float(ticker['result']['last_price'])
            
            self.logger.error(f"Unknown ticker structure: {ticker}")
            return 0.0
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            return 0.0
    
    def set_leverage(self, symbol: str, leverage: int) -> Optional[Dict[str, Any]]:
        """
        Set leverage for a symbol.
        
        Note: May not be supported by API. Set manually on web interface.
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage multiplier
        
        Returns:
            API response or None
        """
        try:
            self.logger.info(f"Attempting to set leverage {leverage}x for {symbol}")
            
            # Try using the client's set_leverage method
            if hasattr(self.client, 'set_leverage') and callable(self.client.set_leverage):
                result = self.client.set_leverage(leverage, symbol)
                self.logger.info(f"Set leverage response: {result}")
                return result
            else:
                self.logger.warning("set_leverage not available in client")
                return None
        except Exception as e:
            self.logger.error(f"Error setting leverage: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        amount: float, 
        leverage: Optional[int] = None, 
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Quantity in base currency (e.g. BTC)
            leverage: Leverage (optional, may not be used)
            params: Extra params like 'stopLossPrice', 'takeProfitPrice'
        
        Returns:
            Order response or None on error
        """
        try:
            req_params = {'sub_account_id': self.sub_account_id}
            if params:
                req_params.update(params)
            
            # Place order
            order = self.client.create_order(
                symbol=symbol,
                order_type='market',
                side=side,
                amount=amount,
                params=req_params
            )
            return self._handle_order_response(order, 'market')
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def place_limit_order(
        self, 
        symbol: str, 
        side: str, 
        amount: float, 
        price: float, 
        leverage: Optional[int] = None, 
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Quantity in base currency
            price: Limit price
            leverage: Leverage (optional, may not be used)
            params: Extra parameters
        
        Returns:
            Order response or None on error
        """
        try:
            req_params = {'sub_account_id': self.sub_account_id}
            if params:
                req_params.update(params)
            
            order = self.client.create_order(
                symbol=symbol,
                order_type='limit',
                side=side,
                amount=amount,
                price=price,
                params=req_params
            )
            return self._handle_order_response(order, 'limit')
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _handle_order_response(
        self, 
        order_response: Optional[Dict], 
        order_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate and normalize the order response.
        
        Args:
            order_response: Raw response from exchange
            order_type: 'market' or 'limit'
        
        Returns:
            Normalized order response or None
        """
        if not order_response:
            return None
        
        # Check for error in response
        if 'code' in order_response and order_response['code'] != 0:
            if order_response.get('status') != 200 and 'message' in order_response:
                self.logger.error(f"Order failed: {order_response}")
                return None
        
        # Normalize result
        result = order_response.get('result', {})
        if 'order_id' in result:
            order_response['id'] = result['order_id']
            order_response['type'] = order_type
        elif 'order_id' in order_response:
            order_response['id'] = order_response['order_id']
            order_response['type'] = order_type
        
        # Check if we successfully got an ID
        if 'id' in order_response:
            self.logger.info(f"{order_type.capitalize()} Order placed: {order_response['id']}")
            return order_response
        
        self.logger.warning(f"Order placed but ID not found in response: {order_response}")
        return order_response
    
    def close_all_positions(self, symbol: str) -> None:
        """
        Close all open positions for a symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        try:
            positions = self.client.fetch_positions([symbol])
            for position in positions:
                contracts = position.get('contracts', 0)
                if contracts != 0:
                    side = 'sell' if contracts > 0 else 'buy'
                    amount = abs(contracts)
                    self.logger.info(f"Closing position: {contracts} contracts of {symbol}")
                    self.place_market_order(symbol, side, amount)
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
