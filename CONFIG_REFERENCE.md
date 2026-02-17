# CONFIG REFERENCE

Reference for `config/config.yaml`.

## grvt

- `env` (`testnet` | `prod`)
- `api_key`
- `private_key`
- `trading_account_id`
- `sub_account_id` (default `0`)

## trading

- `symbol`: market symbol (example `PAXG_USDT_Perp`)
- `leverage`: intended leverage for sizing context
- `order_size_usdt`: compatibility fallback if strategy amount is absent
- `loop_interval`: loop cadence in minutes; runtime aligns to second `00`

## risk

- `active_track`: `normal` | `low_vol`
- `fail_closed`: block on missing critical data
- `kill_switch`: blocks new entry when `true`
- `threshold_action`: expected `flatten_halt`
- `risk_per_trade_pct`: notional budget = equity * pct * leverage
- `min_notional_safety_factor`: used for derived min notional check
- `tracks.normal.max_drawdown_pct`
- `tracks.normal.profit_target_pct`
- `tracks.low_vol.max_drawdown_pct`
- `tracks.low_vol.profit_target_pct`

### Entry gate notes

- `min_qty` comes from exchange metadata (`min_size`).
- derived min notional:

`derived_min_notional = min_qty * reference_price * min_notional_safety_factor`

- Reference price chain:
  - buy: best ask
  - sell: best bid
  - fallback: last/mark variants

## ops

- `data_close_buffer_seconds` (default `2`)
- `state_file` (default `state/runtime_state.json`)
- `lock_file` (default `state/runtime.lock`)
- `halt_on_reconcile_mismatch` (legacy fallback signal)
- `startup_mismatch_policy`:
  - `adopt_continue`
  - `halt_only`
  - `auto_flatten_halt`
- `error_backoff_seconds`
- `max_repeated_errors`
- `repeated_error_window_seconds`

## execution

- `close_mode`: expected `reduce_only_twap_slice`
- `liquidity_usage_pct`: fraction of available in-band liquidity per slice
- `orderbook_levels`: orderbook depth levels to read
- `max_slippage_bps`: in-band liquidity filter threshold
- `close_min_slice_qty`: lower bound per slice
- `close_retry_interval_seconds`: wait between retries
- `close_max_retries`: hard retry cap
- `close_max_duration_seconds`: hard time cap
- `close_no_progress_retries`: cap for repeated no-progress attempts
- `position_qty_tolerance`: qty tolerance for "fully closed"
- `fail_halt_on_close_failure`: halt after close failure in exit path

## alerts

- `enabled`
- `telegram_enabled`
- `telegram_bot_token`
- `telegram_chat_id`

## Environment Variable Overrides

Selected supported env overrides include:

- `GRVT_ENV`, `GRVT_API_KEY`, `GRVT_PRIVATE_KEY`, `GRVT_TRADING_ACCOUNT_ID`, `GRVT_SUB_ACCOUNT_ID`
- `SYMBOL`, `LEVERAGE`, `ORDER_SIZE_USDT`, `MAIN_LOOP_INTERVAL`
- `RISK_ACTIVE_TRACK`, `RISK_FAIL_CLOSED`, `RISK_KILL_SWITCH`, `RISK_PER_TRADE_PCT`, `RISK_MIN_NOTIONAL_SAFETY_FACTOR`
- `OPS_DATA_CLOSE_BUFFER_SECONDS`, `OPS_STATE_FILE`, `OPS_LOCK_FILE`, `OPS_STARTUP_MISMATCH_POLICY`
- `OPS_ERROR_BACKOFF_SECONDS`, `OPS_MAX_REPEATED_ERRORS`, `OPS_REPEATED_ERROR_WINDOW_SECONDS`
- `EXECUTION_CLOSE_MODE`, `EXECUTION_LIQUIDITY_USAGE_PCT`, `EXECUTION_ORDERBOOK_LEVELS`, `EXECUTION_MAX_SLIPPAGE_BPS`
- `EXECUTION_CLOSE_MIN_SLICE_QTY`, `EXECUTION_CLOSE_RETRY_INTERVAL_SECONDS`
- `EXECUTION_CLOSE_MAX_RETRIES`, `EXECUTION_CLOSE_MAX_DURATION_SECONDS`
- `EXECUTION_CLOSE_NO_PROGRESS_RETRIES`, `EXECUTION_POSITION_QTY_TOLERANCE`
- `EXECUTION_FAIL_HALT_ON_CLOSE_FAILURE`
- `ALERTS_ENABLED`, `ALERTS_TELEGRAM_ENABLED`, `ALERTS_TELEGRAM_BOT_TOKEN`, `ALERTS_TELEGRAM_CHAT_ID`
