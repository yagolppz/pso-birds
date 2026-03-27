"""Piezas basicas del parque: cada pajarito por separado."""

from __future__ import annotations

from dataclasses import dataclass


Vector = list[float]


@dataclass(slots=True)
class BirdParticle:
    """Cada particula es un pajarito con posicion, velocidad y memoria."""

    position: Vector
    velocity: Vector
    remembered_best_position: Vector
    remembered_best_crumbs: float
