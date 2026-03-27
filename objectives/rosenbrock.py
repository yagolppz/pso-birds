"""Parque con un valle estrecho que cuesta seguir en grupo."""

from __future__ import annotations

import numpy as np

from core.particle import Vector
from core.types import ObjectiveDefinition


def rosenbrock(position: Vector) -> float:
    return sum(
        100 * (position[index + 1] - position[index] ** 2) ** 2
        + (1 - position[index]) ** 2
        for index in range(len(position) - 1)
    )


def rosenbrock_numpy(positions: np.ndarray) -> np.ndarray:
    left = positions[:, :-1]
    right = positions[:, 1:]
    return np.sum(100 * (right - left * left) ** 2 + (1 - left) ** 2, axis=1)


def rosenbrock_definition() -> ObjectiveDefinition:
    return ObjectiveDefinition(
        name="rosenbrock",
        description="Un parque con un valle estrecho y dificil de seguir.",
        scalar_function=rosenbrock,
        vectorized_function=rosenbrock_numpy,
        suggested_lower_bound=-2.048,
        suggested_upper_bound=2.048,
    )
