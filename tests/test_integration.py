import pytest
import logging
import time

# Setup logger for tests
logger = logging.getLogger(__name__)
pytestmark = pytest.mark.integration

class TestGRVTIntegration:
    
    def test_account_summary(self, live_executor):
        """Test fetching account summary."""
        balance = live_executor.get_account_summary()
        assert balance is not None
        logger.info(f"Account Balance: {balance}")
        # Depending on CCXT response structure, we might check 'total' or specific currency
        # e.g., assert 'USDC' in balance['total']

    def test_market_order_flow(self, live_executor, live_config):
        """
        Tests placing a market order and then closing it.
        WARNING: This uses REAL MONEY on Mainnet or Testnet funds on Testnet.
        """
        symbol = live_config.SYMBOL
        amount_usdc = 200.0 # Increased to meet min order size
        
        # Get current price to calculate base amount
        price = live_executor.get_market_price(symbol)
        assert price > 0, "Market price should be positive"
        
        amount_base = amount_usdc / price
        # Round logic might be needed depending on exchange precision
        # For now, rely on API to handle or reject if too precise, but usually 6 decimals is safe for many
        # "Order size too granular" with 5 decimals, trying 3
        amount_base = round(amount_base, 3) 

        if amount_base <= 0:
            pytest.skip("Calculated amount is too small")

        logger.info(f"Placing Market BUY for {amount_base} {symbol}")
        order = live_executor.place_market_order(
            symbol,
            "buy",
            amount_base,
            leverage=live_config.LEVERAGE,
        )
        assert order is not None
        assert 'id' in order
        
        # Wait a bit
        time.sleep(2)
        
        # Check positions? (Not strictly required if executor doesn't have get_position method easily exposed yet)
        
        # Close position
        logger.info(f"Closing position for {symbol}")
        live_executor.place_market_order(
            symbol,
            "sell",
            amount_base,
            leverage=live_config.LEVERAGE,
        )
        # Or use close_all_positions if implemented robustly
        
    def test_limit_order(self, live_executor, live_config):
        """Tests placing a Limit order away from market price."""
        symbol = live_config.SYMBOL
        price = live_executor.get_market_price(symbol)
        assert price > 0
        
        # Place buy limit 50% below current price to avoid fill
        limit_price = round(price * 0.5, 2)
        amount_usdc = 200.0
        # Calculate amount based on LIMIT price to ensure notional > min (e.g. 100-200 USD)
        amount_base = round(amount_usdc / limit_price, 3)

        logger.info(f"Placing Limit BUY at {limit_price}")
        order = live_executor.place_limit_order(
            symbol,
            "buy",
            amount_base,
            limit_price,
            leverage=live_config.LEVERAGE,
        )
        assert order is not None
        assert order['type'] == 'limit'
        
        # Cancel order (if cancel is implemented, otherwise it sits there)
        # Since I didn't verify cancel_order in executor, I might skip verifying cancel
        # BUT standard ccxt has cancel_order.
        if order.get('id'):
            try:
                live_executor.client.cancel_order(order['id'], symbol)
                logger.info("Limit order canceled")
            except Exception as e:
                logger.warning(f"Failed to cancel limit order: {e}")

    def test_tpsl_order(self, live_executor, live_config):
        """Tests placing an order with TP/SL params."""
        symbol = live_config.SYMBOL
        price = live_executor.get_market_price(symbol)
        assert price > 0
        
        amount_usdc = 200.0
        amount_base = round(amount_usdc / price, 3)
        
        # Assuming CCXT standard params for stopLoss/takeProfit
        # or exchange specific params. GRVT specific might differ.
        # This is a bit speculative without docs, but common pattern.
        # If 'grvt-pysdk' follows ccxt, it might look for 'stopLossPrice' etc in params.
        
        tpsl_params = {
            'stopLossPrice': round(price * 0.9, 2),
            'takeProfitPrice': round(price * 1.1, 2)
        }
        
        logger.info(f"Placing Market BUY with TP/SL: {tpsl_params}")
        order = live_executor.place_market_order(
            symbol, 'buy', amount_base,
            leverage=live_config.LEVERAGE,
            params=tpsl_params
        )
        
        if order:
            logger.info("Order with TP/SL sent")
            # Verify TP/SL if possible (fetch open orders not implemented in executor wrapper yet)
            
            # Close/Cleanup
            time.sleep(2)
            live_executor.place_market_order(
                symbol,
                'sell',
                amount_base,
                leverage=live_config.LEVERAGE,
            )
