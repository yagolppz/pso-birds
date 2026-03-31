"""Motor PSO y coordinacion directa del vuelo del enjambre."""

from __future__ import annotations

import random
import time

from .config import SearchSpaceConfig, SwarmConfig
from .logging import StructuredLogger, get_project_logger
from .particle import BirdParticle, Vector
from .results import FlightMetrics, FlightResult
from .swarm import FlockTreasure, SwarmHistory
from .types import FitnessEvaluator, ObjectiveDefinition, ObjectiveFunction


def _measure_crumbs(arguments: tuple[ObjectiveFunction, Vector]) -> float:
    objective, position = arguments
    return objective(position)


class BirdSwarmOptimizer:
    """PSO explicado como una bandada de pajaritos que busca migas."""

    def __init__(
        self,
        swarm_config: SwarmConfig,
        search_space: SearchSpaceConfig,
        evaluator: FitnessEvaluator,
        logger: StructuredLogger | None = None,
    ) -> None:
        self.swarm_config = swarm_config
        self.search_space = search_space
        self.evaluator = evaluator
        self.logger = logger
        self.project_logger = get_project_logger()
        self.random = random.Random(swarm_config.random_seed)

    def run(self, objective: ObjectiveDefinition, include_history: bool = True) -> FlightResult:
        birds = self._create_flock()
        history = SwarmHistory() if include_history else None
        total_start = time.perf_counter()
        total_evaluation_seconds = 0.0
        total_update_seconds = 0.0

        self.project_logger.info(
            "Inicio PSO | objective=%s | dimensions=%d | birds=%d | flights=%d | mode=%s | seed=%d | w=%.4f | c1=%.4f | c2=%.4f",
            objective.name,
            self.search_space.dimensions,
            self.swarm_config.birds,
            self.swarm_config.flights,
            self.evaluator.mode,
            self.swarm_config.random_seed,
            self.swarm_config.inertia,
            self.swarm_config.cognitive_weight,
            self.swarm_config.social_weight,
        )

        first_iteration_start = time.perf_counter()
        treasure, first_evaluation = self._measure_and_update_memories(birds, objective)
        first_total = time.perf_counter() - first_iteration_start
        first_overhead = max(0.0, first_total - first_evaluation)
        total_evaluation_seconds += first_evaluation
        if history is not None:
            history.remember(
                0,
                treasure.position,
                treasure.crumbs,
                self._average_remembered_crumbs(birds),
                first_evaluation,
                0.0,
                first_overhead,
                [list(bird.position) for bird in birds],
            )
        self._log_flight(0, treasure, first_evaluation, 0.0, first_total, first_overhead)

        flights_completed = 0
        for flight_number in range(1, self.swarm_config.flights + 1):
            flights_completed = flight_number
            iteration_start = time.perf_counter()

            update_start = time.perf_counter()
            self._move_flock(birds, treasure)
            update_seconds = time.perf_counter() - update_start
            total_update_seconds += update_seconds

            treasure, evaluation_seconds = self._measure_and_update_memories(birds, objective, treasure)
            total_evaluation_seconds += evaluation_seconds
            iteration_total = time.perf_counter() - iteration_start
            overhead_seconds = max(0.0, iteration_total - evaluation_seconds - update_seconds)

            if history is not None:
                history.remember(
                    flight_number,
                    treasure.position,
                    treasure.crumbs,
                    self._average_remembered_crumbs(birds),
                    evaluation_seconds,
                    update_seconds,
                    overhead_seconds,
                    [list(bird.position) for bird in birds],
                )
            self._log_flight(flight_number, treasure, evaluation_seconds, update_seconds, iteration_total, overhead_seconds)

            threshold = self.swarm_config.stop_when_crumbs_below
            if threshold is not None and treasure.crumbs <= threshold:
                break

        total_seconds = time.perf_counter() - total_start
        result = FlightResult(
            best_position=list(treasure.position),
            best_crumbs=treasure.crumbs,
            flights_completed=flights_completed,
            history=history,
            metrics=FlightMetrics(
                total_seconds=total_seconds,
                evaluation_seconds=total_evaluation_seconds,
                update_seconds=total_update_seconds,
                overhead_seconds=max(0.0, total_seconds - total_evaluation_seconds - total_update_seconds),
            ),
            evaluator_mode=self.evaluator.mode,
        )
        self.project_logger.info(
            "Fin PSO | best_fitness=%.10e | total=%.4fs",
            result.best_crumbs,
            total_seconds,
        )
        if self.logger is not None:
            self.logger.log_event("flight_result", result.as_dict())
        return result

    def _create_flock(self) -> list[BirdParticle]:
        birds: list[BirdParticle] = []
        for _ in range(self.swarm_config.birds):
            position = [self._random_coordinate() for _ in range(self.search_space.dimensions)]
            velocity = [self._random_velocity() for _ in range(self.search_space.dimensions)]
            birds.append(
                BirdParticle(
                    position=position,
                    velocity=velocity,
                    remembered_best_position=list(position),
                    remembered_best_crumbs=float("inf"),
                )
            )
        return birds

    def _measure_and_update_memories(
        self,
        birds: list[BirdParticle],
        objective: ObjectiveDefinition,
        previous_treasure: FlockTreasure | None = None,
    ) -> tuple[FlockTreasure, float]:
        report = self.evaluator.evaluate_many([list(bird.position) for bird in birds], objective)
        treasure = previous_treasure

        for bird, crumbs in zip(birds, report.crumbs_by_bird, strict=True):
            if crumbs < bird.remembered_best_crumbs:
                bird.remembered_best_crumbs = crumbs
                bird.remembered_best_position = list(bird.position)
            if treasure is None or crumbs < treasure.crumbs:
                treasure = FlockTreasure(position=list(bird.position), crumbs=crumbs)

        assert treasure is not None
        return treasure, report.elapsed_seconds

    def _move_flock(self, birds: list[BirdParticle], treasure: FlockTreasure) -> None:
        speed_limit = (self.search_space.upper_bound - self.search_space.lower_bound) * self.swarm_config.velocity_limit_factor
        for bird in birds:
            next_velocity: Vector = []
            next_position: Vector = []
            for index, coordinate in enumerate(bird.position):
                inertia_push = self.swarm_config.inertia * bird.velocity[index]
                memory_pull = (
                    self.swarm_config.cognitive_weight
                    * self.random.random()
                    * (bird.remembered_best_position[index] - coordinate)
                )
                flock_pull = (
                    self.swarm_config.social_weight
                    * self.random.random()
                    * (treasure.position[index] - coordinate)
                )
                unclamped_velocity = inertia_push + memory_pull + flock_pull
                new_velocity = max(-speed_limit, min(speed_limit, unclamped_velocity))
                next_velocity.append(new_velocity)
                next_position.append(self._clamp_to_park(coordinate + new_velocity))
            bird.velocity = next_velocity
            bird.position = next_position

    def _average_remembered_crumbs(self, birds: list[BirdParticle]) -> float:
        return sum(bird.remembered_best_crumbs for bird in birds) / len(birds)

    def _random_coordinate(self) -> float:
        return self.random.uniform(self.search_space.lower_bound, self.search_space.upper_bound)

    def _random_velocity(self) -> float:
        speed_limit = (self.search_space.upper_bound - self.search_space.lower_bound) * self.swarm_config.velocity_limit_factor
        return self.random.uniform(-speed_limit, speed_limit)

    def _clamp_to_park(self, coordinate: float) -> float:
        return max(self.search_space.lower_bound, min(self.search_space.upper_bound, coordinate))

    def _log_flight(
        self,
        flight_number: int,
        treasure: FlockTreasure,
        evaluation_seconds: float,
        update_seconds: float,
        iteration_total: float,
        overhead_seconds: float,
    ) -> None:
        self.project_logger.info(
            "Iter %d/%d | best=%.6e | eval=%.4fs | update=%.4fs | total=%.4fs | overhead=%.4fs",
            flight_number,
            self.swarm_config.flights,
            treasure.crumbs,
            evaluation_seconds,
            update_seconds,
            iteration_total,
            overhead_seconds,
        )
        if self.logger is None:
            return
        self.logger.log_event(
            "flight_snapshot",
            {
                "flight_number": flight_number,
                "treasure_position": list(treasure.position),
                "treasure_crumbs": treasure.crumbs,
                "evaluation_seconds": evaluation_seconds,
                "update_seconds": update_seconds,
                "iteration_total_seconds": iteration_total,
                "overhead_seconds": overhead_seconds,
                "mode": self.evaluator.mode,
            },
        )


def _swarm_for_repetition(swarm: SwarmConfig, repetition: int) -> SwarmConfig:
    return SwarmConfig(
        birds=swarm.birds,
        flights=swarm.flights,
        inertia=swarm.inertia,
        cognitive_weight=swarm.cognitive_weight,
        social_weight=swarm.social_weight,
        random_seed=swarm.random_seed + repetition,
        stop_when_crumbs_below=swarm.stop_when_crumbs_below,
        velocity_limit_factor=swarm.velocity_limit_factor,
    )


def _swarm_with_overrides(swarm: SwarmConfig, values: dict[str, float | int]) -> SwarmConfig:
    return SwarmConfig(
        birds=int(values.get("birds", swarm.birds)),
        flights=int(values.get("flights", swarm.flights)),
        inertia=float(values.get("inertia", swarm.inertia)),
        cognitive_weight=float(values.get("cognitive_weight", swarm.cognitive_weight)),
        social_weight=float(values.get("social_weight", swarm.social_weight)),
        random_seed=int(values.get("random_seed", swarm.random_seed)),
        stop_when_crumbs_below=swarm.stop_when_crumbs_below,
        velocity_limit_factor=float(values.get("velocity_limit_factor", swarm.velocity_limit_factor)),
    )
