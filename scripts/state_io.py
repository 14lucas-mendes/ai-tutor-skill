#!/usr/bin/env python3
"""Concurrency-safe JSON updates for canonical AI Tutor state."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

try:
    from scripts.init_study import atomic_write
except ModuleNotFoundError:  # direct import from the scripts directory
    from init_study import atomic_write


class RevisionConflict(RuntimeError):
    """Raised when a caller tries to update a stale canonical revision."""


class FileLock:
    def __init__(self, path: Path, *, timeout: float = 5.0, poll_interval: float = 0.05):
        self.path = Path(path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._owned = False

    def __enter__(self) -> "FileLock":
        deadline = time.monotonic() + self.timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                descriptor = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(f"pid={os.getpid()}\n")
                self._owned = True
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for lock: {self.path}")
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._owned:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            finally:
                self._owned = False


def atomic_update_json(
    path: Path,
    updater: Callable[[dict], dict | None],
    *,
    expected_revision: int | None = None,
    timeout: float = 5.0,
) -> dict:
    """Read, validate revision, update, and atomically replace a JSON object.

    The lock is a sibling ``.lock`` file acquired with exclusive creation. The
    canonical integer ``revision`` is incremented exactly once after the
    updater succeeds. A stale ``expected_revision`` leaves the original file
    untouched and raises :class:`RevisionConflict`.
    """

    path = Path(path)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with FileLock(lock_path, timeout=timeout):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path.name} must contain a JSON object")
        revision = payload.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise ValueError(f"{path.name} revision must be a non-negative integer")
        if expected_revision is not None and revision != expected_revision:
            raise RevisionConflict(
                f"revision conflict for {path}: expected {expected_revision}, found {revision}"
            )
        updated = updater(payload)
        if updated is None:
            updated = payload
        if not isinstance(updated, dict):
            raise TypeError("updater must return a JSON object or None")
        updated["revision"] = revision + 1
        atomic_write(path, json.dumps(updated, ensure_ascii=False, indent=2) + "\n")
        return updated
