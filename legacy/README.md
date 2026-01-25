# Legacy Files

This folder contains old files from the script-based structure that have been replaced by the modular package.

## ⚠️ These files are no longer used

The bot now uses the modular package structure in `grvt_bot/`.

### Old Files (Replaced)

| Old File | Replaced By | Notes |
|----------|-------------|-------|
| `main.py` | `grvt_bot/cli/main.py` | Use `grvt-bot` command instead |
| `execution.py` | `grvt_bot/core/executor.py` | Import from `grvt_bot.core` |
| `trading_logic.py` | `grvt_bot/strategies/random_strategy.py` | Import from `grvt_bot.strategies` |
| `config.py` | `config/config.yaml` | Use YAML configuration |
| `check_leverage.py` | `scripts/check_leverage.py` | Moved to scripts folder |
| `README.md` | `../README.md` (new modular version) | Updated documentation |
| `README_TH.md` | `../PROJECT_OVERVIEW_TH.md` | Thai documentation updated |

## 📚 New Documentation

For current usage, see:
- [README.md](../README.md) - Main documentation
- [docs/SKILL.md](../docs/SKILL.md) - Antigravity skill documentation
- [docs/MIGRATION.md](../docs/MIGRATION.md) - Migration guide

## 🔄 Migration

If you have custom code using these old files, see [docs/MIGRATION.md](../docs/MIGRATION.md) for migration instructions.

---

**These files are kept for reference only. Do not use them in new code.**
