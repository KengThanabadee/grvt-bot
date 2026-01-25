---
name: Trading Strategy Builder for GRVT
description: Step-by-step guided workflow to build custom trading strategies with proper structure and validation
---

# 🎯 Trading Strategy Builder - Antigravity Skill

A comprehensive, step-by-step guided process to help students and traders build their own trading strategies for GRVT Exchange using a standardized framework.

## 📌 What This Skill Does

This skill provides a **structured workflow** to:

1. ✅ **Discover** what trading style suits you
2. ✅ **Define** your strategy logic in plain language  
3. ✅ **Generate** production-ready Python code
4. ✅ **Validate** and test your strategy
5. ✅ **Deploy** with confidence

**Problem Solved:** Eliminates inconsistency in strategy development. Every strategy built through this skill follows the same standard, making it repeatable, testable, and maintainable.

---

## 🎓 Target Audience

- **Students** learning algorithmic trading
- **Traders** wanting to automate their strategies
- **Developers** building trading bots systematically

---

## 📋 Prerequisites

Before starting:
- [ ] GRVT Bot package installed (`pip install -e .`)
- [ ] Basic understanding of trading concepts (buy/sell, indicators)
- [ ] GRVT testnet credentials (get from [grvt.io](https://testnet.grvt.io))
- [ ] Python 3.8+ installed

---

## 🚦 START HERE: Phase 0 - Check Existing Strategy

### AI Agent Instructions

**First, ask the user:**

> 💬 **"Do you already have a trading strategy defined?"**
>
> **A.** Yes, I have a strategy → Skip to **Phase 2** (Logic to Code Conversion)  
> **B.** No, I need help creating one → Continue to **Phase 1**  
> **C.** I have some ideas but not fully defined → Continue to **Phase 1**

**Based on answer:**
- If **A**: Jump directly to Phase 2
- If **B** or **C**: Proceed with Phase 1

---

## 🔍 Phase 1: Strategy Discovery

**Goal:** Understand what type of strategy the user wants to build.

### Step 1.1: Understand Trading Style

**AI Agent asks:**

> 💬 **"What trading style interests you?"**
>
> 1. **Trend Following** - เทรดตามเทรนด์ (Buy uptrend, Sell downtrend)
> 2. **Mean Reversion** - เทรดย้อนกลับ (Buy oversold, Sell overbought)  
> 3. **Breakout** - เทรดตอนทะลุแนวรับ/ต้าน
> 4. **Scalping** - เทรดระยะสั้นมาก (รวดเร็ว in/out)
> 5. **Other/Mixed** - ผสมหลายแบบ
>
> **Type the number or describe your style.**

**Record user answer:** `[User's chosen style]`

---

### Step 1.2: Platform & Constraints

**AI Agent explains GRVT requirements:**

> ℹ️ **GRVT Exchange Information**
>
> **Platform Details:**
> - **Type:** Crypto Perpetual Futures
> - **Available Pairs:** BTC_USDT_Perp, ETH_USDT_Perp, SOL_USDT_Perp, etc.
> - **Leverage:** 1x to 20x (⚠️ must be set manually on web interface)
> - **Minimum Order:** ~$500 USDT notional value
> - **Trading Hours:** 24/7
>
> **Technical Limits:**
> - API rate limits apply
> - Testnet available for practice
> - Position size limits per account tier

**AI Agent asks:**

> 💬 **"Based on this, let's configure your strategy:"**
>
> 1. **Which symbol?** (BTC_USDT_Perp recommended for beginners)
> 2. **What timeframe?** (1m, 5m, 15m, 1h, 4h, 1d)
> 3. **How much leverage?** (Recommend 2x-5x for beginners, max 20x)
> 4. **Order size?** (Minimum $500 USDT, recommend $500-$1000 for testing)

**Record answers:**
```
Symbol: [e.g., BTC_USDT_Perp]
Timeframe: [e.g., 5m]
Leverage: [e.g., 5x]
Order Size: [e.g., $500]
```

---

### Step 1.3: Indicator Selection

**AI Agent suggests based on style chosen:**

**For Trend Following:**
```
Common indicators:
- Moving Averages (SMA, EMA) - แนวโน้มราคา
- MACD - Momentum และ crossover
- ADX - ความแข็งแกร่งของเทรนด์
- Supertrend - เส้นเทรนด์อัตโนมัติ
```

**For Mean Reversion:**
```
Common indicators:
- RSI - Relative Strength Index (overbought/oversold)
- Bollinger Bands - ช่วงราคาปกติ
- Stochastic - Momentum oscillator
```

**For Breakout:**
```
Common indicators:
- Support/Resistance levels
- Volume - ปริมาณการซื้อขาย
- ATR - Average True Range (volatility)
- Donchian Channels
```

**AI Agent asks:**

> 💬 **"Which indicators would you like to use?"**
>
> You can choose 1-3 indicators. More isn't always better!
>
> **Examples:**
> - "MA 20 and MA 50" (simple crossover)
> - "RSI and Bollinger Bands" (oversold + band touch)
> - "MACD and Volume" (momentum + confirmation)

**Record indicators:** `[User's chosen indicators]`

---

### Step 1.4: Risk Tolerance

**AI Agent asks:**

> 💬 **"What is your risk tolerance?"**
>
> 1. **Conservative** - Small gains, small losses (1-2% per trade)
> 2. **Moderate** - Balanced risk/reward (2-5% per trade)
> 3. **Aggressive** - Higher risk, higher reward (5-10% per trade)
>
> **This affects:**
> - Stop loss percentage
> - Take profit targets
> - Position sizing

**Record risk level:** `[Conservative/Moderate/Aggressive]`

---

## ✍️ Phase 2: Logic Definition

**Goal:** Write the strategy logic in plain, detailed language.

**AI Agent guides:**

> 📝 **"Now let's define your strategy logic in detail."**
>
> I'll guide you through each part. Be as specific as possible!

---

### Step 2.1: Entry Conditions (BUY)

**AI Agent provides template:**

> 💬 **"Describe EXACTLY when you want to OPEN A BUY position:"**
>
> **Template:**
> ```
> I want to BUY when:
> 1. [Indicator A] does [specific action]
> 2. AND [Indicator B] does [specific action]  
> 3. AND [additional condition if any]
> ```
>
> **Example (MA Crossover):**
> ```
> I want to BUY when:
> 1. Short MA (20) crosses ABOVE Long MA (50)
> 2. AND RSI is below 70 (not overbought)
> 3. AND current price is above both MAs (strong confirmation)
> ```

**User writes:** 
```
[User's BUY logic written here]
```

**AI reviews and asks clarifying questions if needed:**
- "What exactly is 'crosses above'? (Previous candle below, current above?)"
- "Any time restrictions? (E.g., not during first hour of day)"
- "Minimum gap between signals? (E.g., wait 1 hour between trades)"

---

### Step 2.2: Entry Conditions (SELL)

**AI Agent asks:**

> 💬 **"Now describe when you want to OPEN A SELL position:"**
>
> **Template:**
> ```
> I want to SELL when:
> 1. [Indicator A] does [specific action]
> 2. AND [Indicator B] does [specific action]
> 3. AND [additional condition if any]
> ```

**User writes:**
```
[User's SELL logic written here]
```

---

### Step 2.3: Exit Conditions

**AI Agent guides:**

> 💬 **"How and when should we EXIT positions?"**

**2.3.1 Take Profit:**
```
When should we take profit?
Option 1: Fixed percentage (e.g., "Exit when +2% profit")
Option 2: Indicator-based (e.g., "Exit when RSI reaches 80")
Option 3: Trailing stop (e.g., "Trail 1% below highest price")

Your choice: [User describes]
```

**2.3.2 Stop Loss:**
```
Where should we cut losses?
Option 1: Fixed percentage (e.g., "Exit when -1% loss")
Option 2: ATR-based (e.g., "1.5x ATR below entry")
Option 3: Support/Resistance based

Your choice: [User describes]
```

**2.3.3 Time-based Exit (optional):**
```
Should we exit after a certain time?
e.g., "Close position after 4 hours regardless"

Your choice: [User describes or "No"]
```

---

### Step 2.4: Position Sizing

**AI Agent asks:**

> 💬 **"How much should we trade per signal?"**
>
> **Options:**
> 1. **Fixed Amount** - Same USDT amount every trade (e.g., $500)
> 2. **Percentage of Balance** - % of total portfolio (e.g., 10% of balance)
> 3. **Risk-Based** - Based on stop loss distance (risk $X per trade)
>
> **Recommendation for beginners:** Fixed amount of $500-$1000

**User choice:** `[User's position sizing method]`

---

### Step 2.5: Additional Rules (Optional)

**AI Agent asks:**

> 💬 **"Any additional rules or filters?"**
>
> Examples:
> - "Only trade during high volume hours"
> - "Avoid trading during news events"
> - "Maximum 3 open positions at once"
> - "Don't trade on weekends"
>
> **Your additional rules (if any):**

**User adds:** `[Any additional rules]`

---

### Step 2.6: Review & Confirm Logic

**AI Agent summarizes:**

> ✅ **"Let me confirm your strategy logic:"**
>
> **Entry (BUY):**
> - [Condition 1]
> - [Condition 2]
> - [Condition 3]
>
> **Entry (SELL):**
> - [Condition 1]
> - [Condition 2]
>
> **Exit:**
> - Take Profit: [TP logic]
> - Stop Loss: [SL logic]
>
> **Position Size:** [Size logic]
>
> **Additional Rules:** [Rules if any]
>
> **Is this correct? (Yes/No/Modify)**

**User confirms or requests changes.**

---

## 💻 Phase 3: Code Generation

**Goal:** Convert the defined logic into working Python code using the GRVT Bot framework.

### Step 3.1: Generate Strategy Class

**AI Agent does:**

> 🤖 **"Generating your custom strategy class..."**

**AI creates `[StrategyName]_strategy.py`:**

```python
"""
Custom Trading Strategy: [User's Strategy Name]

Generated by: Trading Strategy Builder Skill
Date: [Current Date]
Author: [User Name]

Strategy Description:
[Brief description based on user's inputs]

Entry Conditions:
- BUY: [User's buy logic]
- SELL: [User's sell logic]

Exit Conditions:
- Take Profit: [TP logic]
- Stop Loss: [SL logic]

Risk Parameters:
- Position Size: [Size]
- Risk Level: [Conservative/Moderate/Aggressive]
"""

from grvt_bot.strategies.base import BaseStrategy
from typing import Optional, Dict, Any
import logging


class CustomStrategy(BaseStrategy):
    """
    [Strategy Name] - [Brief description]
    """
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        
        # Strategy parameters (extracted from user inputs)
        self.timeframe = "[timeframe]"
        self.symbol = "[symbol]"
        
        # Indicator parameters
        self.short_ma_period = 20  # Adjust based on user's choice
        self.long_ma_period = 50
        self.rsi_period = 14
        
        # Risk management
        self.take_profit_pct = 2.0  # From user input
        self.stop_loss_pct = 1.0
        
        # Position tracking
        self.last_signal_time = 0
        self.min_signal_interval = 300  # 5 minutes
        
        # Data storage (in real implementation, fetch from exchange)
        self.price_data = []
        
        self.logger.info(f"Initialized {self.__class__.__name__}")
    
    def get_signal(self) -> Optional[Dict[str, Any]]:
        """
        Main method to generate trading signals.
        
        Returns:
            Signal dict with 'side', 'amount_usdt', 'confidence', 'reason'
            or None if no signal
        """
        # Check if enough time has passed since last signal
        import time
        current_time = time.time()
        if current_time - self.last_signal_time < self.min_signal_interval:
            return None
        
        # TODO: Fetch current market data
        # current_price = self.get_current_price()
        # self.update_price_data(current_price)
        
        # Check if we have enough data
        if not self._has_enough_data():
            self.logger.debug("Not enough data for indicators")
            return None
        
        # Calculate indicators
        indicators = self._calculate_indicators()
        
        # Check BUY signal
        if self._check_buy_conditions(indicators):
            self.last_signal_time = current_time
            return {
                'side': 'buy',
                'amount_usdt': self.config.ORDER_SIZE_USDT,
                'confidence': self._calculate_confidence(indicators, 'buy'),
                'reason': self._format_buy_reason(indicators)
            }
        
        # Check SELL signal
        if self._check_sell_conditions(indicators):
            self.last_signal_time = current_time
            return {
                'side': 'sell',
                'amount_usdt': self.config.ORDER_SIZE_USDT,
                'confidence': self._calculate_confidence(indicators, 'sell'),
                'reason': self._format_sell_reason(indicators)
            }
        
        return None
    
    def _calculate_indicators(self) -> Dict[str, float]:
        """
        Calculate all required technical indicators.
        
        Returns:
            Dictionary with calculated indicator values
        """
        # TODO: Implement indicator calculations based on user's chosen indicators
        # This is a template - actual implementation depends on user's choices
        
        indicators = {}
        
        # Example: Moving Averages (if user chose MAs)
        # if len(self.price_data) >= self.long_ma_period:
        #     indicators['short_ma'] = self._calculate_sma(self.short_ma_period)
        #     indicators['long_ma'] = self._calculate_sma(self.long_ma_period)
        
        # Example: RSI (if user chose RSI)
        # if len(self.price_data) >= self.rsi_period:
        #     indicators['rsi'] = self._calculate_rsi(self.rsi_period)
        
        return indicators
    
    def _check_buy_conditions(self, indicators: Dict[str, float]) -> bool:
        """
        Check if BUY entry conditions are met.
        
        Based on user's defined logic:
        [Insert user's BUY conditions here]
        """
        # TODO: Implement user's BUY logic
        # Example template:
        # return (
        #     indicators['short_ma'] > indicators['long_ma'] and  # MA crossover
        #     indicators['rsi'] < 70  # Not overbought
        # )
        return False  # Placeholder
    
    def _check_sell_conditions(self, indicators: Dict[str, float]) -> bool:
        """
        Check if SELL entry conditions are met.
        
        Based on user's defined logic:
        [Insert user's SELL conditions here]
        """
        # TODO: Implement user's SELL logic
        return False  # Placeholder
    
    def _calculate_confidence(self, indicators: Dict[str, float], side: str) -> float:
        """
        Calculate confidence score (0.0 to 1.0) for the signal.
        
        Higher confidence = stronger signal
        """
        # Simple confidence calculation based on indicators
        # Customize based on user's strategy
        confidence = 0.5  # Default moderate confidence
        
        # Adjust based on indicator strength
        # Example: if RSI is very oversold/overbought, higher confidence
        
        return min(max(confidence, 0.3), 0.9)
    
    def _format_buy_reason(self, indicators: Dict[str, float]) -> str:
        """Format human-readable reason for BUY signal."""
        # Create descriptive reason based on which conditions triggered
        return "BUY conditions met"  # Customize based on indicators
    
    def _format_sell_reason(self, indicators: Dict[str, float]) -> str:
        """Format human-readable reason for SELL signal."""
        return "SELL conditions met"  # Customize based on indicators
    
    def _has_enough_data(self) -> bool:
        """Check if we have enough historical data for indicators."""
        required_periods = max(self.long_ma_period, self.rsi_period)
        return len(self.price_data) >= required_periods
    
    # Helper methods for indicator calculations
    def _calculate_sma(self, period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(self.price_data) < period:
            return 0.0
        return sum(self.price_data[-period:]) / period
    
    def _calculate_rsi(self, period: int) -> float:
        """Calculate Relative Strength Index."""
        # RSI calculation implementation
        # (Use library like 'ta' or implement manually)
        pass
    
    def initialize(self) -> None:
        """Called before strategy starts."""
        super().initialize()
        self.logger.info(f"Strategy initialized with parameters:")
        self.logger.info(f"  - Symbol: {self.symbol}")
        self.logger.info(f"  - Timeframe: {self.timeframe}")
        self.logger.info(f"  - Take Profit: {self.take_profit_pct}%")
        self.logger.info(f"  - Stop Loss: {self.stop_loss_pct}%")
    
    def on_order_placed(self, order: Dict[str, Any]) -> None:
        """Called after order is placed."""
        super().on_order_placed(order)
        # TODO: Track position for TP/SL management
        
    def on_order_filled(self, order: Dict[str, Any]) -> None:
        """Called when order is filled."""
        super().on_order_filled(order)
        # TODO: Set TP/SL orders if needed
```

---

### Step 3.2: Generate Configuration File

**AI creates `custom_strategy_config.yaml`:**

```yaml
# Configuration for [Strategy Name]
# Generated by Trading Strategy Builder

grvt:
  # Exchange settings
  env: "testnet"  # Change to "prod" for live trading
  api_key: "your_api_key_here"
  private_key: "0xyour_private_key_here"
  trading_account_id: "your_account_id"
  sub_account_id: "0"

trading:
  # Trading parameters (from user input)
  symbol: "[BTC_USDT_Perp or user's choice]"
  leverage: [5 or user's choice]
  order_size_usdt: [500 or user's choice]
  loop_interval: 60  # Check for signals every 60 seconds

strategy:
  # Strategy-specific settings
  name: "CustomStrategy"
  timeframe: "[5m or user's choice]"
  
  # Indicators (customize based on user's choices)
  short_ma_period: 20
  long_ma_period: 50
  rsi_period: 14
  
  # Risk management (from user input)
  take_profit_percent: 2.0
  stop_loss_percent: 1.0
  
  # Position management
  max_positions: 1
  min_signal_interval: 300  # Seconds between signals
```

---

### Step 3.3: Generate Documentation

**AI creates `STRATEGY_DOCUMENTATION.md`:**

```markdown
# [Strategy Name] Documentation

**Generated:** [Date]  
**Author:** [User Name]  
**Framework:** GRVT Bot v1.0.0

## Strategy Overview

**Type:** [Trend Following/Mean Reversion/etc.]  
**Symbol:** [BTC_USDT_Perp]  
**Timeframe:** [5m]  
**Risk Level:** [Conservative/Moderate/Aggressive]

## Logic

### Entry Conditions

**BUY Signal:**
1. [Condition 1]
2. [Condition 2]
3. [Condition 3]

**SELL Signal:**
1. [Condition 1]
2. [Condition 2]

### Exit Conditions

- **Take Profit:** [X%]
- **Stop Loss:** [Y%]
- **Time Exit:** [If applicable]

## Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Symbol | [BTC_USDT_Perp] | Trading pair |
| Timeframe | [5m] | Candle interval |
| Leverage | [5x] | Position leverage |
| Order Size | [$500] | USDT per trade |
| Take Profit | [2%] | Profit target |
| Stop Loss | [1%] | Loss limit |

## Indicators Used

1. **[Indicator 1]** - [Purpose]
2. **[Indicator 2]** - [Purpose]

## Risk Management

- **Max Position Size:** $500 per trade
- **Risk per Trade:** ~1% of capital
- **Max Concurrent Positions:** 1

## Usage

```bash
# Run with dry-run (no real orders)
grvt-bot --config custom_strategy_config.yaml --dry-run

# Run live (testnet)
grvt-bot --config custom_strategy_config.yaml
```

## Test Results

(To be filled after backtesting)

## Notes

[Any additional notes or observations]
```

---

## ✅ Phase 4: Validation & Testing

**Goal:** Ensure the strategy code is correct and works as expected.

### Step 4.1: Code Syntax Check

**AI runs:**
```bash
python -m py_compile custom_strategy.py
```

**Result:** 
- ✅ No syntax errors → Continue
- ❌ Syntax errors → Fix and rerun

---

### Step 4.2: Import Test

**AI runs:**
```python
# Test if strategy can be imported
from custom_strategy import CustomStrategy
from grvt_bot.core.config import ConfigManager

config = ConfigManager(config_path="custom_strategy_config.yaml")
strategy = CustomStrategy(config)
print("✅ Strategy imported successfully")
```

---

### Step 4.3: Logic Validation Checklist

**AI asks user to confirm:**

> ✅ **Strategy Validation Checklist**
>
> Please confirm each item:
>
> - [ ] Entry logic clearly defined for both BUY and SELL
> - [ ] Exit conditions include both TP and SL
> - [ ] Position sizing is appropriate for your capital
> - [ ] Risk management parameters are set
> - [ ] No contradictory conditions (e.g., RSI > 70 AND RSI < 30)
> - [ ] Minimum wait time between signals is defined
> - [ ] Config file has all required credentials
> - [ ] Leverage is set correctly on GRVT web interface

**User confirms all items.**

---

### Step 4.4: Dry Run Test

**AI executes:**

```bash
grvt-bot --config custom_strategy_config.yaml --strategy custom_strategy --dry-run --log-level DEBUG
```

**Expected output:**
```
2026-01-25 13:00:00 - grvt_bot - INFO - ✓ Bot initialized successfully!
2026-01-25 13:00:00 - CustomStrategy - INFO - Strategy initialized
2026-01-25 13:00:05 - CustomStrategy - DEBUG - Checking for signals...
2026-01-25 13:00:05 - CustomStrategy - INFO - No signal at this time
...
```

**AI reviews output and confirms:**
- ✅ No errors
- ✅ Strategy initializes correctly
- ✅ Signal checking works

---

### Step 4.5: Unit Test (Optional but Recommended)

**AI generates test file `test_custom_strategy.py`:**

```python
import pytest
from custom_strategy import CustomStrategy
from grvt_bot.core.config import ConfigManager


def test_strategy_initialization():
    """Test strategy initializes without errors."""
    config = ConfigManager(config_dict={
        'trading': {'order_size_usdt': 500, 'symbol': 'BTC_USDT_Perp'}
    })
    strategy = CustomStrategy(config)
    assert strategy is not None
    assert strategy.config is not None


def test_signal_generation():
    """Test signal generation doesn't crash."""
    config = ConfigManager(config_dict={
        'trading': {'order_size_usdt': 500}
    })
    strategy = CustomStrategy(config)
    
    # Should return None or valid signal
    signal = strategy.get_signal()
    
    if signal:
        assert 'side' in signal
        assert signal['side'] in ['buy', 'sell']
        assert 'amount_usdt' in signal
        assert signal['amount_usdt'] > 0


def test_buy_conditions():
    """Test BUY condition logic."""
    # Add specific tests for your BUY logic
    pass


def test_sell_conditions():
    """Test SELL condition logic."""
    # Add specific tests for your SELL logic
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Run tests:**
```bash
pytest test_custom_strategy.py -v
```

---

## 🎊 Phase 5: Deployment Guide

**Goal:** Guide user to deploy their strategy safely.

### Step 5.1: Testnet Deployment

**AI provides step-by-step guide:**

> 🚀 **Deploying to GRVT Testnet**
>
> **Step 1:** Get testnet credentials
> ```
> 1. Go to https://testnet.grvt.io
> 2. Create account
> 3. Get API key and private key
> 4. Get some testnet USDT (from faucet)
> ```
>
> **Step 2:** Update config file
> ```yaml
> grvt:
>   env: "testnet"  # ← Make sure it's testnet
>   api_key: "your_real_testnet_key"
>   private_key: "0x..."
>   trading_account_id: "your_account"
> ```
>
> **Step 3:** Set leverage on web interface
> ```
> ⚠️ IMPORTANT: Go to GRVT website and manually set leverage to [X]x
> The bot cannot set leverage via API!
> ```
>
> **Step 4:** Start with small amount
> ```yaml
> trading:
>   order_size_usdt: 500  # Start small!
> ```
>
> **Step 5:** Run with monitoring
> ```bash
> grvt-bot --config custom_strategy_config.yaml --log-level INFO
> ```
>
> **Step 6:** Monitor for at least 24-48 hours
> - Watch the logs
> - Check if signals are generated
> - Verify orders are placed correctly
> - Monitor P&L

---

### Step 5.2: Performance Tracking

**AI suggests:**

> 📊 **Track Your Strategy Performance**
>
> Create a simple tracking spreadsheet:
>
> | Date | Time | Signal | Entry Price | Exit Price | P&L | Notes |
> |------|------|--------|-------------|------------|-----|-------|
> | ... | ... | BUY | 50000 | 51000 | +$50 | MA cross worked |
>
> **Metrics to watch:**
> - Win rate (% of profitable trades)
> - Average profit per trade
> - Maximum drawdown
> - Sharpe ratio (if you know how)

---

### Step 5.3: Production Deployment (Advanced)

> ⚠️ **Before Going to Production:**
>
> - [ ] Tested on testnet for at least 1-2 weeks
> - [ ] Win rate is acceptable (>50% ideally)
> - [ ] Risk management is working correctly
> - [ ] You can afford to lose the trading capital
> - [ ] You understand this is HIGH RISK
>
> **To deploy to production:**
> ```yaml
> grvt:
>   env: "prod"  # ← Change to prod
>   api_key: "prod_api_key"
>   private_key: "0xprod_private_key"
> ```
>
> **Start with VERY small amounts!**

---

## 📚 Additional Resources

### Templates Available

1. **Trend Following Template** - MA Crossover with ADX filter
2. **Mean Reversion Template** - RSI + Bollinger Bands
3. **Breakout Template** - Donchian Channel breakout

### Example Strategies

See `examples/` folder:
- `ma_crossover_strategy.py` - Simple MA crossover
- `rsi_bb_strategy.py` - RSI + Bollinger Bands mean reversion
- `macd_volume_strategy.py` - MACD with volume confirmation

### Learn More

- [GRVT API Documentation](https://docs.grvt.io)
- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)
- [Base Strategy API Reference](../docs/SKILL.md#basestrategy)

---

## ⚠️ Important Warnings

> **Risk Disclaimer:**
>
> - Trading involves significant risk of loss
> - Never trade with money you can't afford to lose
> - Past performance does not guarantee future results
> - Start with testnet and small amounts
> - This tool is for educational purposes
> - The creator is not responsible for your trading losses

> **Technical Warnings:**
>
> - Always test on testnet first
> - Monitor your bot regularly
> - Have stop-loss in place
> - Don't leave bot running unattended initially
> - Check logs frequently
> - Be prepared to manually intervene

---

## 🔄 Iteration & Improvement

**After running your strategy:**

1. **Analyze Results** - What worked? What didn't?
2. **Adjust Parameters** - Fine-tune your indicators
3. **Add Filters** - Reduce false signals
4. **Backtest Changes** - Test improvements on historical data
5. **Repeat Process** - Continuous improvement

**To modify your strategy:**
- Update the logic in `custom_strategy.py`
- Adjust parameters in `custom_strategy_config.yaml`
- Re-run validation (Phase 4)
- Test on testnet again

---

## 📞 Support

If you encounter issues:

1. Check logs in `grvt_bot.log`
2. Review [docs/MIGRATION.md](../docs/MIGRATION.md)
3. Verify all prerequisites are met
4. Check GRVT API status
5. Test with `--dry-run` mode first

---

## ✅ Success Checklist

Before considering your strategy complete:

- [ ] Strategy logic is clearly documented
- [ ] All entry/exit conditions are coded
- [ ] Risk management is in place
- [ ] Code passes all validation checks
- [ ] Tested in dry-run mode
- [ ] Tested on testnet with real API
- [ ] Performance tracked for at least 1 week
- [ ] You understand how and why it trades
- [ ] You can explain the strategy to someone else
- [ ] Emergency stop procedure is clear

---

**Congratulations! 🎉**

You've built a complete, production-ready trading strategy using a standardized framework!

---

**Version:** 1.0.0  
**Last Updated:** 2026-01-25  
**Compatible With:** grvt-bot v1.0.0+  
**Skill Type:** Guided Workflow
