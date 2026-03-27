"""Parque con muchas migas falsas que distraen a los pajaritos."""

from __future__ import annotations

import math

import numpy as np

from core.particle import Vector
from core.types import ObjectiveDefinition


def rastrigin(position: Vector) -> float:
    dimensions = len(position)
    return 10 * dimensions + sum(
        coordinate * coordinate - 10 * math.cos(2 * math.pi * coordinate)
        for coordinate in position
    )


def rastrigin_numpy(positions: np.ndarray) -> np.ndarray:
    dimensions = positions.shape[1]
    return 10 * dimensions + np.sum(
        positions * positions - 10 * np.cos(2 * np.pi * positions),
        axis=1,
    )


def rastrigin_definition() -> ObjectiveDefinition:
    return ObjectiveDefinition(
        name="rastrigin",
        description="Un parque lleno de migas falsas que distraen a la bandada.",
        scalar_function=rastrigin,
        vectorized_function=rastrigin_numpy,
        suggested_lower_bound=-5.12,
        suggested_upper_bound=5.12,
    )
