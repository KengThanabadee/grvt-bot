# Migration Guide (Legacy Script Style -> Current Runtime)

This guide helps migrate from legacy script usage to the current package/runtime model.

## 1. Migration Goal

Move from ad-hoc script execution to a single CLI/runtime flow with:
- centralized config,
- risk + state controls,
- predictable operator runbook.

## 2. Current Canonical Runtime

Use:

```bash
grvt-bot --config config/config.yaml
```

Do not rely on historical top-level script paths as runtime entrypoints.

## 3. Legacy-to-Current Mapping

| Legacy concept | Current equivalent |
|---|---|
| Script entrypoint | `grvt_bot/cli/main.py` via `grvt-bot` command |
| Python config constants | `config/config.yaml` + `ConfigManager` |
| Manual loop logic | minute-aligned runtime loop with data guard |
| direct exchange calls only | executor + risk + state orchestration |
| ad-hoc shutdown/restart | lock + persisted runtime state + startup reconcile |

## 4. Required Migration Steps

1. Install package and deps.

```bash
pip install -e .
pip install pandas ta
```

2. Create config from template.

```bash
cp config/config.example.yaml config/config.yaml
```

3. Populate credentials and environment.

4. Validate locally.

```bash
grvt-bot --config config/config.yaml --dry-run
```

5. Start runtime.

```bash
grvt-bot --config config/config.yaml
```

## 5. Config Migration Notes

- `trading.loop_interval` is now minutes.
- Use domain-based keys (`grvt`, `trading`, `risk`, `ops`, `execution`, `alerts`).
- Risk and execution controls are explicit; do not assume permissive defaults.

## 6. Strategy Migration Notes

- Strategy should implement `BaseStrategy` contract.
- Add `check_exit()` for managed exit behavior.
- Signal fields should match runtime expectations (`side`, optional `amount_usdt`, optional `sl_price/tp_price`).

## 7. Operational Migration Notes

- Startup reconcile is now mandatory behavior.
- Runtime state is persisted (`ops.state_file`).
- Single-instance lock is enforced (`ops.lock_file`).

## 8. Common Migration Pitfalls

1. Wrong symbol for selected strategy
- Example: running PAXG strategy while symbol remains `BTC_USDT_Perp`.

2. Assuming loop interval is seconds
- Runtime expects minutes.

3. Skipping dry-run after config changes
- Restart with dry-run after each significant config update.

4. Ignoring close failure codes
- `CLOSE_*` codes require runbook response before resuming.

## 9. Post-Migration Validation

```bash
python -m grvt_bot.cli.main --help
python -m flake8 grvt_bot tests --select=E9,F63,F7,F82 --jobs=1
python -m mypy --ignore-missing-imports --follow-imports=skip grvt_bot/cli/main.py
pytest -q
```

## 10. Scope of This Guide

- Focused on practical migration to current runtime.
- Historical narrative is intentionally minimized; git history is the archive.
