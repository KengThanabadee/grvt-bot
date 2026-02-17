"""
Alert helpers (logger + optional Telegram notifications).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import requests


class AlertManager:
    """Sends alerts to logs and optional Telegram channel."""

    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        self.enabled = self._get_bool("alerts", "enabled", True)
        self.telegram_enabled = self._get_bool("alerts", "telegram_enabled", False)
        self.telegram_bot_token = (
            os.getenv("TELEGRAM_BOT_TOKEN")
            or self._get("alerts", "telegram_bot_token", "")
            or ""
        )
        self.telegram_chat_id = (
            os.getenv("TELEGRAM_CHAT_ID")
            or self._get("alerts", "telegram_chat_id", "")
            or ""
        )

    def _get(self, section: str, key: str, default: Any = None) -> Any:
        if hasattr(self.config, "get"):
            return self.config.get(section, key, default)
        return default

    def _get_bool(self, section: str, key: str, default: bool) -> bool:
        value = self._get(section, key, default)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def send(self, message: str, level: str = "info") -> None:
        """Send alert to logger and Telegram (when configured)."""
        text = str(message)
        level = level.lower()
        if level == "error":
            self.logger.error(text)
        elif level == "warning":
            self.logger.warning(text)
        else:
            self.logger.info(text)

        if not self.enabled or not self.telegram_enabled:
            return
        if not self.telegram_bot_token or not self.telegram_chat_id:
            self.logger.debug("Telegram alert skipped: token/chat_id not configured")
            return

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {"chat_id": self.telegram_chat_id, "text": text}
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code >= 400:
                self.logger.warning(
                    "Telegram alert failed status=%s body=%s",
                    response.status_code,
                    response.text,
                )
        except Exception as exc:
            self.logger.warning("Telegram alert error: %s", exc)
