# CONFIG REFERENCE

Source of truth: `grvt_bot/core/config.py`.

## Global Notes

- `trading.loop_interval` is in **minutes**.
- CLI default strategy is `PAXGMeanReversionStrategy`.
- Config default symbol in code is `BTC_USDT_Perp`; set symbol explicitly per strategy/session.

## grvt

| Key | Type | Default | Notes |
|---|---|---|---|
| `env` | string | `testnet` | `testnet` or `prod` |
| `api_key` | string | `""` | required for live API calls |
| `private_key` | string | `""` | required for signing |
| `trading_account_id` | string | `""` | required |
| `sub_account_id` | string | `"0"` | sub-account scope |

## trading

| Key | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | `BTC_USDT_Perp` | set intentionally for chosen strategy |
| `leverage` | int | `10` | sizing context and order args |
| `order_size_usdt` | int | `500` | fallback notional when signal amount missing |
| `loop_interval` | int | `1` | minutes, aligned to second `00` |

## risk

| Key | Type | Default | Notes |
|---|---|---|---|
| `active_track` | string | `normal` | selects threshold profile |
| `fail_closed` | bool | `true` | block entries on missing critical data |
| `kill_switch` | bool | `false` | immediate entry block |
| `threshold_action` | string | `flatten_halt` | action on threshold hit |
| `risk_per_trade_pct` | float | `0.25` | used for notional sizing |
| `min_notional_safety_factor` | float | `1.05` | applied in derived min-notional check |
| `tracks.normal.max_drawdown_pct` | float | `5.0` | threshold profile |
| `tracks.normal.profit_target_pct` | float | `5.0` | threshold profile |
| `tracks.low_vol.max_drawdown_pct` | float | `2.0` | threshold profile |
| `tracks.low_vol.profit_target_pct` | float | `2.0` | threshold profile |

### Entry Gate Notes

- `min_qty` uses exchange `min_size` metadata.
- derived min-notional formula:

`derived_min_notional = min_qty * reference_price * min_notional_safety_factor`

- reference price chain:
  - buy: best ask
  - sell: best bid
  - fallback: last/mark variants

## ops

| Key | Type | Default | Notes |
|---|---|---|---|
| `data_close_buffer_seconds` | int | `2` | wait after boundary before candle fetch |
| `state_file` | string | `state/runtime_state.json` | runtime persistence path |
| `lock_file` | string | `state/runtime.lock` | single-instance lock path |
| `halt_on_reconcile_mismatch` | bool | `true` | legacy fallback control |
| `startup_mismatch_policy` | string | `adopt_continue` | `adopt_continue` / `halt_only` / `auto_flatten_halt` |
| `error_backoff_seconds` | int | `2` | backoff after loop exception |
| `max_repeated_errors` | int | `20` | auto-exit threshold |
| `repeated_error_window_seconds` | int | `300` | repeated-error time window |

## execution

| Key | Type | Default | Notes |
|---|---|---|---|
| `close_mode` | string | `reduce_only_twap_slice` | adaptive close mode |
| `liquidity_usage_pct` | float | `0.20` | fraction of in-band liquidity per slice |
| `orderbook_levels` | int | `20` | orderbook depth sampled |
| `max_slippage_bps` | int | `20` | in-band liquidity threshold |
| `close_min_slice_qty` | float | `0.01` | minimum slice quantity |
| `close_retry_interval_seconds` | int | `2` | wait between close attempts |
| `close_max_retries` | int | `20` | hard retry cap |
| `close_max_duration_seconds` | int | `90` | hard duration cap |
| `close_no_progress_retries` | int | `3` | no-progress cap |
| `position_qty_tolerance` | float | `0.000001` | treated as fully closed tolerance |
| `fail_halt_on_close_failure` | bool | `true` | halt when close fails in managed exit path |

## alerts

| Key | Type | Default | Notes |
|---|---|---|---|
| `enabled` | bool | `true` | enable alert manager |
| `telegram_enabled` | bool | `false` | telegram delivery toggle |
| `telegram_bot_token` | string | `""` | telegram bot token |
| `telegram_chat_id` | string | `""` | telegram chat id |

## Environment Overrides

Supported environment overrides include:

- GRVT: `GRVT_ENV`, `GRVT_API_KEY`, `GRVT_PRIVATE_KEY`, `GRVT_TRADING_ACCOUNT_ID`, `GRVT_SUB_ACCOUNT_ID`
- Trading: `SYMBOL`, `LEVERAGE`, `ORDER_SIZE_USDT`, `MAIN_LOOP_INTERVAL`
- Risk: `RISK_ACTIVE_TRACK`, `RISK_FAIL_CLOSED`, `RISK_KILL_SWITCH`, `RISK_PER_TRADE_PCT`, `RISK_MIN_NOTIONAL_SAFETY_FACTOR`
- Ops: `OPS_DATA_CLOSE_BUFFER_SECONDS`, `OPS_STATE_FILE`, `OPS_LOCK_FILE`, `OPS_STARTUP_MISMATCH_POLICY`, `OPS_ERROR_BACKOFF_SECONDS`, `OPS_MAX_REPEATED_ERRORS`, `OPS_REPEATED_ERROR_WINDOW_SECONDS`
- Execution: `EXECUTION_CLOSE_MODE`, `EXECUTION_LIQUIDITY_USAGE_PCT`, `EXECUTION_ORDERBOOK_LEVELS`, `EXECUTION_MAX_SLIPPAGE_BPS`, `EXECUTION_CLOSE_MIN_SLICE_QTY`, `EXECUTION_CLOSE_RETRY_INTERVAL_SECONDS`, `EXECUTION_CLOSE_MAX_RETRIES`, `EXECUTION_CLOSE_MAX_DURATION_SECONDS`, `EXECUTION_CLOSE_NO_PROGRESS_RETRIES`, `EXECUTION_POSITION_QTY_TOLERANCE`, `EXECUTION_FAIL_HALT_ON_CLOSE_FAILURE`
- Alerts: `ALERTS_ENABLED`, `ALERTS_TELEGRAM_ENABLED`, `ALERTS_TELEGRAM_BOT_TOKEN`, `ALERTS_TELEGRAM_CHAT_ID`
