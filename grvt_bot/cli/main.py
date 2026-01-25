"""
CLI Entry Point for GRVT Bot

Command-line interface for running the trading bot.
"""

import time
import sys
import os
import argparse
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from grvt_bot.core.executor import GRVTExecutor
from grvt_bot.core.config import ConfigManager
from grvt_bot.strategies.random_strategy import RandomStrategy
from grvt_bot.utils.logger import setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="GRVT Trading Bot - Automated trading for GRVT Exchange"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        default='random',
        choices=['random'],
        help='Trading strategy to use (default: random)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default='grvt_bot.log',
        help='Path to log file (default: grvt_bot.log)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no real orders)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the trading bot."""
    args = parse_args()
    
    # Setup logger
    import logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger("grvt_bot", args.log_file, log_level)
    
    logger.info("=" * 60)
    logger.info("GRVT Trading Bot Starting...")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        
        # Check if config file exists
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config file not found: {args.config}")
            logger.info("Please create a config file from config/config.example.yaml")
            return 1
        
        config = ConfigManager(config_path=str(config_path))
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Invalid configuration: {e}")
            return 1
        
        logger.info(f"Environment: {config.GRVT_ENV}")
        logger.info(f"Trading Symbol: {config.SYMBOL}")
        logger.info(f"Order Size: {config.ORDER_SIZE_USDT} USDT")
        logger.info(f"Leverage: {config.LEVERAGE}x")
        
        if args.dry_run:
            logger.warning("⚠️  DRY RUN MODE - No real orders will be placed!")
        
        # Initialize Executor
        logger.info("Initializing GRVT Executor...")
        executor = GRVTExecutor(config, logger)
        
        # Initialize Strategy
        logger.info(f"Initializing strategy: {args.strategy}")
        
        if args.strategy == 'random':
            strategy = RandomStrategy(config, logger)
        else:
            logger.error(f"Unknown strategy: {args.strategy}")
            return 1
        
        strategy.initialize()
        
        logger.info("✓ Bot initialized successfully!")
        logger.info(f"⚠️  IMPORTANT: Ensure leverage is set to {config.LEVERAGE}x on GRVT web interface")
        logger.info("")
        logger.info("Starting main trading loop...")
        logger.info(f"Loop interval: {config.MAIN_LOOP_INTERVAL} seconds")
        logger.info("")
        
        # Main trading loop
        loop_count = 0
        while True:
            try:
                loop_count += 1
                logger.debug(f"Loop iteration: {loop_count}")
                
                # 1. Get trading signal from strategy
                signal = strategy.get_signal()
                
                if signal:
                    logger.info(f"📊 Signal received: {signal}")
                    
                    side = signal['side']
                    amount_usdt = signal.get('amount_usdt', config.ORDER_SIZE_USDT)
                    reason = signal.get('reason', 'No reason provided')
                    
                    logger.info(f"   Reason: {reason}")
                    
                    # 2. Get current market price
                    price = executor.get_market_price(config.SYMBOL)
                    
                    if price > 0:
                        # Convert USDT amount to base currency
                        amount_base = amount_usdt / price
                        amount_base = round(amount_base, 3)
                        
                        logger.info(
                            f"📈 Executing {side.upper()} order: "
                            f"{amount_base:.3f} {config.SYMBOL} "
                            f"(~{amount_usdt} USDT at ${price:.2f})"
                        )
                        
                        # 3. Execute order (unless dry-run)
                        if not args.dry_run:
                            order = executor.place_market_order(
                                symbol=config.SYMBOL,
                                side=side,
                                amount=amount_base,
                                leverage=config.LEVERAGE
                            )
                            
                            if order:
                                strategy.on_order_placed(order)
                                logger.info(f"✓ Order placed successfully: {order.get('id')}")
                            else:
                                logger.error("✗ Order placement failed")
                        else:
                            logger.info("   [DRY RUN] Order would be placed here")
                    else:
                        logger.warning("⚠️  Could not fetch market price, skipping order")
                
                # Sleep to prevent tight loop
                time.sleep(config.MAIN_LOOP_INTERVAL)
                
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                logger.error(traceback.format_exc())
                strategy.on_error(e)
                time.sleep(5)  # Wait before retrying
                
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Bot stopped by user (Ctrl+C)")
        logger.info("=" * 60)
        
        # Cleanup
        if 'strategy' in locals():
            strategy.cleanup()
        
        return 0
        
    except Exception as e:
        logger.critical(f"💥 Fatal error: {e}")
        logger.critical(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
