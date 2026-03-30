"""Persistencia simple para resultados del banco de pruebas."""

from __future__ import annotations

import csv
import json

from pathlib import Path

from .config import ArtifactConfig
from .results import BenchmarkResult, FlightResult


class ArtifactWriter:
    """Guarda resultados en formatos simples para la practica."""

    def __init__(self, config: ArtifactConfig) -> None:
        self.config = config

    def prepare_run_directory(self, objective_name: str, mode: str, repetition: int) -> Path | None:
        if self.config.output_directory is None:
            return None
        directory = self.config.output_directory / objective_name / mode / f"run_{repetition:03d}"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write_run_artifacts(self, run: FlightResult, objective_name: str, mode: str, repetition: int) -> None:
        directory = self.prepare_run_directory(objective_name, mode, repetition)
        if directory is None:
            return
        payload = run.as_dict()
        if self.config.save_json:
            self._write_json(directory / "result.json", payload)
        if self.config.save_yaml:
            self._write_yaml(directory / "result.yaml", payload)
        if self.config.save_csv and run.history is not None:
            self._write_csv(directory / "history.csv", run.history.as_records())

    def write_summary_artifacts(self, summary: BenchmarkResult, objective_name: str, mode: str) -> None:
        if self.config.output_directory is None:
            return
        directory = self.config.output_directory / objective_name / mode
        directory.mkdir(parents=True, exist_ok=True)
        if self.config.save_json:
            self._write_json(directory / "summary.json", summary.as_dict())
        if self.config.save_yaml:
            self._write_yaml(directory / "summary.yaml", summary.as_dict())

    def write_comparison_artifacts(self, comparison: dict[str, object], objective_name: str, candidate_mode: str) -> None:
        if self.config.output_directory is None:
            return
        directory = self.config.output_directory / objective_name / f"compare_sequential_vs_{candidate_mode}"
        directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "baseline": comparison["baseline"].as_dict(),
            "candidate": comparison["candidate"].as_dict(),
            "speedup": comparison["speedup"],
        }
        if self.config.save_json:
            self._write_json(directory / "comparison.json", payload)
        if self.config.save_yaml:
            self._write_yaml(directory / "comparison.yaml", payload)

    def write_grid_search_artifacts(self, rows: list[dict[str, object]], objective_name: str, mode: str) -> None:
        if self.config.output_directory is None:
            return
        directory = self.config.output_directory / objective_name / f"grid_search_{mode}"
        directory.mkdir(parents=True, exist_ok=True)
        if self.config.save_json:
            self._write_json(directory / "grid_search.json", {"rows": rows})
        if self.config.save_yaml:
            self._write_yaml(directory / "grid_search.yaml", {"rows": rows})
        if self.config.save_csv:
            self._write_csv(directory / "grid_search.csv", rows)

    def _write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    def _write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _write_yaml(self, path: Path, payload: dict[str, object]) -> None:
        path.write_text(self._to_yaml(payload), encoding="utf-8")

    def _to_yaml(self, value: object, depth: int = 0) -> str:
        indent = "  " * depth
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}{key}:")
                    lines.append(self._to_yaml(item, depth + 1))
                else:
                    lines.append(f"{indent}{key}: {self._yaml_scalar(item)}")
            return "\n".join(lines)
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}-")
                    lines.append(self._to_yaml(item, depth + 1))
                else:
                    lines.append(f"{indent}- {self._yaml_scalar(item)}")
            return "\n".join(lines)
        return f"{indent}{self._yaml_scalar(value)}"

    def _yaml_scalar(self, value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(str(value), ensure_ascii=True)
