"""Logging del parque de pajaritos."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


class StructuredLogger(Protocol):
    """Contrato para registrar eventos del vuelo."""

    def log_event(self, event: str, payload: dict[str, object]) -> None:
        ...


class JsonLinesBirdLogger:
    """Escribe cada vuelo como una linea JSON."""

    def __init__(self, path: Path | None) -> None:
        self.path = path

    @classmethod
    def for_directory(cls, directory: Path | None, enabled: bool) -> "JsonLinesBirdLogger":
        if not enabled or directory is None:
            return cls(path=None)
        directory.mkdir(parents=True, exist_ok=True)
        return cls(directory / "flights.jsonl")

    def log_event(self, event: str, payload: dict[str, object]) -> None:
        if self.path is None:
            return
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")
