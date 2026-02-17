# RUNBOOK

Runbook for operating GRVT Bot in API-only mode.

## 1. Preconditions

- `config/config.yaml` exists and passes local validation.
- Required strategy deps are installed (`pandas`, `ta`) for default strategy.
- GRVT credentials match selected `grvt.env`.
- `risk.fail_closed=true` for production runs.
- `ops.startup_mismatch_policy` is explicitly set.

## 2. Start Procedure

1. Check CLI.

```bash
grvt-bot --help
```

2. Run dry-run.

```bash
grvt-bot --config config/config.yaml --dry-run
```

3. Start runtime.

```bash
grvt-bot --config config/config.yaml
```

4. Optional random smoke strategy.

```bash
grvt-bot --config config/config.yaml --strategy random --dry-run
```

## 3. Environment Modes (Testnet vs Prod)

| Topic | Testnet | Production |
|---|---|---|
| `grvt.env` | `testnet` | `prod` |
| Credentials | test credentials | production credentials |
| Capital risk | test funds | real funds |
| First execution | dry-run then small live size | dry-run on prod creds then canary size |

### Minimum switch checklist to production

1. Replace all GRVT credentials with production values.
2. Verify `trading.symbol` and leverage settings on production account.
3. Keep `risk.fail_closed=true` and reduce `risk.risk_per_trade_pct` for canary.
4. Run one canary cycle before normal sizing.

## 4. Runtime Signals to Watch

### Startup

- `Runtime lock acquired`
- startup reconcile outcome and selected policy behavior

### Loop health

- `Minute cycle #...`
- post-boundary wait message
- no stale-candle warning floods

### Risk and entry

- `[ENTRY BLOCKED] ...`
- threshold events (`MAX_DRAWDOWN_HIT`, `PROFIT_TARGET_HIT`)

### Exit and close flow

- `Position closed successfully`
- close failure code in alerts/state

## 5. Startup Reconcile Policy

Configured by `ops.startup_mismatch_policy`:

- `adopt_continue`: adopt exchange position and continue.
- `halt_only`: halt on mismatch.
- `auto_flatten_halt`: attempt adaptive flatten, then halt.

## 6. Adaptive Close Execution

Close path uses orderbook-aware, reduce-only market slices.

Stop guards preventing infinite retry:
- `execution.close_max_retries`
- `execution.close_max_duration_seconds`
- `execution.close_no_progress_retries`

## 7. Close Reason Codes

- `CLOSE_SUCCESS`
- `CLOSE_NO_PROGRESS`
- `CLOSE_TIMEOUT`
- `CLOSE_INCOMPLETE_THIN_BOOK`
- `CLOSE_INVALID_SIDE`
- `DRY_RUN_CLOSE`

## 8. Halt and Recovery

1. Inspect `state/runtime_state.json`:
- `halted`
- `halt_reason`
- `open_position`
- `last_close_reason`

2. Verify live exchange position and balance.
3. Resolve mismatch/position state first.
4. Resume only when local state and exchange state match.

## 9. Runtime Lock

- Lock path: `ops.lock_file` (default `state/runtime.lock`).
- Only one active runtime instance should hold lock.
- Remove lock manually only after PID/process validation.

## 10. Incident Response

Immediate pause conditions:
- repeated `CLOSE_*` failures,
- repeated startup reconcile mismatch,
- repeated runtime exceptions and auto-exit,
- account/equity data unavailable under fail-closed mode.

Response flow:
1. Stop bot process.
2. Capture logs + state file.
3. Verify exchange state.
4. Apply config/runtime corrective action.
5. Resume with dry-run or canary first.

## 11. Known Failure Patterns

1. `CLOSE_NO_PROGRESS`
- Cause: thin liquidity or no net reduction per cycle.
- Action: reduce size, tune `execution.max_slippage_bps` / `execution.close_min_slice_qty`, verify live position.

2. `CLOSE_TIMEOUT`
- Cause: retry or duration cap reached before flatten.
- Action: inspect book depth and close guard values (`close_max_retries`, `close_max_duration_seconds`).

3. Startup reconcile mismatch
- Cause: local state diverges from exchange after restart/manual actions.
- Action: follow selected startup policy and reconcile before resuming.

4. Repeated runtime errors then process exit
- Cause: recurring exception in configured error window.
- Action: inspect stack traces, run dry-run, and re-enable live only after fix.

5. Equity unavailable while fail-closed
- Cause: account summary endpoint failure or malformed payload.
- Action: restore account-data reliability before allowing entries.
