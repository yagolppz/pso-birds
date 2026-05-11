"""V2: evaluacion de fitness con ProcessPoolExecutor."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import math

from core.particle import Vector
from core.types import ObjectiveDefinition
from .base import BaseFitnessEvaluator
from .common import measure_crumbs, measure_crumbs_batch


class V2MultiprocessingEvaluator(BaseFitnessEvaluator):
    """Cuenta las migas de varios pajaritos en paralelo usando procesos."""

    mode = "process"

    def __init__(self, workers: int | None = None, batch_size: int | None = None) -> None:
        self.workers = workers
        self.batch_size = batch_size

    def _evaluate_crumbs(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        if self.batch_size is None:
            return self._evaluate_unbatched(positions, objective)
        return self._evaluate_batched(positions, objective)

    def _evaluate_unbatched(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            return list(
                executor.map(
                    measure_crumbs,
                    ((objective.scalar_function, position) for position in positions),
                )
            )

    def _evaluate_batched(self, positions: list[Vector], objective: ObjectiveDefinition) -> list[float]:
        batches = self._batch_positions(positions, self.batch_size or 1)
        batch_arguments = [(objective.scalar_function, batch) for batch in batches]
        
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            batch_results = list(executor.map(measure_crumbs_batch, batch_arguments))
        
        all_crumbs: list[float] = []
        for batch_crumbs in batch_results:
            all_crumbs.extend(batch_crumbs)
        
        return all_crumbs

    def _batch_positions(self, positions: list[Vector], batch_size: int) -> list[list[Vector]]:
        """Divide posiciones en lotes de tamaño batch_size."""
        if batch_size <= 0:
            batch_size = 1
        num_batches = max(1, math.ceil(len(positions) / batch_size))
        batch_size = max(1, math.ceil(len(positions) / num_batches))
        batches: list[list[Vector]] = []
        for i in range(0, len(positions), batch_size):
            batches.append(positions[i : i + batch_size])
        return batches
