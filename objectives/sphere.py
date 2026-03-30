"""Parque suave donde las migas apuntan al origen."""

from __future__ import annotations

import time
import numpy as np

from core.particle import Vector
from core.types import ObjectiveDefinition


def sphere(position: Vector) -> float:
    return sum(coordinate * coordinate for coordinate in position)


def sphere_numpy(positions: np.ndarray) -> np.ndarray:
    return np.sum(positions * positions, axis=1)


def sleepy_sphere(position: Vector) -> float:
    time.sleep(0.002)
    return sphere(position)


def sleepy_sphere_numpy(positions: np.ndarray) -> np.ndarray:
    time.sleep(0.002 * len(positions))
    return sphere_numpy(positions)


def sphere_definition() -> ObjectiveDefinition:
    return ObjectiveDefinition(
        name="sphere",
        description="Un parque suave cuyo tesoro esta en el origen.",
        scalar_function=sphere,
        vectorized_function=sphere_numpy,
        suggested_lower_bound=-5.12,
        suggested_upper_bound=5.12,
    )


def sleepy_sphere_definition() -> ObjectiveDefinition:
    return ObjectiveDefinition(
        name="sleepy_sphere",
        description="Un parque artificialmente lento para estudiar evaluacion paralela.",
        scalar_function=sleepy_sphere,
        vectorized_function=sleepy_sphere_numpy,
        suggested_lower_bound=-5.12,
        suggested_upper_bound=5.12,
    )
