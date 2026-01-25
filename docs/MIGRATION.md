# Migration Guide: Script-based → Modular Package

This guide helps you migrate from the old script-based structure to the new modular package structure.

## What Changed?

### Old Structure (Script-based)
```
grvt_demo_bot/
├── main.py
├── execution.py
├── trading_logic.py
├── config.py
├── check_leverage.py
└── requirements.txt
```

### New Structure (Modular Package)
```
grvt_demo_bot/
├── grvt_bot/              # ← Main package
│   ├── core/
│   ├── strategies/
│   ├── utils/
│   └── cli/
├── config/                # ← Config files
├── scripts/               # ← Helper scripts
├── docs/                  # ← Documentation
├── setup.py              # ← Package setup
└── pyproject.toml        # ← Modern packaging
```

---

## Breaking Changes

### 1. Import Paths

**Old:**
```python
from execution import GRVTExecutor
from trading_logic import TradingLogic
import config
```

**New:**
```python
from grvt_bot.core import GRVTExecutor
from grvt_bot.strategies import RandomStrategy
from grvt_bot.core.config import ConfigManager
```

### 2. Configuration

**Old:**
```python
# config.py
GRVT_ENV = "testnet"
GRVT_API_KEY = "..."
SYMBOL = "BTC_USDT_Perp"
```

**New:**
```yaml
# config/config.yaml
grvt:
  env: "testnet"
  api_key: "..."
trading:
  symbol: "BTC_USDT_Perp"
```

```python
# In code
from grvt_bot.core.config import ConfigManager
config = ConfigManager(config_path="config/config.yaml")
```

### 3. Executor Initialization

**Old:**
```python
executor = GRVTExecutor()  # Uses global config
```

**New:**
```python
config = ConfigManager(config_path="config/config.yaml")
logger = setup_logger("my_bot")
executor = GRVTExecutor(config, logger)
```

### 4. Strategy Implementation

**Old:**
```python
class TradingLogic:
    def get_signal(self):
        # Return signal dict
        pass
```

**New:**
```python
from grvt_bot.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def get_signal(self):
        # Return signal dict
        pass
```

---

## Step-by-Step Migration

### For Users (Running the Bot)

#### Option 1: Use CLI (Easiest)

1. **Install the package:**
   ```bash
   cd grvt_demo_bot
   pip install -e .
   ```

2. **Create config file:**
   ```bash
   cp config/config.example.yaml config/config.yaml
   # Edit config.yaml with your credentials
   ```

3. **Run the bot:**
   ```bash
   grvt-bot --config config/config.yaml
   ```

#### Option 2: Use Python Script

1. **Update your script:**
   ```python
   # old_main.py → new_main.py
   
   from grvt_bot.core.executor import GRVTExecutor
   from grvt_bot.core.config import ConfigManager
   from grvt_bot.strategies.random_strategy import RandomStrategy
   from grvt_bot.utils.logger import setup_logger
   import time
   
   # Setup
   logger = setup_logger("my_bot")
   config = ConfigManager(config_path="config/config.yaml")
   
   # Initialize
   executor = GRVTExecutor(config, logger)
   strategy = RandomStrategy(config, logger)
   strategy.initialize()
   
   # Main loop
   while True:
       signal = strategy.get_signal()
       if signal:
           price = executor.get_market_price(config.SYMBOL)
           amount = signal['amount_usdt'] / price
           executor.place_market_order(
               config.SYMBOL,
               signal['side'],
               round(amount, 3)
           )
       time.sleep(config.MAIN_LOOP_INTERVAL)
   ```

### For Developers (Custom Strategies)

#### Migrate Your Strategy

**Old `my_strategy.py`:**
```python
import config

class MyStrategy:
    def __init__(self):
        self.interval = config.MAIN_LOOP_INTERVAL
    
    def get_signal(self):
        # Your logic
        if self.should_buy():
            return {'side': 'buy', 'amount_usdt': config.ORDER_SIZE_USDT}
        return None
```

**New `my_strategy.py`:**
```python
from grvt_bot.strategies.base import BaseStrategy
from typing import Optional, Dict, Any

class MyStrategy(BaseStrategy):
    def __init__(self, config, logger=None):
        super().__init__(config, logger)
        self.interval = config.MAIN_LOOP_INTERVAL
    
    def get_signal(self) -> Optional[Dict[str, Any]]:
        # Your logic
        if self.should_buy():
            return {
                'side': 'buy',
                'amount_usdt': self.config.ORDER_SIZE_USDT,
                'reason': 'My strategy signal'
            }
        return None
    
    def initialize(self):
        super().initialize()
        self.logger.info("MyStrategy initialized")
```

**Usage:**
```python
from grvt_bot.core.config import ConfigManager
from grvt_bot.utils.logger import setup_logger
from my_strategy import MyStrategy

config = ConfigManager(config_path="config/config.yaml")
logger = setup_logger("strategy_bot")
strategy = MyStrategy(config, logger)
```

---

## Configuration Migration

### From Python config.py to YAML

**Old `config.py`:**
```python
GRVT_ENV = "testnet"
GRVT_API_KEY = "abc123"
GRVT_PRIVATE_KEY = "0x..."
GRVT_TRADING_ACCOUNT_ID = "12345"
GRVT_SUB_ACCOUNT_ID = "0"

SYMBOL = "BTC_USDT_Perp"
LEVERAGE = 10
ORDER_SIZE_USDT = 500
MAIN_LOOP_INTERVAL = 60
```

**New `config/config.yaml`:**
```yaml
grvt:
  env: "testnet"
  api_key: "abc123"
  private_key: "0x..."
  trading_account_id: "12345"
  sub_account_id: "0"

trading:
  symbol: "BTC_USDT_Perp"
  leverage: 10
  order_size_usdt: 500
  loop_interval: 60
```

### Backward Compatibility

If you want to keep using Python dict config:

```python
from grvt_bot.core.config import ConfigManager

# Old style with dict
config_dict = {
    'grvt': {
        'env': 'testnet',
        'api_key': 'abc123',
        # ...
    },
    'trading': {
        'symbol': 'BTC_USDT_Perp',
        # ...
    }
}

config = ConfigManager(config_dict=config_dict)
```

---

## Testing Migration

### Update Test Imports

**Old `test_execution.py`:**
```python
from execution import GRVTExecutor
import config

def test_executor():
    executor = GRVTExecutor()
    assert executor.client is not None
```

**New `test_executor.py`:**
```python
from grvt_bot.core.executor import GRVTExecutor
from grvt_bot.core.config import ConfigManager

def test_executor():
    config = ConfigManager(config_path="config/config.yaml")
    executor = GRVTExecutor(config)
    assert executor.client is not None
```

---

## Common Issues

### Issue 1: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'grvt_bot'
```

**Solution:**
```bash
# Make sure you're in the project root
cd grvt_demo_bot

# Install in development mode
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/grvt_demo_bot"
```

### Issue 2: Config File Not Found

```
FileNotFoundError: Config file not found: config/config.yaml
```

**Solution:**
```bash
# Create config from example
cp config/config.example.yaml config/config.yaml

# Or use absolute path
grvt-bot --config /full/path/to/config.yaml
```

### Issue 3: Import eth_account Error

```
ModuleNotFoundError: No module named 'eth_account'
```

**Solution:**
```bash
# Install requirements
pip install -r requirements.txt
```

---

## File Mapping Reference

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `main.py` | `grvt_bot/cli/main.py` | Now has CLI args |
| `execution.py` | `grvt_bot/core/executor.py` | Config-based init |
| `trading_logic.py` | `grvt_bot/strategies/random_strategy.py` | Inherits BaseStrategy |
| `config.py` | `config/config.yaml` | YAML format |
| `check_leverage.py` | `scripts/check_leverage.py` | Moved to scripts/ |
| N/A | `grvt_bot/strategies/base.py` | New: Base class |
| N/A | `grvt_bot/utils/logger.py` | New: Logger setup |
| N/A | `grvt_bot/core/config.py` | New: Config manager |

---

## Benefits of Migration

✅ **Better Organization**: Clear separation of concerns  
✅ **Reusability**: Use as a library in other projects  
✅ **Extensibility**: Easy to add new strategies  
✅ **Professional**: Follows Python packaging standards  
✅ **Testability**: Easier to write and run tests  
✅ **Distribution**: Can be installed via pip  
✅ **CLI Support**: Run from command line with args  
✅ **Type Safety**: Better IDE support and type hints  

---

## Rollback (If Needed)

If you need to use the old structure temporarily:

1. The old files still exist in the root directory
2. They will work as before (but won't use new features)
3. Simply run `python main.py` with old `config.py`

However, we recommend migrating to the new structure for long-term use.

---

## Next Steps

1. ✅ Complete migration following this guide
2. ✅ Test on testnet
3. ✅ Create backup of old config
4. ✅ Update any external scripts that import the bot
5. ✅ Review [SKILL.md](SKILL.md) for new features
6. ✅ Consider implementing custom strategies

---

**Questions?** Check [docs/SKILL.md](SKILL.md) for detailed documentation.
