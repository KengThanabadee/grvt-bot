import sys
import os

# Add root to path just in case
sys.path.insert(0, os.getcwd())

try:
    # Just skip direct pysdk import if it fails, focusing on executor
    pass
except ImportError:
    pass

try:
    from grvt_bot.core.executor import GRVTExecutor
    from grvt_bot.core.config import ConfigManager
    
    # Init config
    config = ConfigManager("config/config.yaml") # Ensure this file exists and has credentials
    
    executor = GRVTExecutor(config)
    print("Executor Initialized")
    
    if hasattr(executor.client, 'fetch_ohlcv'):
        print("✅ fetch_ohlcv is supported!")
        # Try fetching 1 candle
        try:
            # Use the executor's method which now handles formatting
            klines = executor.fetch_ohlcv(config.SYMBOL, timeframe='15m', limit=5)
            print(f"Fetched {len(klines)} klines")
            if len(klines) > 0:
                print(f"Sample: {klines[0]}")
                print(f"Format check: Timestamp={klines[0][0]}, Open={klines[0][1]}")
        except Exception as e:
            print(f"❌ Error fetching klines: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ fetch_ohlcv is NOT supported by client")
        print(f"Client attributes: {dir(executor.client)}")

except Exception as e:
    print(f"Error: {e}")
