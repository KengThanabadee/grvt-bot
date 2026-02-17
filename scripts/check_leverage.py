#!/usr/bin/env python3
"""
Check Current Leverage Settings on GRVT

This script checks the current leverage settings for your GRVT sub-account.
Useful for verifying leverage before running the bot.
"""

import os
import logging
from pathlib import Path
from typing import Any, Optional, Tuple

from grvt_bot.core.config import ConfigManager
from grvt_bot.core.executor import GRVTExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _extract_leverage_value(payload: Any) -> Tuple[Optional[Any], Optional[str]]:
    """
    Best-effort extraction of leverage value from various payload formats.
    """
    if payload is None:
        return None, None

    if isinstance(payload, list):
        if not payload:
            return None, None
        payload = payload[0]

    if isinstance(payload, dict):
        symbol = payload.get("symbol") or payload.get("instrument")

        leverage = payload.get("leverage")
        if leverage is not None:
            return leverage, symbol

        info = payload.get("info")
        if isinstance(info, dict):
            leverage = info.get("leverage")
            if leverage is not None:
                return leverage, symbol

        result = payload.get("result")
        if isinstance(result, dict):
            leverage = result.get("leverage")
            if leverage is not None:
                return leverage, symbol

    return None, None


def main() -> int:
    print("=" * 60)
    print("GRVT Leverage Checker")
    print("=" * 60)
    print()

    try:
        config_path = Path(os.getenv("GRVT_CONFIG_PATH", "config/config.yaml")).resolve()
        if not config_path.exists():
            print(f"Config file not found: {config_path}")
            print("Set GRVT_CONFIG_PATH or create config/config.yaml first.")
            return 1

        config = ConfigManager(config_path=str(config_path))
        config.validate()

        # Initialize executor
        logger.info("Connecting to GRVT...")
        try:
            executor = GRVTExecutor(config, logger)
        except Exception as exc:
            print(f"Could not initialize GRVT client: {exc}")
            print("Please verify network access, API keys, and testnet availability.")
            return 1

        # Check specific symbol from config
        print(f"Checking leverage for: {config.SYMBOL}")
        print(f"Expected from config: {config.LEVERAGE}x")
        print()

        result = executor.get_current_leverage(config.SYMBOL)
        leverage, symbol = _extract_leverage_value(result)
        if leverage is not None:
            print("Current leverage settings:")
            print(f"  Symbol: {symbol or config.SYMBOL}")
            print(f"  Current: {leverage}x")
            print()

            # Compare with config
            if str(leverage) == str(config.LEVERAGE):
                print("Leverage matches config.")
            else:
                print("WARNING: Leverage mismatch.")
                print(f"  Exchange has: {leverage}x")
                print(f"  Config expects: {config.LEVERAGE}x")
                print()
                print("  Please update leverage on GRVT web interface.")
        else:
            print("Could not retrieve leverage settings for symbol.")
            print("Client may not expose leverage query endpoints for this environment.")

        print()
        print("-" * 60)
        print("Checking all leverage settings...")
        print()

        # Check all leverages
        all_leverages = executor.get_current_leverage()
        if isinstance(all_leverages, list) and all_leverages:
            print(f"Found {len(all_leverages)} leverage entries:")
            print()
            for entry in all_leverages[:10]:
                value, entry_symbol = _extract_leverage_value(entry)
                if value is None:
                    continue
                print(f"  - {entry_symbol or 'unknown':20s} : {value}x")

            if len(all_leverages) > 10:
                print(f"  ... and {len(all_leverages) - 10} more")
        elif all_leverages is not None:
            print(f"Leverage response type: {type(all_leverages).__name__}")
            print(all_leverages)
        else:
            print("No leverage summary returned.")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    print()
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
