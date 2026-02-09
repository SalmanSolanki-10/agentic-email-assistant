from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Set


class ProcessedMessageStore:
    """
    Tracks processed Message-IDs to prevent duplicate replies across restarts.

    Stored as JSONL: one message id per line {"message_id": "...", "ts": "..."}.
    """

    def __init__(self, path: str):
        self._path = Path(path)
        self._lock = Lock()
        self._ids: Set[str] = set()
        self._load()

    def _load(self) -> None:
        with self._lock:
            self._ids.clear()
            if not self._path.exists():
                return
            try:
                for line in self._path.read_text(errors="ignore").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        mid = obj.get("message_id")
                        if mid:
                            self._ids.add(mid)
                    except Exception:
                        # Ignore malformed lines
                        continue
            except Exception:
                # If file is unreadable, start clean
                self._ids.clear()

    def contains(self, message_id: str) -> bool:
        with self._lock:
            return message_id in self._ids

    def add(self, message_id: str, ts: str) -> None:
        with self._lock:
            if message_id in self._ids:
                return
            self._ids.add(message_id)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"message_id": message_id, "ts": ts}) + "\n")
