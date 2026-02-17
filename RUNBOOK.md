# RUNBOOK

This runbook is for operating the bot in API-only mode.

## 1. Preconditions

- `config/config.yaml` is present and validated.
- Strategy dependencies for default runtime are installed (`pandas`, `ta`).
- API key and private key are correct for selected `grvt.env`.
- Account leverage is set as expected on exchange side.
- `risk.fail_closed=true`.
- `ops.startup_mismatch_policy` is explicitly set.

## 2. Start Procedure

1. Verify CLI availability:

```bash
grvt-bot --help
```

2. Optional smoke test:

```bash
grvt-bot --config config/config.yaml --dry-run
```

3. Run live strategy (default is `PAXGMeanReversionStrategy`):

```bash
grvt-bot --config config/config.yaml
```

4. If needed, force random strategy:

```bash
grvt-bot --config config/config.yaml --strategy random --dry-run
```

## 3. What To Watch In Logs

- Startup:
  - `Runtime lock acquired`
  - `Startup mismatch` plus selected startup policy behavior
- Loop:
  - `Minute cycle #...`
  - `Waiting ...s after boundary before candle fetch`
- Risk:
  - `[ENTRY BLOCKED] ...`
  - `[RISK] MAX_DRAWDOWN_HIT` or `[RISK] PROFIT_TARGET_HIT`
- Exit/close:
  - `Position closed successfully`
  - close failure code in `last_close_reason` / alert messages

## 4. Startup Reconcile Policy

Configured by `ops.startup_mismatch_policy`:

- `adopt_continue`:
  - Exchange position becomes source of truth.
  - Bot continues (no forced halt).
- `halt_only`:
  - Bot halts immediately on mismatch.
- `auto_flatten_halt`:
  - Bot tries adaptive close first, then halts regardless of result.

## 5. Adaptive Close Execution

Close logic uses orderbook depth and reduce-only orders.

Behavior:
- If liquidity in slippage band is enough: close in one shot.
- If liquidity is thin: slice and retry.
- Exit conditions are finite (no infinite retry):
  - `execution.close_max_retries`
  - `execution.close_max_duration_seconds`
  - `execution.close_no_progress_retries`

## 6. Close Reason Codes

- `CLOSE_SUCCESS`: close completed.
- `CLOSE_NO_PROGRESS`: repeated attempts with no reduction in remaining qty.
- `CLOSE_TIMEOUT`: retry cap or duration cap reached.
- `CLOSE_INCOMPLETE_THIN_BOOK`: thin liquidity prevented compliant close.
- `CLOSE_INVALID_SIDE`: invalid close side input.
- `DRY_RUN_CLOSE`: simulated close in dry-run path.

## 7. Halt and Recovery

If bot halts due to close/risk conditions:

1. Check `state/runtime_state.json`:
  - `halted`
  - `halt_reason`
  - `open_position`
  - `last_close_reason`
2. Verify actual exchange position via API.
3. Resolve position first (or update policy for controlled recovery).
4. Clear halt state only when exchange and local state are consistent.

## 8. Runtime Lock

- Lock file path: `ops.lock_file` (default `state/runtime.lock`).
- Only one runtime instance should hold the lock.
- If stale lock is suspected, verify process status before manual cleanup.

## 9. Incident Response

Immediate stop conditions:
- repeated close failures (`CLOSE_NO_PROGRESS`, `CLOSE_TIMEOUT`, `CLOSE_INCOMPLETE_THIN_BOOK`)
- repeated reconcile mismatch at startup
- API failure burst or connectivity instability

Action:
1. Halt bot.
2. Capture relevant log segment and current state file.
3. Verify exchange position and balances by API.
4. Resume only after root cause is identified.
