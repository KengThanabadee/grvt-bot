import time
import logging
import sys
import traceback

# Add current directory to path to ensure local imports work if run directly
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execution import GRVTExecutor
import config
from trading_logic import TradingLogic

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("grvt_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

def main():
    logger.info("Starting GRVT Demo Bot...")
    logger.info(f"Environment: {config.GRVT_ENV}")
    logger.info(f"Trading Symbol: {config.SYMBOL}")

    try:
        # Initialize Executor
        executor = GRVTExecutor()
        
        # Initialize Strategy
        strategy = TradingLogic()
        
        logger.info("Bot initialized successfully. Starting main loop.")
        logger.info(f"IMPORTANT: Set leverage to {config.LEVERAGE}x on GRVT web interface manually.")
        
        while True:
            try:
                # 1. Get Signal
                signal = strategy.get_signal()
                
                if signal:
                    logger.info(f"Signal received: {signal}")
                    
                    side = signal['side']
                    amount_usdt = signal.get('amount_usdt', config.ORDER_SIZE_USDT)
                    
                    # Convert USDT amount to base currency amount roughly
                    # This requires current price
                    price = executor.get_market_price(config.SYMBOL)
                    if price > 0:
                        amount_base = amount_usdt / price
                        # Round to 3 decimal places for larger order size
                        amount_base = round(amount_base, 3)
                        
                        logger.info(f"Executing {side} order for {amount_base:.3f} {config.SYMBOL} (~{amount_usdt} USDT)")
                        
                        # 2. Execute Order
                        executor.place_market_order(
                            symbol=config.SYMBOL,
                            side=side,
                            amount=amount_base,
                            leverage=config.LEVERAGE
                        )
                    else:
                        logger.warning("Could not fetch market price, skipping order.")
                
                # Sleep to prevent tight loop
                time.sleep(config.MAIN_LOOP_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.error(traceback.format_exc())
                time.sleep(5) # Wait a bit before retrying after error
                
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())

if __name__ == "__main__":
    main()
