# PAXG Mean Reversion Strategy

เอกสารนี้อธิบายพฤติกรรมจริงของ `PAXGMeanReversionStrategy` ในระบบ runtime ปัจจุบัน

## 1. Strategy Summary

- Strategy class: `PAXGMeanReversionStrategy`
- Symbol หลัก: `PAXG_USDT_Perp` (ปรับได้ใน config)
- Timeframe หลัก: `15m` (ค่า default ใน strategy)
- แนวคิด: Mean reversion ด้วย Bollinger Bands + ATR stop distance

## 2. Entry Logic

ใช้ข้อมูล candle ล่าสุดและ candle ก่อนหน้า:

1. Long entry (`buy`)
- เงื่อนไข: close ของ candle ก่อนหน้า `< lower band`
- เหตุผล: ราคา oversold มีโอกาส revert กลับ mean

2. Short entry (`sell`)
- เงื่อนไข: close ของ candle ก่อนหน้า `> upper band`
- เหตุผล: ราคา overbought มีโอกาส revert ลง

## 3. Exit Logic

Exit เป็นแบบ dynamic โดย strategy ตรวจเงื่อนไขผ่าน `check_exit`:

1. ถ้า position เป็น long และราคาปัจจุบันแตะ/สูงกว่า middle band -> close
2. ถ้า position เป็น short และราคาปัจจุบันแตะ/ต่ำกว่า middle band -> close

หมายเหตุ:
- ตอนปิดจริง runtime ใช้ adaptive reduce-only close flow ใน executor
- ไม่ได้ยิงปิดแบบ fixed one-shot เสมอ

## 4. Position Sizing (ใน Strategy)

strategy คำนวณ `amount_usdt` จาก:

- `capital`
- `risk_per_trade_pct`
- `atr_window`
- `sl_atr_multiplier`

สูตรโดยย่อ:

1. `risk_amount = capital * (risk_per_trade_pct / 100)`
2. `sl_distance = ATR * sl_atr_multiplier`
3. `position_size_units = risk_amount / sl_distance`
4. `position_size_usdt = position_size_units * entry_price`

จากนั้น runtime จะคุมซ้ำด้วย risk engine อีกชั้น (fail-closed)

## 5. Runtime Integration (สำคัญ)

strategy ไม่ได้ทำงานลำพัง แต่ถูกควบคุมโดย runtime policy:

1. Loop cadence
- รันตาม `trading.loop_interval` (หน่วยนาที)
- align ที่ second `00`
- รอ `ops.data_close_buffer_seconds` ก่อน fetch candle

2. Data guards
- stale candle guard
- duplicate candle guard

3. Risk gates
- `risk.kill_switch`
- halted state
- `min_qty` จาก exchange metadata
- derived min notional:
  - `min_qty * reference_price * risk.min_notional_safety_factor`

4. Threshold controls
- track `normal` / `low_vol`
- hit drawdown/profit target -> flatten + halt

5. Startup reconcile
- policy ตาม `ops.startup_mismatch_policy`
  - `adopt_continue`
  - `halt_only`
  - `auto_flatten_halt`

## 6. API-Only Close Execution

ระบบปิด position ใช้ adaptive reduce-only execution:

1. อ่าน orderbook ฝั่งตรงข้าม
2. ถ้า liquidity พอใน slippage band -> ปิดทีเดียว
3. ถ้า liquidity บาง -> ซอยไม้แล้ว retry
4. มี stop guards กัน loop ไม่จบ:
- `execution.close_max_retries`
- `execution.close_max_duration_seconds`
- `execution.close_no_progress_retries`

reason codes ที่เจอได้:
- `CLOSE_SUCCESS`
- `CLOSE_NO_PROGRESS`
- `CLOSE_TIMEOUT`
- `CLOSE_INCOMPLETE_THIN_BOOK`

## 7. Recommended Config (สำหรับเริ่มต้น)

```yaml
trading:
  symbol: "PAXG_USDT_Perp"
  leverage: 10
  loop_interval: 1

risk:
  active_track: "normal"
  fail_closed: true
  threshold_action: "flatten_halt"
  risk_per_trade_pct: 0.25

ops:
  data_close_buffer_seconds: 2
  startup_mismatch_policy: "adopt_continue"

execution:
  close_mode: "reduce_only_twap_slice"
  liquidity_usage_pct: 0.20
  max_slippage_bps: 20
  close_retry_interval_seconds: 2
  close_max_retries: 20
  close_max_duration_seconds: 90
  close_no_progress_retries: 3
```

## 8. Limitations / Notes

1. Strategy ต้องมี `pandas` และ `ta`
2. ถ้า exchange metadata/candle/reference price ขาด และ `fail_closed=true` จะ block entry
3. การ leverage จริงควรยืนยันที่ exchange side ให้ตรง config

## 9. Run Commands

```bash
grvt-bot --config config/config.yaml --strategy PAXGMeanReversionStrategy --dry-run
grvt-bot --config config/config.yaml --strategy PAXGMeanReversionStrategy
```

เอกสารที่ใช้คู่กัน:
- `RUNBOOK.md`
- `CONFIG_REFERENCE.md`
- `OPERATIONS_CHECKLIST.md`
