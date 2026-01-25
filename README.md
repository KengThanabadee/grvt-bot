# GRVT Bot - Modular Trading Package 🤖

<div align="center">

**Professional trading bot for GRVT Exchange (Testnet/Prod)**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples) • [Migration](#-migration-guide)

</div>

---

## 🎯 Features

- ✅ **Modular Package Structure** - Professional Python package architecture
- ✅ **YAML Configuration** - Secure, flexible config management
- ✅ **Extensible Strategies** - Plugin-based strategy system
- ✅ **CLI Interface** - Rich command-line with arguments
- ✅ **Pip Installable** - Install and use anywhere
- ✅ **Antigravity Skill** - Ready to use as AI agent skill
- ✅ **Comprehensive Docs** - Full API reference and examples

---

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to project
cd grvt_demo_bot

# Install in development mode
pip install -e .
```

### Configuration

```bash
# Create config from template
cp config/config.example.yaml config/config.yaml

# Edit with your credentials
nano config/config.yaml
```

### Run the Bot

```bash
# Run with default settings
grvt-bot

# Run with custom config
grvt-bot --config config/config.yaml

# Test mode (no real orders)
grvt-bot --dry-run

# See all options
grvt-bot --help
```

---

## 📦 Package Structure

```
grvt_bot/
├── core/               # Core functionality
│   ├── executor.py     # GRVT API interface
│   └── config.py       # Configuration manager
├── strategies/         # Trading strategies
│   ├── base.py         # Abstract base class
│   └── random_strategy.py  # Example strategy
├── utils/              # Utilities
│   └── logger.py       # Logging setup
└── cli/                # Command-line interface
    └── main.py         # Entry point
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SKILL.md](docs/SKILL.md) | Complete Antigravity skill documentation |
| [MIGRATION.md](docs/MIGRATION.md) | Migration guide from old structure |
| [PROJECT_OVERVIEW_TH.md](PROJECT_OVERVIEW_TH.md) | Thai documentation (ภาษาไทย) |
| [Walkthrough](C:\Users\ไพรัตน์\.gemini\antigravity\brain\37e968b9-2d39-4ad8-b7a9-992bd5717961\walkthrough.md) | Development walkthrough |

---

## 💻 Usage Examples

### As CLI Application

```bash
# Basic usage
grvt-bot --config config/config.yaml

# With options
grvt-bot --config config/config.yaml \
         --strategy random \
         --log-level INFO \
         --dry-run
```

### As Python Library

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

# Get signal and execute
signal = strategy.get_signal()
if signal:
    price = executor.get_market_price(config.SYMBOL)
    amount = signal['amount_usdt'] / price
    
    executor.place_market_order(
        symbol=config.SYMBOL,
        side=signal['side'],
        amount=amount
    )
```

### Custom Strategy

```python
from grvt_bot.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    """My custom trading strategy."""
    
    def get_signal(self):
        # Your strategy logic here
        if self.should_buy():
            return {
                'side': 'buy',
                'amount_usdt': 500,
                'reason': 'My signal detected'
            }
        return None
    
    def should_buy(self):
        # Implement your buy logic
        # Example: MA crossover, RSI, etc.
        pass
```

---

## 🔧 Configuration

### YAML Format (Recommended)

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

### Python Dict (Backward Compatible)

```python
config = ConfigManager(config_dict={
    'grvt': {
        'env': 'testnet',
        'api_key': 'xxx',
        # ...
    },
    'trading': {
        'symbol': 'BTC_USDT_Perp',
        # ...
    }
})
```

### Environment Variables

```bash
export GRVT_API_KEY="your_api_key"
export GRVT_PRIVATE_KEY="0x..."
export SYMBOL="BTC_USDT_Perp"

# Config manager auto-loads from env
config = ConfigManager()
```

---

## 🤖 Using Antigravity Workflows

**New to Antigravity workflows?** [Read the complete guide →](ANTIGRAVITY_GUIDE.md)

### Quick Start with Workflows

1. Open this folder in your editor (VS Code, etc.)
2. Open Antigravity chat panel
3. Type: `"Help me build a trading strategy"`
4. Follow the guided workflow!

**Available workflows:**
- **Trading Strategy Builder** - Step-by-step strategy creation

See [ANTIGRAVITY_GUIDE.md](ANTIGRAVITY_GUIDE.md) for detailed instructions.

---

## ⚠️ Important Notes

> **🔐 Security Warning**
> 
> Never commit your `config/config.yaml` to git! It contains sensitive credentials.
> The file is already in `.gitignore` for your protection.

> **⚡ Leverage Setting**
> 
> You **must** set leverage manually on GRVT web interface before running the bot.
> The API does not support setting leverage programmatically.

> **🧪 Always Test First**
> 
> - Use `env: "testnet"` in config for testing
> - Test with `--dry-run` flag first
> - Start with small order sizes
> - Only move to production after thorough testing

---

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=grvt_bot --cov-report=html
```

### Code Quality

```bash
# Format code
black grvt_bot/

# Lint
flake8 grvt_bot/

# Type check
mypy grvt_bot/
```

---

## 🔄 Migration Guide

Migrating from the old script-based structure?

See [docs/MIGRATION.md](docs/MIGRATION.md) for detailed instructions.

**Quick Summary:**

```python
# Old
from execution import GRVTExecutor
import config
executor = GRVTExecutor()

# New
from grvt_bot.core import GRVTExecutor
from grvt_bot.core.config import ConfigManager

config = ConfigManager(config_path="config/config.yaml")
executor = GRVTExecutor(config)
```

---

## 📊 API Reference

### GRVTExecutor

Main class for GRVT Exchange operations.

```python
executor = GRVTExecutor(config, logger)

# Get market price
price = executor.get_market_price("BTC_USDT_Perp")

# Place market order
order = executor.place_market_order(
    symbol="BTC_USDT_Perp",
    side="buy",  # or "sell"
    amount=0.001
)

# Place limit order
order = executor.place_limit_order(
    symbol="BTC_USDT_Perp",
    side="buy",
    amount=0.001,
    price=50000.0
)

# Get account balance
balance = executor.get_account_summary()

# Close all positions
executor.close_all_positions("BTC_USDT_Perp")
```

### BaseStrategy

Abstract base class for strategies.

```python
class MyStrategy(BaseStrategy):
    def get_signal(self):
        """Must implement this method."""
        return {'side': 'buy', 'amount_usdt': 500}
    
    def initialize(self):
        """Optional: Called before main loop."""
        pass
    
    def on_order_placed(self, order):
        """Optional: Called after order placed."""
        pass
```

### ConfigManager

Configuration management.

```python
config = ConfigManager(config_path="config/config.yaml")

# Access values
config.GRVT_API_KEY
config.SYMBOL
config.LEVERAGE
config.ORDER_SIZE_USDT

# Get with default
config.get('trading', 'symbol', default='BTC_USDT_Perp')

# Set value
config.set('trading', 'leverage', 5)
```

---

## 🎓 Learning Path

1. **Beginner**: Run the bot with RandomStrategy
2. **Intermediate**: Create a simple Moving Average strategy
3. **Advanced**: Implement multi-indicator strategies
4. **Expert**: Build backtesting and optimization systems

---

## 📞 Support & Resources

- 📖 **Documentation**: See [docs/SKILL.md](docs/SKILL.md)
- 🇹🇭 **Thai Docs**: See [PROJECT_OVERVIEW_TH.md](PROJECT_OVERVIEW_TH.md)
- 🔄 **Migration**: See [docs/MIGRATION.md](docs/MIGRATION.md)
- 🐛 **Issues**: Check documentation first
- 💡 **Examples**: See examples in SKILL.md

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- GRVT Exchange for API access
- Python community for excellent tools
- Contributors and testers

---

<div align="center">

**Built with ❤️ for automated trading**

Version 1.0.0 • 2026-01-25

</div>
