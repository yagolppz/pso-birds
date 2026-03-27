"""Tipos y contratos compartidos del parque."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

import numpy as np

from .particle import Vector
from .results import EvaluationReport


ObjectiveFunction = Callable[[Vector], float]
VectorizedObjectiveFunction = Callable[[np.ndarray], np.ndarray]
EVALUATION_MODES = {"sequential", "thread", "process", "asyncio", "numpy"}


@dataclass(frozen=True, slots=True)
class ObjectiveDefinition:
    """Describe un parque y la regla para contar migas."""

    name: str
    description: str
    scalar_function: ObjectiveFunction
    vectorized_function: VectorizedObjectiveFunction
    suggested_lower_bound: float
    suggested_upper_bound: float


class FitnessEvaluator(Protocol):
    """Contrato para contar migas sin acoplar el motor a una estrategia concreta."""

    mode: str

    def evaluate_many(self, positions: list[Vector], objective: ObjectiveDefinition) -> EvaluationReport:
        ...
