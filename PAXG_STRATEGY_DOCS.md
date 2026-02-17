# PAXG Mean Reversion Strategy

This document explains runtime behavior of `PAXGMeanReversionStrategy`.

## 1. Summary

- Strategy class: `PAXGMeanReversionStrategy`
- Entry style: Bollinger-band mean reversion
- Exit style: middle-band reversion
- Runtime mode: API-only (no web UI dependency)

## 2. Dependencies and Runtime Assumptions

Required Python packages:
- `pandas`
- `ta`

Assumptions:
- Strategy receives OHLCV updates from runtime (`update_market_data`).
- Runtime handles risk gating, state persistence, and close execution.

## 3. Strategy Parameters (from `strategy` config section)

- `timeframe` (default `15m`)
- `symbol` (fallback from `config.SYMBOL`, final fallback `PAXG_USDT_Perp`)
- `bb_window` (default `20`)
- `bb_std` (default `2.0`)
- `atr_window` (default `14`)
- `sl_atr_multiplier` (default `1.5`)
- `capital` (default `100000.0`)
- `risk_per_trade_pct` (default `0.25`)

## 4. Entry Logic

Entry uses previous candle position vs Bollinger bands:

- Buy condition: previous close < previous lower band
- Sell condition: previous close > previous upper band

Signal payload includes:
- `side`
- `amount_usdt`
- `sl_price`
- `tp_price` (middle band)
- `reason`

## 5. Exit Logic

Dynamic exit via `check_exit`:

- Long closes when price touches/reaches middle band
- Short closes when price touches/reaches middle band

Returned signal includes `action: close` and close side.

## 6. Position Sizing in Strategy

Strategy computes local risk amount:

`risk_amount = capital * (risk_per_trade_pct / 100)`

Then:

`position_units = risk_amount / (ATR * sl_atr_multiplier)`

`amount_usdt = position_units * entry_price`

Runtime still applies its own risk gates and exchange min-threshold checks before sending orders.

## 7. Runtime Integration (Important)

Runtime (`grvt_bot/cli/main.py`) is responsible for:
- schedule and candle freshness checks,
- startup reconcile and persisted state,
- threshold/kill-switch controls,
- adaptive reduce-only close execution.

Strategy is not a standalone execution engine.

## 8. Recommended Config for Initial Rollout

```yaml
trading:
  symbol: "PAXG_USDT_Perp"
  leverage: 3
  loop_interval: 1

risk:
  fail_closed: true
  risk_per_trade_pct: 0.10

ops:
  startup_mismatch_policy: "halt_only"

execution:
  fail_halt_on_close_failure: true
```

## 9. Limitations / Notes

- Strategy quality depends on OHLCV quality and timely updates.
- Default config symbol in code is `BTC_USDT_Perp`; set `trading.symbol` explicitly for PAXG sessions.
- In thin liquidity, close flow can stop with `CLOSE_NO_PROGRESS` or `CLOSE_TIMEOUT`; follow runbook incident flow.

## 10. Commands

```bash
grvt-bot --config config/config.yaml --dry-run
grvt-bot --config config/config.yaml --strategy PAXGMeanReversionStrategy
```
