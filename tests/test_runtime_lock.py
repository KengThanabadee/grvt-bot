import json
import shutil
import uuid
from pathlib import Path

import pytest

from grvt_bot.core.runtime_lock import RuntimeLock


def _make_tmp_dir() -> Path:
    path = Path(f".runtime_lock_test_{uuid.uuid4().hex}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_runtime_lock_acquire_release():
    tmp_dir = _make_tmp_dir()
    try:
        lock_path = tmp_dir / "runtime.lock"
        lock = RuntimeLock(str(lock_path))
        lock.acquire()
        assert lock_path.exists()
        lock.release()
        assert not lock_path.exists()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_runtime_lock_overwrites_stale_lock():
    tmp_dir = _make_tmp_dir()
    try:
        lock_path = tmp_dir / "runtime.lock"
        lock_path.write_text(
            json.dumps({"pid": 999999, "started_at": "old"}),
            encoding="utf-8",
        )
        lock = RuntimeLock(str(lock_path))
        lock.acquire()
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        assert int(payload["pid"]) > 0
        lock.release()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_runtime_lock_blocks_if_other_pid_alive(monkeypatch):
    tmp_dir = _make_tmp_dir()
    try:
        lock_path = tmp_dir / "runtime.lock"
        lock_path.write_text(
            json.dumps({"pid": 123456, "started_at": "running"}),
            encoding="utf-8",
        )
        monkeypatch.setattr(RuntimeLock, "_is_pid_alive", staticmethod(lambda pid: True))
        lock = RuntimeLock(str(lock_path))
        with pytest.raises(RuntimeError):
            lock.acquire()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
