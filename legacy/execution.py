import logging
import time
import random
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any
from eth_account import Account

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

import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GRVTExecutor:
    def __init__(self):
        self.api_key = config.GRVT_API_KEY
        self.private_key = config.GRVT_PRIVATE_KEY
        self.trading_account_id = config.GRVT_TRADING_ACCOUNT_ID
        self.sub_account_id = config.GRVT_SUB_ACCOUNT_ID
        self.env_str = config.GRVT_ENV
        self.client = None
        
        self.initialize_client()

    def initialize_client(self):
        try:
            env = GrvtEnv(self.env_str)
            params = {
                "api_key": self.api_key,
                "trading_account_id": self.trading_account_id,
                "private_key": self.private_key,
            }
            # Initialize the CCXT-compatible client
            self.client = GrvtCcxt(env, logger, parameters=params)
            logger.info(f"Initialized GRVT client for env: {self.env_str}")
        except Exception as e:
            logger.error(f"Failed to initialize GRVT client: {e}")
            raise

    def get_account_summary(self):
        """Fetches account summary specifically for the sub-account."""
        try:
            # GrvtCcxt might not support params for fetch_balance, or requires specific structure.
            # detailed log of what is returned
            balance = self.client.fetch_balance() 
            return balance
        except Exception as e:
            logger.error(f"Error fetching account summary: {e}")
            return None

    def get_market_price(self, symbol: str) -> float:
        try:
            ticker = self.client.fetch_ticker(symbol)
            # Check for standard CCXT 'last' or raw 'last_price'
            if 'last' in ticker:
                return float(ticker['last'])
            elif 'last_price' in ticker:
                return float(ticker['last_price'])
            elif 'result' in ticker and 'last_price' in ticker['result']:
                 return float(ticker['result']['last_price'])
            
            logger.error(f"Unknown ticker structure: {ticker}")
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return 0.0

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol. Calls set_leverage if supported by client."""
        try:
            logger.info(f"Attempting to set leverage {leverage}x for {symbol}")
            # Try using the client's set_leverage method
            if hasattr(self.client, 'set_leverage') and callable(self.client.set_leverage):
                result = self.client.set_leverage(leverage, symbol)
                logger.info(f"Set leverage response: {result}")
                return result
            else:
                logger.warning("set_leverage not available in client")
                return None
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def place_market_order(self, symbol: str, side: str, amount: float, leverage: int = None, params: Dict = None):
        """
        Places a market order.
        side: 'buy' or 'sell'
        amount: quantity in base currency (e.g. BTC)
        params: Optional dict for extra params like 'stopLossPrice', 'takeProfitPrice' if supported.
        """
        try:
            req_params = {'sub_account_id': self.sub_account_id}
            if params:
                req_params.update(params)

            # Place order
            # order_type='market'
            order = self.client.create_order(
                symbol=symbol,
                order_type='market',
                side=side,
                amount=amount,
                params=req_params
            )
            return self._handle_order_response(order, 'market')
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float, leverage: int = None, params: Dict = None):
        """
        Places a limit order.
        side: 'buy' or 'sell'
        amount: quantity in base currency
        price: limit price
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
            logger.error(f"Error placing limit order: {e}")
            return None

    def _handle_order_response(self, order_response: Dict, order_type: str) -> Optional[Dict]:
        """Validates and normalizes the order response."""
        if not order_response:
            return None
            
        # Check for error in response (e.g. {'code': 2066, ...})
        if 'code' in order_response and order_response['code'] != 0:
             # Some APIs use 0 for success, others don't return code on success.
             # Based on logs, error has 'code' and 'status': 400
             if order_response.get('status') != 200 and 'message' in order_response:
                 logger.error(f"Order failed: {order_response}")
                 return None

        # Normalize result
        # Success response: {'result': {'order_id': '...', ...}}
        result = order_response.get('result', {})
        if 'order_id' in result:
            # Flatten or add id for CCXT compatibility
            order_response['id'] = result['order_id']
            order_response['type'] = order_type # Manually add type for tests
        elif 'order_id' in order_response:
             order_response['id'] = order_response['order_id']
             order_response['type'] = order_type

        # Double check if we successfully got an ID
        if 'id' in order_response:
             logger.info(f"{order_type.capitalize()} Order placed: {order_response['id']}")
             return order_response
        
        logger.warning(f"Order placed but ID not found in response: {order_response}")
        return order_response

    def close_all_positions(self, symbol: str):
        """Closes all matching positions for the symbol."""
        try:
            positions = self.client.fetch_positions([symbol])
            for position in positions:
                contracts = position['contracts']
                if contracts != 0:
                    side = 'sell' if contracts > 0 else 'buy'
                    amount = abs(contracts)
                    logger.info(f"Closing position: {contracts} contracts of {symbol}")
                    self.place_market_order(symbol, side, amount)
        except Exception as e:
            logger.error(f"Error closing positions: {e}")

if __name__ == "__main__":
    # Simple test
    try:
        executor = GRVTExecutor()
        print("Client initialized successfully.")
    except Exception as e:
        print(f"Initialization failed: {e}")
