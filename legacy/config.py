
# Configuration for GRVT Demo Bot

# Environment: "testnet" or "prod"
GRVT_ENV = "testnet"

# Credentials
# Replace these with your actual keys
GRVT_API_KEY = "38e9GlBoO80I8qqqBzJrVuladPo"
GRVT_PRIVATE_KEY = "0x9f3cd80ad997582a2f52dbbf2e91c7adda9ee466d3df8f2b36abeb630ea3a176"
GRVT_TRADING_ACCOUNT_ID = "2874699003423238"
GRVT_SUB_ACCOUNT_ID = "0" # Default sub-account ID

# Trading Settings
SYMBOL = "BTC_USDT_Perp"
LEVERAGE = 10
ORDER_SIZE_USDT = 500 # Size in USDT to trade per signal (meets minimum notional requirement)
MAIN_LOOP_INTERVAL = 60 # Seconds to sleep in the main loop
