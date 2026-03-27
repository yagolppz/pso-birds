"""Utilidades compartidas entre estrategias de evaluacion."""

from __future__ import annotations

from core.particle import Vector
from core.types import ObjectiveFunction


def measure_crumbs(arguments: tuple[ObjectiveFunction, Vector]) -> float:
    """Cuenta las migas de un pajarito en una posicion concreta."""

    objective, position = arguments
    return objective(position)
