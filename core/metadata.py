"""Metadatos de reproducibilidad para ejecuciones de PSO-BIRDS."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _run_git_command(arguments: list[str]) -> str | None:
    try:
        root = Path(__file__).resolve().parents[1]
        output = subprocess.check_output(
            ["git", *arguments],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return output.strip()
    except Exception:
        return None


def _git_commit_hash() -> str | None:
    return _run_git_command(["rev-parse", "HEAD"])


def _git_branch() -> str | None:
    return _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])


def _git_dirty() -> bool | None:
    status = _run_git_command(["status", "--porcelain"])
    if status is None:
        return False
    return bool(status.strip())


def build_reproducibility_metadata(context: dict[str, Any] | None = None) -> dict[str, object]:
    """Construye metadata reproducible para resultados y artefactos."""

    context = context or {}
    metadata: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit_hash() or "unknown",
        "git_branch": _git_branch() or "unknown",
        "repo_dirty": _git_dirty(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count() or 1,
    }

    for key in ("seed", "mode", "workers"):
        if key in context:
            metadata[key] = context[key]

    return metadata
