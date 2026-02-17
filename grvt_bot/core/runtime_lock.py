"""
Single-instance runtime lock for bot process.
"""

from __future__ import annotations

import errno
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RuntimeLock:
    """File-based process lock to prevent multiple bot instances."""

    def __init__(self, lock_path: str, logger: Optional[logging.Logger] = None):
        self.path = Path(lock_path)
        self.logger = logger or logging.getLogger(__name__)
        self.acquired = False

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but not permitted to signal.
            return True
        except OSError as exc:
            if exc.errno in (errno.EPERM, errno.EACCES):
                return True
            return False

    def _read_lock_payload(self) -> Optional[Dict[str, Any]]:
        if not self.path.exists():
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                return payload
            return None
        except Exception:
            return None

    def acquire(self) -> None:
        """
        Acquire lock file or raise RuntimeError if another instance is alive.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._read_lock_payload()
        current_pid = os.getpid()

        if payload:
            existing_pid_raw = payload.get("pid")
            try:
                existing_pid = int(existing_pid_raw)
            except (TypeError, ValueError):
                existing_pid = 0

            if existing_pid > 0 and existing_pid != current_pid and self._is_pid_alive(existing_pid):
                raise RuntimeError(
                    f"Another bot instance is running (pid={existing_pid}). "
                    f"Remove stale lock only if you are sure process is dead: {self.path}"
                )

        data = {
            "pid": current_pid,
            "started_at": _utc_now_iso(),
            "command": " ".join(sys.argv),
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True, indent=2, sort_keys=True)
        tmp.replace(self.path)
        self.acquired = True
        self.logger.info("Runtime lock acquired: %s (pid=%s)", self.path, current_pid)

    def release(self) -> None:
        """Release lock when owned by this process."""
        if not self.acquired:
            return

        try:
            payload = self._read_lock_payload() or {}
            file_pid = int(payload.get("pid", -1))
            if file_pid == os.getpid() and self.path.exists():
                self.path.unlink()
                self.logger.info("Runtime lock released: %s", self.path)
        except Exception as exc:
            self.logger.warning("Failed to release runtime lock %s: %s", self.path, exc)
        finally:
            self.acquired = False
