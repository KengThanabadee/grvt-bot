#!/usr/bin/env python3
"""
Check Current Leverage Settings on GRVT

This script checks the current leverage settings for your GRVT sub-account.
Useful for verifying leverage before running the bot.
"""

import logging
from execution import GRVTExecutor
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("="*60)
    print("GRVT Leverage Checker")
    print("="*60)
    print()
    
    try:
        # Initialize executor
        logger.info("Connecting to GRVT...")
        executor = GRVTExecutor()
        
        # Check specific symbol from config
        print(f"📊 Checking leverage for: {config.SYMBOL}")
        print(f"   Expected from config.py: {config.LEVERAGE}x")
        print()
        
        result = executor.get_current_leverage(config.SYMBOL)
        
        if result and hasattr(result, 'leverage'):
            print("✅ Current Leverage Settings:")
            print(f"   Symbol: {result.instrument}")
            print(f"   Current: {result.leverage}x")
            print(f"   Min: {result.min_leverage}x")
            print(f"   Max: {result.max_leverage}x")
            print()
            
            # Compare with config
            if result.leverage == str(config.LEVERAGE):
                print("✅ ✅ ✅ PERFECT! Leverage matches config.py")
            else:
                print(f"⚠️  WARNING: Leverage mismatch!")
                print(f"   Exchange has: {result.leverage}x")
                print(f"   Config expects: {config.LEVERAGE}x")
                print()
                print("   👉 Please update leverage on GRVT web interface")
        else:
            print("❌ Could not retrieve leverage settings")
            print("   Please check your API credentials and connection")
        
        print()
        print("-"*60)
        print("Checking all leverage settings...")
        print()
        
        # Check all leverages
        all_leverages = executor.get_current_leverage()
        
        if all_leverages and len(all_leverages) > 0:
            print(f"Found {len(all_leverages)} instruments with leverage settings:")
            print()
            for lev in all_leverages[:10]:  # Show first 10
                print(f"  • {lev.instrument:20s} : {lev.leverage}x (min: {lev.min_leverage}x, max: {lev.max_leverage}x)")
            
            if len(all_leverages) > 10:
                print(f"  ... and {len(all_leverages) - 10} more")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("="*60)

if __name__ == "__main__":
    main()
