"""Seleccion y fachada de estrategias de evaluacion."""

from __future__ import annotations

from core.types import EVALUATION_MODES, FitnessEvaluator

from .registry import FITNESS_EVALUATOR_REGISTRY


class CrumbEvaluator:
    """Fachada compatible que delega en una estrategia registrada."""

    def __init__(self, mode: str = "sequential", workers: int | None = None) -> None:
        self.mode = mode
        self.workers = workers
        self._strategy = build_fitness_evaluator(mode=mode, workers=workers)

    def evaluate_many(self, positions, objective):
        return self._strategy.evaluate_many(positions, objective)


def build_fitness_evaluator(mode: str = "sequential", workers: int | None = None) -> FitnessEvaluator:
    """Construye una estrategia de fitness a partir de su nombre publico."""

    try:
        evaluator_class = FITNESS_EVALUATOR_REGISTRY[mode]
    except KeyError as error:
        available = ", ".join(sorted(EVALUATION_MODES))
        raise ValueError(f"Modo de evaluacion desconocido: {mode}. Opciones: {available}") from error

    if workers is not None and workers <= 0:
        raise ValueError("La cantidad de workers debe ser positiva.")

    if mode in {"thread", "process", "asyncio"}:
        return evaluator_class(workers=workers)
    return evaluator_class()
