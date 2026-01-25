# GRVT Demo Bot

A standalone example of a trading bot for the GRVT exchange (Testnet/Prod). This bot demonstrates how to connect, authenticate, generate signals, and execute trades using a local copy of the GRVT Python SDK.

## Project Structure

- **`main.py`**: The entry point of the application. It runs the main loop which fetches signals and executes orders.
- **`config.py`**: Configuration file for credentials (API Key, Private Key, Account IDs) and trading settings (Symbol, Leverage, Order Size).
- **`execution.py`**: Handles the connection to GRVT, authentication, and order placement. It wraps the `pysdk` interactions.
- **`trading_logic.py`**: Contains the strategy logic. Currently implements a simple random signal generator for demonstration purposes.
- **`requirements.txt`**: List of Python dependencies required to run the bot.
- **`pysdk/`**: A local copy of the GRVT Python SDK, ensuring the bot is self-contained.

## Setup

1.  **Prerequisites**: Ensure you have Python 3.8+ installed.

2.  **Install Dependencies**:
    Navigate to this directory and install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    Open `config.py` and strictly follow the comments to input your GRVT credentials.
    ```python
    # Example config.py
    GRVT_ENV = "testnet" # "testnet" or "prod"
    GRVT_API_KEY = "your_real_api_key"
    GRVT_PRIVATE_KEY = "your_real_private_key"
    # ...
    ```

## Running the Bot

To start the bot, simply run the `main.py` script:

```bash
python main.py
```

The bot will:
1. Initialize the connection to GRVT.
2. Enter a loop checking for signals every second.
3. When a signal is generated (randomly in this demo), it will place a market order on the configured symbol.
4. Logs will be printed to the console and saved to `grvt_bot.log`.

## Customization

- **Change Trading Strategy**: Modify `trading_logic.py` to implement your own trading algorithms (e.g., MA crossover, RSI).
- **Change Execution**: Modify `execution.py` if you need advanced order types (Limit, Stop Loss, etc.) or different margin management.

## Testing

I have included a `tests` folder with integration tests that use your real API credentials to verify functionality.

**WARNING**: These tests will execute REAL orders on the environment specified in `config.py`. Use `testnet` environment to avoid losing real funds.

To run the tests:
```bash
pytest grvt_demo_bot/tests
```

