# ภาพรวมระบบ GRVT Bot (ภาษาไทย)

เอกสารนี้เป็นคู่มือภาพรวมสำหรับผู้ดูแลระบบ (operator) โดยอ้างอิงพฤติกรรม runtime ปัจจุบัน

## 1. ระบบนี้ทำอะไร

`grvt-bot` เป็นบอทเทรดแบบ API-only สำหรับตลาด perpetual บน GRVT โดยเน้น:
- การคุมความเสี่ยงแบบ fail-closed
- การทำงานรอบเวลาแบบ minute-aligned
- การเก็บ state เพื่อฟื้นตัวหลัง restart
- การปิดสถานะแบบ adaptive reduce-only

## 2. โครงสร้างหลักที่ต้องรู้

- `grvt_bot/cli/main.py`
  - จุดเริ่ม runtime loop
  - จัดการ schedule, strategy, risk, state และ execution
- `grvt_bot/core/config.py`
  - โหลด config จาก YAML และ environment variables
- `grvt_bot/core/risk.py`
  - entry gate, threshold และ kill switch
- `grvt_bot/core/state.py`
  - จัดเก็บ state และ reconcile กับ exchange ตอนเริ่มระบบ
- `grvt_bot/core/executor.py`
  - ดึงราคา ส่งออเดอร์ และ close แบบ adaptive

## 3. ลำดับการทำงานโดยย่อ

1. โหลด config และตรวจความถูกต้อง
2. lock process เพื่อกันรันซ้ำหลาย instance
3. reconcile state กับ position จริงบน exchange
4. เข้า loop ตาม `trading.loop_interval` (หน่วย: นาที)
5. รอ `ops.data_close_buffer_seconds` ก่อนดึง candle
6. ประเมิน risk/threshold ก่อนเปิดสถานะ
7. ส่งคำสั่งผ่าน executor และบันทึก state

## 4. โหมดใช้งาน (Testnet / Production)

- Testnet:
  - `grvt.env: testnet`
  - ใช้ทดสอบ logic และ dry-run
- Production:
  - `grvt.env: prod`
  - ใช้เงินจริง ต้องเริ่มแบบ canary ก่อน

## 5. จุดที่ต้องระวัง

- ค่า `trading.loop_interval` เป็น “นาที” ไม่ใช่วินาที
- ค่า default strategy ใน CLI คือ `PAXGMeanReversionStrategy`
- แต่ค่า default symbol ใน config code คือ `BTC_USDT_Perp`
  - ถ้าจะใช้กลยุทธ์ PAXG ให้ตั้ง `trading.symbol` เป็น `PAXG_USDT_Perp` ชัดเจน

## 6. คำสั่งพื้นฐาน

```bash
grvt-bot --config config/config.yaml --dry-run
grvt-bot --config config/config.yaml
```

## 7. เอกสารที่ควรอ่านต่อ

1. `README.md`
2. `RUNBOOK.md`
3. `CONFIG_REFERENCE.md`
4. `OPERATIONS_CHECKLIST.md`
5. `PAXG_STRATEGY_DOCS.md`

## 8. ขอบเขตเอกสารนี้

- เน้นมุม operator และการ deploy/runtime
- รายละเอียดเชิง migration/dev ดูที่ `docs/MIGRATION.md` และ `docs/SKILL.md`
