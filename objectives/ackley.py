"""Parque con niebla donde el tesoro exige coordinacion fina."""

from __future__ import annotations

import math

import numpy as np

from core.particle import Vector
from core.types import ObjectiveDefinition


def ackley(position: Vector) -> float:
    dimensions = len(position)
    squared_mean = sum(coordinate * coordinate for coordinate in position) / dimensions
    cosine_mean = sum(math.cos(2 * math.pi * coordinate) for coordinate in position) / dimensions
    return -20 * math.exp(-0.2 * math.sqrt(squared_mean)) - math.exp(cosine_mean) + 20 + math.e


def ackley_numpy(positions: np.ndarray) -> np.ndarray:
    squared_mean = np.mean(positions * positions, axis=1)
    cosine_mean = np.mean(np.cos(2 * np.pi * positions), axis=1)
    return -20 * np.exp(-0.2 * np.sqrt(squared_mean)) - np.exp(cosine_mean) + 20 + np.e


def ackley_definition() -> ObjectiveDefinition:
    return ObjectiveDefinition(
        name="ackley",
        description="Un parque con niebla donde el tesoro esta escondido en calma.",
        scalar_function=ackley,
        vectorized_function=ackley_numpy,
        suggested_lower_bound=-32.768,
        suggested_upper_bound=32.768,
    )
