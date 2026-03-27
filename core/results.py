"""Resultados, metricas y reportes del vuelo."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .particle import Vector
from .swarm import SwarmHistory


@dataclass(slots=True)
class EvaluationReport:
    """Migas medidas para todos los pajaritos en un vuelo."""

    crumbs_by_bird: list[float]
    elapsed_seconds: float


@dataclass(slots=True)
class FlightMetrics:
    """Tiempo total, de comida, de movimiento y de coordinacion."""

    total_seconds: float
    evaluation_seconds: float
    update_seconds: float
    overhead_seconds: float


@dataclass(slots=True)
class FlightResult:
    """Resultado final de una salida de la bandada."""

    best_position: Vector
    best_crumbs: float
    flights_completed: int
    history: SwarmHistory | None
    metrics: FlightMetrics
    evaluator_mode: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class BenchmarkTimingSummary:
    total_seconds_mean: float
    evaluation_seconds_mean: float
    update_seconds_mean: float
    overhead_seconds_mean: float


@dataclass(slots=True)
class BenchmarkResult:
    """Resumen agregado para varias repeticiones."""

    mode: str
    objective_name: str
    repetitions: int
    best_crumbs_mean: float
    timings: BenchmarkTimingSummary
    best_run: FlightResult

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
