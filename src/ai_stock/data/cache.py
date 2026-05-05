"""Disk cache to avoid hammering free APIs and enable offline reruns."""
from __future__ import annotations

import json
import pickle
import time
from pathlib import Path
from typing import Any

from ai_stock.config import REPO_ROOT


class DiskCache:
    def __init__(self, dir_: str | Path, ttl_hours: float = 18.0) -> None:
        self.root = (REPO_ROOT / dir_) if not Path(dir_).is_absolute() else Path(dir_)
        self.root.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600

    def _path(self, key: str, ext: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.root / f"{safe}.{ext}"

    def get_json(self, key: str) -> Any | None:
        p = self._path(key, "json")
        if not p.exists() or time.time() - p.stat().st_mtime > self.ttl_seconds:
            return None
        try:
            return json.loads(p.read_text())
        except Exception:
            return None

    def set_json(self, key: str, value: Any) -> None:
        self._path(key, "json").write_text(json.dumps(value, default=str))

    def get_pickle(self, key: str) -> Any | None:
        p = self._path(key, "pkl")
        if not p.exists() or time.time() - p.stat().st_mtime > self.ttl_seconds:
            return None
        try:
            return pickle.loads(p.read_bytes())
        except Exception:
            return None

    def set_pickle(self, key: str, value: Any) -> None:
        self._path(key, "pkl").write_bytes(pickle.dumps(value))
