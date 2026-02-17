# OPERATIONS CHECKLIST

## A. Pre-Live Checklist

1. Credentials
- Correct API key/private key loaded for target env.
- No real credentials in git-tracked files.

2. Strategy runtime deps
- `pandas` and `ta` are installed for default strategy.

3. Config safety
- `risk.fail_closed=true`
- `risk.kill_switch=false` (unless intentionally paused)
- `ops.startup_mismatch_policy` explicitly set
- `execution.close_mode=reduce_only_twap_slice`

4. Runtime controls
- `ops.lock_file` path valid
- `ops.state_file` path writable
- Log file path valid

5. Test gates
- `python -m grvt_bot.cli.main --help`
- `python -m flake8 grvt_bot tests --select=E9,F63,F7,F82 --jobs=1`
- `python -m mypy --ignore-missing-imports --follow-imports=skip grvt_bot/cli/main.py`
- `pytest --collect-only -q`
- `pytest -q`
- `RUN_LIVE_TESTS=1 pytest --collect-only -q -m integration`

6. Canary sizing
- Start with low `risk.risk_per_trade_pct` (example `0.10`)
- One symbol only for first live session

## B. Live Session Checklist

1. Startup
- Confirm runtime lock acquired once.
- Confirm startup reconcile message and policy behavior.

2. Loop health
- Cycle logs are minute-aligned.
- No stale-candle flood.
- No repeated runtime exception flood.

3. Trade safety
- Entry blocks are understandable and expected.
- Exit/close path uses reduce-only.
- No repeated `CLOSE_NO_PROGRESS`/`CLOSE_TIMEOUT`.

4. Risk controls
- Track is correct (`normal` or `low_vol`).
- Drawdown/profit threshold behavior is visible in logs.
- Kill switch remains available for immediate entry block.

## C. Halt/Incident Checklist

1. Trigger
- Any close failure storm (`CLOSE_*`) or reconcile instability.

2. Immediate actions
- Stop bot process.
- Capture logs and `state/runtime_state.json`.
- Check exchange position/balance via API.

3. Recovery
- Ensure local state and exchange position are consistent.
- Clear or keep halted state intentionally.
- Resume only after root cause identified.

## D. Post-Run Checklist

1. Review
- Confirm no orphan/open position is unintended.
- Confirm halt state and reasons are understood.

2. Archive
- Keep run logs and incident notes.
- Record config values used during session.

3. Next iteration
- Adjust only one risk/execution parameter set at a time.
- Re-run pre-live checks before next live start.
