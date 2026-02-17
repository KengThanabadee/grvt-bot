# OPERATIONS CHECKLIST

Use this checklist for execution discipline. For failure playbooks, see `RUNBOOK.md`.

## A. Pre-Live

- [ ] Correct credentials loaded for target `grvt.env`.
- [ ] No secrets committed to tracked files.
- [ ] Strategy deps installed (`pandas`, `ta`) for default runtime.
- [ ] `risk.fail_closed=true`.
- [ ] `risk.kill_switch=false` unless intentionally paused.
- [ ] `ops.startup_mismatch_policy` explicitly set.
- [ ] `ops.state_file` and `ops.lock_file` paths writable.
- [ ] `execution.close_mode=reduce_only_twap_slice`.
- [ ] `trading.symbol` intentionally set for selected strategy.

## B. Local Gates

- [ ] `python -m grvt_bot.cli.main --help`
- [ ] `python -m flake8 grvt_bot tests --select=E9,F63,F7,F82 --jobs=1`
- [ ] `python -m mypy --ignore-missing-imports --follow-imports=skip grvt_bot/cli/main.py`
- [ ] `pytest -q`

## C. Live Session

- [ ] Runtime lock acquired exactly once.
- [ ] Startup reconcile result is understood.
- [ ] Loop remains minute-aligned without stale-candle floods.
- [ ] Entry blocks are expected and explainable.
- [ ] No repeated `CLOSE_NO_PROGRESS` or `CLOSE_TIMEOUT`.
- [ ] Track (`risk.active_track`) matches session intent.

## D. Incident / Halt

- [ ] Stop bot process.
- [ ] Capture logs and `state/runtime_state.json`.
- [ ] Verify exchange position and account state.
- [ ] Follow `RUNBOOK.md` known failure pattern response.
- [ ] Resume using dry-run or canary sizing first.

## E. Post-Run

- [ ] Confirm open position state is intentional.
- [ ] Review halt reason / close reason if present.
- [ ] Record config values used in session.
- [ ] Apply one parameter change at a time before next run.
