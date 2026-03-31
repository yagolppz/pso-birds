"""Logging del parque de pajaritos."""

from __future__ import annotations

import json
import logging
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


PROJECT_LOGGER_NAME = "PSO_Birds"
_PROJECT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


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


def configure_project_logger(log_file: Path | str | None = None, level: int = logging.INFO) -> logging.Logger:
    """Configura el logger estandar del proyecto para consola y fichero opcional."""

    logger = logging.getLogger(PROJECT_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter(_PROJECT_LOG_FORMAT)

    logger.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_project_logger() -> logging.Logger:
    """Devuelve el logger del proyecto, configurandolo si aun no existe."""

    logger = logging.getLogger(PROJECT_LOGGER_NAME)
    if not logger.handlers:
        configure_project_logger()
    return logger
