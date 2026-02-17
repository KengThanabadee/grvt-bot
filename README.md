# GRVT Bot (API-Only, Production-Oriented)

Trading bot for GRVT perpetual markets with:
- minute-aligned runtime loop,
- fail-closed risk gates,
- startup reconciliation,
- adaptive reduce-only close execution based on orderbook liquidity.

This repository is intended for API-only operation (no web UI dependency during runtime).

## Quick Start

1. Install dependencies

```bash
pip install -e .
pip install pandas ta
```

2. Prepare config

```bash
cp config/config.example.yaml config/config.yaml
```

3. Run dry-run first

```bash
grvt-bot --config config/config.yaml --dry-run
```

4. Run strategy

```bash
grvt-bot --config config/config.yaml
```

5. Optional: run random strategy explicitly

```bash
grvt-bot --config config/config.yaml --strategy random --dry-run
```

## Runtime Behavior (Current)

- Loop cadence follows `trading.loop_interval` in minutes and aligns to second `00`.
- Bot waits `ops.data_close_buffer_seconds` after boundary before candle fetch.
- Startup reconcile policy uses `ops.startup_mismatch_policy`:
  - `adopt_continue`
  - `halt_only`
  - `auto_flatten_halt`
- Exit and flatten use adaptive reduce-only close logic from orderbook depth.
- Infinite retry is prevented by execution stop guards (retry cap, duration cap, no-progress cap).

## Core Docs

- `RUNBOOK.md`: operator runbook for startup, live operation, and incident handling.
- `CONFIG_REFERENCE.md`: full config key reference with defaults and notes.
- `OPERATIONS_CHECKLIST.md`: pre-live, live, and post-run checklists.
- `PAXG_STRATEGY_DOCS.md`: strategy-specific notes.

## Testing Commands

```bash
python -m grvt_bot.cli.main --help
python -m flake8 grvt_bot tests --select=E9,F63,F7,F82 --jobs=1
python -m mypy --ignore-missing-imports --follow-imports=skip grvt_bot/cli/main.py
pytest --collect-only -q
pytest -q
RUN_LIVE_TESTS=1 pytest --collect-only -q -m integration
```

## Safety Notes

- Do not commit real credentials.
- Keep `risk.fail_closed=true` for production.
- Start with low `risk.risk_per_trade_pct` and single symbol canary.
- If close flow reports repeated `CLOSE_*` failures, halt and investigate before resuming.
