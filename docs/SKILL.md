---
name: GRVT Trading Bot
description: Automated trading bot for GRVT Exchange with customizable strategies
---

# GRVT Trading Bot - Antigravity Skill

A professional, modular Python package for automated trading on the GRVT Exchange (Testnet/Prod). This skill provides a complete trading bot framework with extensible strategy architecture.

## 🎯 What This Skill Does

This skill helps you:
- 🤖 **Run automated trading bots** on GRVT Exchange
- 📊 **Create custom trading strategies** by extending base classes
- ⚙️ **Manage configurations** via YAML files
- 📈 **Execute orders** (market, limit) with proper error handling
- 🔍 **Monitor and log** all trading activity

## 📦 Package Structure

```
grvt_bot/
├── core/           # Core functionality
│   ├── executor.py  # GRVT API interaction
│   └── config.py    # Configuration management
├── strategies/      # Trading strategies
│   ├── base.py      # Base strategy class
│   └── random_strategy.py  # Example strategy
├── utils/          # Utilities
│   └── logger.py    # Logging setup
└── cli/            # Command-line interface
    └── main.py      # Entry point
```

## 🚀 Quick Start

### 1. Installation

Install the package in development mode:

```bash
pip install -e .
```

This will:
- Install all dependencies
- Create a `grvt-bot` command
- Make the package importable

### 2. Configuration

Create your configuration file:

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit with your credentials
nano config/config.yaml
```

Required configuration:
```yaml
grvt:
  env: "testnet"  # or "prod"
  api_key: "your_api_key"
  private_key: "0x..."
  trading_account_id: "your_account_id"
  sub_account_id: "0"

trading:
  symbol: "BTC_USDT_Perp"
  leverage: 10
  order_size_usdt: 500
  loop_interval: 60
```

### 3. Run the Bot

```bash
# Run with default config
grvt-bot

# Run with custom config
grvt-bot --config my_config.yaml

# Run in dry-run mode (no real orders)
grvt-bot --dry-run

# Run with different strategy
grvt-bot --strategy random

# Show help
grvt-bot --help
```

## 📚 Usage as Python Package

### Basic Usage

```python
from grvt_bot import GRVTExecutor, RandomStrategy
from grvt_bot.core.config import ConfigManager
from grvt_bot.utils.logger import setup_logger

# Setup
logger = setup_logger("my_bot")
config = ConfigManager(config_path="config/config.yaml")

# Initialize
executor = GRVTExecutor(config, logger)
strategy = RandomStrategy(config, logger)

# Get signal
signal = strategy.get_signal()

# Execute order
if signal:
    price = executor.get_market_price(config.SYMBOL)
    amount = signal['amount_usdt'] / price
    
    executor.place_market_order(
        symbol=config.SYMBOL,
        side=signal['side'],
        amount=amount
    )
```

### Creating Custom Strategies

Create a new strategy by inheriting from `BaseStrategy`:

```python
from grvt_bot.strategies.base import BaseStrategy
from typing import Optional, Dict, Any

class MyCustomStrategy(BaseStrategy):
    """My custom trading strategy."""
    
    def __init__(self, config, logger=None):
        super().__init__(config, logger)
        # Initialize your indicators, data, etc.
    
    def get_signal(self) -> Optional[Dict[str, Any]]:
        """
        Generate trading signal based on your logic.
        
        Returns:
            None or dict with 'side', 'amount_usdt', 'reason'
        """
        # Your strategy logic here
        # Example: MA crossover, RSI, etc.
        
        if self.should_buy():
            return {
                'side': 'buy',
                'amount_usdt': 500,
                'confidence': 0.8,
                'reason': 'MA crossover detected'
            }
        
        if self.should_sell():
            return {
                'side': 'sell',
                'amount_usdt': 500,
                'confidence': 0.8,
                'reason': 'Overbought on RSI'
            }
        
        return None
    
    def should_buy(self) -> bool:
        # Implement your buy logic
        pass
    
    def should_sell(self) -> bool:
        # Implement your sell logic
        pass
```

Then use it:

```python
from my_module import MyCustomStrategy

strategy = MyCustomStrategy(config, logger)
strategy.initialize()

# Use in main loop
signal = strategy.get_signal()
```

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `grvt-bot` | Run bot with default settings |
| `grvt-bot --config PATH` | Use custom config file |
| `grvt-bot --strategy NAME` | Select strategy (currently: random) |
| `grvt-bot --dry-run` | Test mode (no real orders) |
| `grvt-bot --log-level LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) |
| `grvt-bot --help` | Show all options |

## 📊 API Reference

### GRVTExecutor

Main class for interacting with GRVT Exchange.

**Methods:**
- `get_market_price(symbol)` - Get current price
- `place_market_order(symbol, side, amount)` - Place market order
- `place_limit_order(symbol, side, amount, price)` - Place limit order
- `get_account_summary()` - Get account balance
- `close_all_positions(symbol)` - Close all positions
- `set_leverage(symbol, leverage)` - Set leverage (if supported)

### BaseStrategy

Abstract base class for all strategies.

**Methods to Override:**
- `get_signal()` - **Required.** Generate trading signal
- `initialize()` - Optional. Setup before main loop
- `cleanup()` - Optional. Cleanup when stopping
- `on_order_placed(order)` - Optional. Called after order placed
- `on_order_filled(order)` - Optional. Called when order filled
- `on_error(error)` - Optional. Called on error

### ConfigManager

Manages configuration from YAML, env vars, or dict.

**Properties:**
- `GRVT_ENV` - Environment (testnet/prod)
- `GRVT_API_KEY` - API key
- `GRVT_PRIVATE_KEY` - Private key
- `SYMBOL` - Trading symbol
- `LEVERAGE` - Leverage multiplier
- `ORDER_SIZE_USDT` - Order size in USDT
- `MAIN_LOOP_INTERVAL` - Loop interval in seconds

## ⚠️ Important Notes

### Security

> **⚠️ WARNING**: Never commit credentials to git!
> - Use `config/config.yaml` (ignored by .gitignore)
> - Or use environment variables
> - Keep your private keys secure

### Leverage

> **⚠️ IMPORTANT**: Leverage must be set manually on GRVT web interface!
> 
> The bot cannot set leverage via API. Before running:
> 1. Login to GRVT web interface
> 2. Navigate to your account settings
> 3. Set leverage for your trading pair
> 4. Then run the bot

### Testing

> **⚠️ ALWAYS test on testnet first!**
> 
> - Use `env: "testnet"` in config
> - Test with small amounts
> - Use `--dry-run` mode to verify logic
> - Only move to prod after thorough testing

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=grvt_bot --cov-report=html

# Run specific test
pytest tests/test_executor.py
```

### Code Formatting

```bash
# Format code
black grvt_bot/

# Check linting
flake8 grvt_bot/

# Type checking
mypy grvt_bot/
```

## 📖 Examples

### Example 1: Simple Bot Runner

```python
from grvt_bot.cli.main import main
import sys

# Run the bot
sys.exit(main())
```

### Example 2: Custom Bot with Multiple Strategies

```python
from grvt_bot import GRVTExecutor
from grvt_bot.core.config import ConfigManager
from grvt_bot.utils.logger import setup_logger
from my_strategies import MAStrategy, RSIStrategy, CombinedStrategy

logger = setup_logger("multi_strategy_bot")
config = ConfigManager(config_path="config/config.yaml")
executor = GRVTExecutor(config, logger)

# Initialize strategies
strategies = [
    MAStrategy(config, logger),
    RSIStrategy(config, logger),
    CombinedStrategy(config, logger),
]

# Main loop
import time
while True:
    for strategy in strategies:
        signal = strategy.get_signal()
        if signal:
            # Execute trade
            price = executor.get_market_price(config.SYMBOL)
            amount = signal['amount_usdt'] / price
            executor.place_market_order(
                config.SYMBOL,
                signal['side'],
                amount
            )
    
    time.sleep(60)
```

### Example 3: Backtesting Setup

```python
from grvt_bot.strategies.base import BaseStrategy
from grvt_bot.core.config import ConfigManager

class BacktestStrategy(BaseStrategy):
    def __init__(self, config, historical_data):
        super().__init__(config)
        self.data = historical_data
        self.current_idx = 0
    
    def get_signal(self):
        if self.current_idx >= len(self.data):
            return None
        
        # Analyze current data point
        candle = self.data[self.current_idx]
        self.current_idx += 1
        
        # Your backtesting logic
        return self.analyze(candle)

# Run backtest
config = ConfigManager(config_dict={'trading': {'order_size_usdt': 500}})
strategy = BacktestStrategy(config, load_historical_data())

results = run_backtest(strategy)
print(f"Win rate: {results['win_rate']}")
```

## 🔗 Related Files

- [README.md](file:///e:/work/week1_01_26/bot_test/grvt_demo_bot/README.md) - Main documentation
- [PROJECT_OVERVIEW_TH.md](file:///e:/work/week1_01_26/bot_test/grvt_demo_bot/PROJECT_OVERVIEW_TH.md) - Thai overview
- [config/config.example.yaml](file:///e:/work/week1_01_26/bot_test/grvt_demo_bot/config/config.example.yaml) - Config template
- [setup.py](file:///e:/work/week1_01_26/bot_test/grvt_demo_bot/setup.py) - Package setup
- [pyproject.toml](file:///e:/work/week1_01_26/bot_test/grvt_demo_bot/pyproject.toml) - Modern packaging

## 📞 Support

For issues, questions, or contributions:
1. Check the documentation files above
2. Review example strategies
3. Test on testnet first
4. Use `--dry-run` mode for debugging

## 🎓 Learning Path

1. **Beginner**: Use the RandomStrategy to understand the framework
2. **Intermediate**: Create a simple MA crossover strategy
3. **Advanced**: Implement multi-indicator strategies with risk management
4. **Expert**: Build strategy optimization and backtesting systems

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-25  
**Environment**: Testnet/Production  
**Language**: Python 3.8+
