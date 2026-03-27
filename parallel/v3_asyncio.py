"""V3: evaluacion de fitness coordinada con asyncio."""

from __future__ import annotations

import asyncio

from core.particle import Vector
from core.types import ObjectiveDefinition
from .base import BaseFitnessEvaluator


class V3AsyncioEvaluator(BaseFitnessEvaluator):
    """Cuenta las migas con tareas asíncronas y latencia simulada."""

    mode = "asyncio"

    def __init__(self, workers: int | None = None, latency_seconds: float = 0.0) -> None:
        self.workers = workers
        self.latency_seconds = latency_seconds

    def _evaluate_crumbs(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        return asyncio.run(self._evaluate_asyncio(positions, objective))

    async def _evaluate_asyncio(
        self,
        positions: list[Vector],
        objective: ObjectiveDefinition,
    ) -> list[float]:
        semaphore = asyncio.Semaphore(self.workers or len(positions) or 1)

        async def count_crumbs(position: Vector) -> float:
            async with semaphore:
                await asyncio.sleep(self.latency_seconds)
                return objective.scalar_function(position)

        return list(await asyncio.gather(*(count_crumbs(position) for position in positions)))
