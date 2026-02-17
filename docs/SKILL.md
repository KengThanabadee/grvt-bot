---
name: GRVT Bot
summary: API-only GRVT trading runtime with operator-first controls and strategy integration.
---

# GRVT Bot Skill Reference

This document explains how to use the project as a reusable runtime/skill in development workflows.

## 1. What This Provides

- API-only execution runtime (`grvt_bot/cli/main.py`)
- Config manager with YAML + env override (`grvt_bot/core/config.py`)
- Risk gates and threshold logic (`grvt_bot/core/risk.py`)
- Persistent state and startup reconcile (`grvt_bot/core/state.py`)
- Adaptive reduce-only close execution (`grvt_bot/core/executor.py`)
- Strategy interface and implementations (`grvt_bot/strategies/`)

## 2. Package Layout

```text
grvt_bot/
  cli/
  core/
  strategies/
  utils/
```

## 3. Install and Validate

```bash
pip install -e .
pip install pandas ta
python -m grvt_bot.cli.main --help
```

## 4. CLI Commands

| Command | Purpose |
|---|---|
| `grvt-bot --config config/config.yaml` | start runtime |
| `grvt-bot --config config/config.yaml --dry-run` | dry-run validation |
| `grvt-bot --strategy random --dry-run` | random strategy smoke run |
| `grvt-bot --log-level DEBUG` | debug logging |

Notes:
- default strategy is `PAXGMeanReversionStrategy`
- config path default is `config/config.yaml`

## 5. Config Model

Primary config domains:
- `grvt`
- `trading`
- `risk`
- `ops`
- `execution`
- `alerts`

See `CONFIG_REFERENCE.md` for full key list and defaults.

## 6. Runtime Integration Pattern

Typical integration flow:
1. load config
2. initialize executor + strategy
3. run minute-aligned loop
4. apply risk gate before entry
5. persist state and reconcile on startup

## 7. Strategy Extension Contract

Create custom strategy by extending `BaseStrategy` and implementing:
- `get_signal()` (required)
- `initialize()` (optional)
- `on_error()` (optional)
- `check_exit()` (optional but recommended)

Signal contract (runtime expects):
- `side`: buy/sell (or long/short, normalized)
- `amount_usdt`: optional
- `reason`: optional
- `sl_price`, `tp_price`: optional

## 8. Operational Expectations

- Use `risk.fail_closed=true` in production.
- Use dry-run before live sessions.
- Handle `CLOSE_*` failure codes using `RUNBOOK.md`.
- Keep one runtime process only (lock file enforced).

## 9. Validation Commands for Changes

```bash
python -m flake8 grvt_bot tests --select=E9,F63,F7,F82 --jobs=1
python -m mypy --ignore-missing-imports --follow-imports=skip grvt_bot/cli/main.py
pytest -q
```

## 10. Related Active Docs

- `README.md`
- `RUNBOOK.md`
- `OPERATIONS_CHECKLIST.md`
- `CONFIG_REFERENCE.md`
- `PAXG_STRATEGY_DOCS.md`
- `docs/MIGRATION.md`
- `PROJECT_OVERVIEW_TH.md`
