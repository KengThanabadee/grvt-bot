# GRVT Bot (API-Only, Operator-First)

GRVT Bot is an API-only trading runtime for GRVT perpetual markets with:
- minute-aligned scheduling,
- fail-closed risk gates,
- startup reconcile and persisted runtime state,
- adaptive reduce-only close execution.

## Quick Start

1. Install package and strategy dependencies.

```bash
pip install -e .
pip install pandas ta
```

2. Create runtime config.

```bash
cp config/config.example.yaml config/config.yaml
```

3. Fill credentials and environment in `config/config.yaml`.

4. Run dry-run first.

```bash
grvt-bot --config config/config.yaml --dry-run
```

5. Run live runtime.

```bash
grvt-bot --config config/config.yaml
```

## Runtime Defaults (Important)

- CLI default strategy is `PAXGMeanReversionStrategy`.
- `trading.loop_interval` is in **minutes**.
- Config default `trading.symbol` in code is `BTC_USDT_Perp`; for PAXG strategy rollout, explicitly set `trading.symbol: PAXG_USDT_Perp`.

## Environment Modes

| Mode | Key config | Use case |
|---|---|---|
| Testnet | `grvt.env: testnet` | development, validation, canary behavior checks |
| Production | `grvt.env: prod` | real-capital deployment |

## Active Documentation

- `docs/INDEX.md`: documentation map and reading paths.
- `RUNBOOK.md`: runtime operation and incident handling.
- `OPERATIONS_CHECKLIST.md`: pre-live/live/post-run checklists.
- `CONFIG_REFERENCE.md`: config keys and defaults.
- `PAXG_STRATEGY_DOCS.md`: strategy-specific behavior.
- `PROJECT_OVERVIEW_TH.md`: Thai operator guide.
- `docs/SKILL.md`: developer/integration usage.
- `docs/MIGRATION.md`: migration from legacy structure.

## Validation Commands

```bash
python -m grvt_bot.cli.main --help
python -m flake8 grvt_bot tests --select=E9,F63,F7,F82 --jobs=1
python -m mypy --ignore-missing-imports --follow-imports=skip grvt_bot/cli/main.py
pytest -q
```

## Safety Notes

- Keep `risk.fail_closed=true` in production.
- Start with lower `risk.risk_per_trade_pct` for first live sessions.
- If repeated close failures occur (`CLOSE_*`), halt and follow `RUNBOOK.md` recovery flow.
