# ภาพรวมโปรเจกต์ (Thai)

เอกสารนี้สรุปโครงสร้างและพฤติกรรมของระบบบอทเวอร์ชันปัจจุบันแบบสั้นและใช้งานจริง

## 1. เป้าหมายโปรเจกต์

`grvt_demo_bot` คือบอทเทรดสำหรับ GRVT perpetual market ที่เน้น:

1. รันแบบ API-only
2. คุมความเสี่ยงแบบ fail-closed
3. มี state/reconcile เพื่อ recovery หลัง restart
4. ปิด position แบบ adaptive ตาม liquidity ของ orderbook

## 2. สถาปัตยกรรมหลัก

โครงสร้างสำคัญ:

- `grvt_bot/cli/main.py`
  - entrypoint ของบอท
  - loop minute-aligned
  - ผูก strategy + risk + state + execution
- `grvt_bot/core/config.py`
  - config manager จาก YAML + env override
- `grvt_bot/core/executor.py`
  - interface คุย exchange (price/order/position/orderbook)
  - adaptive reduce-only close flow
- `grvt_bot/core/risk.py`
  - entry gate และ threshold policy
- `grvt_bot/core/state.py`
  - persist/recover/reconcile state
- `grvt_bot/core/alerts.py`
  - alerts ผ่าน logger และ telegram (optional)
- `grvt_bot/strategies/`
  - strategy implementations (`random`, `paxg_mean_reversion_strategy`)

## 3. พฤติกรรม Runtime ปัจจุบัน

1. Scheduler
- รันตาม `trading.loop_interval` (นาที)
- align ที่วินาที `00`
- รอ `ops.data_close_buffer_seconds` ก่อนดึง candle

2. Data guards
- ถ้า candle เก่าเกินหรือซ้ำรอบเดิม จะ skip

3. Startup reconcile
- sync state กับ exchange ก่อนเริ่ม loop
- policy ตาม `ops.startup_mismatch_policy`:
  - `adopt_continue`
  - `halt_only`
  - `auto_flatten_halt`

4. Risk flow
- บล็อก entry เมื่อ kill-switch/halted/fail-closed condition
- คำนวณ sizing จาก `risk_per_trade_pct + leverage`
- ตรวจ min thresholds จาก exchange metadata + derived min notional

5. Exit/flatten execution
- ใช้ adaptive close แบบ reduce-only
- ถ้า liquidity ดี: ปิดก้อนเดียว
- ถ้า liquidity บาง: ซอยไม้ + retry
- มี hard stop เพื่อไม่ให้วนไม่จบ

## 4. Config Domains ที่สำคัญ

1. `grvt`: credentials + env
2. `trading`: symbol/leverage/loop interval
3. `risk`: track, thresholds, fail-closed, risk per trade
4. `ops`: state/lock/reconcile/runtime guards
5. `execution`: adaptive close policy
6. `alerts`: alert channels

ดูรายละเอียด key ทั้งหมดที่ `CONFIG_REFERENCE.md`

## 5. State และความทนทาน

state file (`ops.state_file`) เก็บอย่างน้อย:

- `open_position`
- `halted` / `halt_reason`
- `baseline_equity_usdt`
- `last_candle_open_time_ms`
- `pending_action`
- `close_attempt_count`
- `last_close_reason`

เป้าหมายคือ restart แล้ว recover ได้ และไม่สูญเสียบริบทการจัดการความเสี่ยง

## 6. Test Strategy

แนวปัจจุบัน:

1. Unit tests เป็น default (`pytest -q`)
2. Integration tests opt-in (`RUN_LIVE_TESTS=1`)
3. มี test ครอบ scheduler/risk/state/executor close policy

## 7. การใช้งานเอกสาร

ลำดับอ่านสำหรับ operator:

1. `README.md`
2. `RUNBOOK.md`
3. `CONFIG_REFERENCE.md`
4. `OPERATIONS_CHECKLIST.md`
5. `PAXG_STRATEGY_DOCS.md` (เมื่อใช้ strategy นี้)

## 8. Known Non-Goals (รอบนี้)

1. ไม่แตะ git history cleanup
2. ไม่ผูกกับ UI/web flow สำหรับการเทรดจริง
3. ไม่ refactor legacy ทั้งก้อน
