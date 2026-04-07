"""Base comun para estrategias de evaluacion de fitness."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from core.particle import Vector
from core.results import EvaluationReport
from core.types import ObjectiveDefinition


class BaseFitnessEvaluator(ABC):
    """Cronometra la evaluacion de forma uniforme para todas las estrategias."""

    mode: str

    def evaluate_many(self, positions: list[Vector], objective: ObjectiveDefinition) -> EvaluationReport:
        start_time = time.perf_counter()
        crumbs = self._evaluate_crumbs(positions, objective)
        return EvaluationReport(crumbs_by_bird=crumbs, elapsed_seconds=time.perf_counter() - start_time)

    @abstractmethod
    def _evaluate_crumbs(
        self,
        positions: list[Vector],
        objective: ObjectiveDefinition,
    ) -> list[float]:
        """Cuenta las migas sin preocuparse del cronometro."""
