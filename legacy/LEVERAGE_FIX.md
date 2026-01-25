# Leverage Management - Final Summary

## 🔍 สรุปปัญหาและการแก้ไข

### ปัญหาที่พบ

1. **ปัญหาเดิม**: Bot ไม่สามารถปรับ leverage ผ่าน code ได้
2. **หลังแก้ไข**: สามารถเรียก API ได้ แต่ได้ **error 403 "Not authorized"**

### สาเหตุ

GRVT **ไม่อนุญาตให้ตั้งค่า leverage ผ่าน API** บน testnet หรือต้องการ permission พิเศษ:

```
GrvtError(code=1001, message='You are not authorized to access this functionality', status=403)
```

### วิธีแก้ไข Final

✅ **Bot จะทำงานได้ปกติ** แม้ว่าจะตั้งค่า leverage ผ่าน API ไม่ได้

1. Bot จะพยายามตั้งค่า leverage ผ่าน API
2. ถ้าไม่สำเร็จ → แสดงคำเตือนและตรวจสอบ leverage ปัจจุบัน
3. Bot ทำงานต่อด้วย leverage ที่ตั้งค่าบนเว็บ

---

## 📝 วิธีใช้งาน

### 1. ตั้งค่า Leverage บนเว็บ GRVT (Required)

เนื่องจาก API ไม่อนุญาตให้ตั้งค่า คุณต้อง:

1. ไปที่ [GRVT Testnet Web Interface](https://testnet.grvt.io/)
2. เลือก **BTC_USDT_Perp** (หรือ instrument ที่คุณใช้)
3. ตั้งค่า **Leverage = 10x** (หรือตามที่กำหนดใน `config.py`)
4. Save/Confirm

### 2. รัน Bot

```bash
.\env\Scripts\activate
python main.py
```

### 3. ตรวจสอบ Log

Bot จะแสดง:

```
2026-01-23 16:55:21 - INFO - Attempting to set leverage to 10x for BTC_USDT_Perp...
2026-01-23 16:55:21 - ERROR - Failed to set leverage: GrvtError(code=1001, message='You are not authorized...', status=403)
2026-01-23 16:55:21 - WARNING - ⚠ Could not set leverage via API (may require manual setup)
2026-01-23 16:55:21 - INFO - 📝 IMPORTANT: Please set leverage to 10x for BTC_USDT_Perp on GRVT web interface
2026-01-23 16:55:21 - INFO -    Bot will use whatever leverage is currently set on the exchange
2026-01-23 16:55:22 - INFO - ℹ️  Current leverage on exchange: 10x (min: 1x, max: 50x)
```

---

## ✅ Features ที่ทำงาน

### 1. ตรวจสอบ Leverage ปัจจุบัน (Working ✅)

```python
# ใน execution.py
result = executor.get_current_leverage("BTC_USDT_Perp")
print(f"Current: {result.leverage}x")
print(f"Min: {result.min_leverage}x, Max: {result.max_leverage}x")
```

### 2. พยายามตั้งค่า Leverage (Graceful Failure ✅)

```python
# Bot จะพยายาม แต่ถ้าไม่สำเร็จก็แสดง warning และทำงานต่อ
executor.set_leverage("BTC_USDT_Perp", 10)
```

### 3. การเตือนถ้า Leverage ไม่ตรง (Working ✅)

ถ้า leverage บนเว็บไม่ตรงกับ `config.py`:
```
⚠️ WARNING: Exchange leverage (5x) differs from config (10x)
```

---

## 🎯 Best Practice

### ขั้นตอนที่แนะนำ

1. **ตั้งค่า leverage บนเว็บก่อน** ตามค่าใน `config.py`
2. **รัน bot** → bot จะตรวจสอบและแจ้งเตือนถ้าไม่ตรง
3. **ตรวจสอบ log** เพื่อ confirm ว่า leverage ถูกต้อง

### ตรวจสอบ Leverage ปัจจุบัน

```python
# สคริปต์แยกสำหรับ check leverage
from execution import GRVTExecutor
import config

executor = GRVTExecutor()
result = executor.get_current_leverage(config.SYMBOL)

if result:
    print(f"Symbol: {result.instrument}")
    print(f"Current Leverage: {result.leverage}x")
    print(f"Min: {result.min_leverage}x")
    print(f"Max: {result.max_leverage}x")
```

---

## ❓ FAQ

### Q: ทำไม API ตั้งค่า leverage ไม่ได้?
**A:** GRVT อาจจำกัด permission นี้บน testnet หรือต้องการ signature พิเศษที่ยังไม่ support

### Q: Bot ทำงานได้ไหมถ้าตั้งค่า leverage ผ่าน API ไม่ได้?
**A:** ✅ **ได้!** Bot จะใช้ leverage ที่คุณตั้งค่าบนเว็บ

### Q: จะรู้ได้ยังไงว่า leverage ถูกต้อง?
**A:** ดูที่ log หลังเริ่ม bot:
```
ℹ️  Current leverage on exchange: 10x (min: 1x, max: 50x)
```

### Q: ถ้า leverage บนเว็บไม่ตรงกับ config จะเกิดอะไร?
**A:** Bot จะแสดง **WARNING** แต่จะยังทำงานต่อ (ใช้ค่าที่ตั้งบนเว็บ)

---

## 🔧 Code Changes Summary

### `execution.py`
- ✅ เพิ่ม `set_leverage()` ที่ใช้ Raw API
- ✅ เพิ่ม `get_current_leverage()` ที่ทำงานได้
- ✅ Handle authorization errors gracefully

### `main.py`
- ✅ พยายามตั้งค่า leverage อัตโนมัติ
- ✅ แสดง warning ถ้าไม่สำเร็จ
- ✅ ตรวจสอบและแจ้ง leverage ปัจจุบัน
- ✅ เตือนถ้า leverage ไม่ตรงกับ config

---

## 📊 Status

| Feature | Status | หมายเหตุ |
|---------|--------|----------|
| Get Current Leverage | ✅ Working | อ่านค่าได้ปกติ |
| Set Leverage via API | ⚠️ Not Authorized | GRVT ไม่อนุญาต |
| Manual Leverage Setup | ✅ Working | ตั้งค่าบนเว็บแทน |
| Leverage Verification | ✅ Working | Bot check และเตือน |
| Bot Trading | ✅ Working | ใช้ leverage จากเว็บ |

---

## 🎉 Conclusion

แม้ว่า GRVT จะไม่อนุญาตให้ตั้งค่า leverage ผ่าน API แต่:

✅ Bot **ทำงานได้ปกติ** โดยใช้ leverage ที่ตั้งบนเว็บ  
✅ Bot **ตรวจสอบและเตือน** ถ้า leverage ไม่ตรงกับ config  
✅ มี **utility functions** สำหรับตรวจสอบ leverage  
✅ Code มี **error handling** ที่ดี ไม่ crash

**คุณสามารถใช้ bot ได้เลย!** เพียงแค่ตั้งค่า leverage บนเว็บ GRVT ก่อนรัน 🚀
