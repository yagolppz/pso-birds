"""V4: evaluacion de fitness vectorizada con NumPy."""

from __future__ import annotations

import numpy as np

from core.particle import Vector
from core.types import ObjectiveDefinition
from .base import BaseFitnessEvaluator


class V4NumpyEvaluator(BaseFitnessEvaluator):
    """Cuenta las migas de toda la bandada usando una matriz vectorizada."""

    mode = "numpy"

    def _evaluate_crumbs(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        matrix = np.asarray(positions, dtype=float)
        return objective.vectorized_function(matrix).astype(float).tolist()
