"""V1: evaluacion de fitness con ThreadPoolExecutor."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from core.particle import Vector
from core.types import ObjectiveDefinition
from .base import BaseFitnessEvaluator
from .common import measure_crumbs


class V1ThreadingEvaluator(BaseFitnessEvaluator):
    """Cuenta las migas de varios pajaritos en paralelo usando hilos."""

    mode = "thread"

    def __init__(self, workers: int | None = None) -> None:
        self.workers = workers

    def _evaluate_crumbs(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            return list(
                executor.map(
                    measure_crumbs,
                    ((objective.scalar_function, position) for position in positions),
                )
            )
