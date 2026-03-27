"""V0: evaluacion secuencial baseline del fitness."""

from __future__ import annotations

from core.particle import Vector
from core.types import ObjectiveDefinition
from .base import BaseFitnessEvaluator


class V0SequentialEvaluator(BaseFitnessEvaluator):
    """Cuenta las migas de un pajarito tras otro, sin paralelismo."""

    mode = "sequential"

    def _evaluate_crumbs(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        return [objective.scalar_function(position) for position in positions]
