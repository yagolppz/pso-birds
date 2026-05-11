import unittest

import numpy as np

from core.config import SearchSpaceConfig, SwarmConfig
from core.pso import BirdSwarmOptimizer
from core.types import ObjectiveDefinition
from objectives import get_objective
from parallel import CrumbEvaluator, build_fitness_evaluator


class EngineTests(unittest.TestCase):
    def _build_optimizer(
        self,
        *,
        seed: int,
        birds: int = 20,
        flights: int = 18,
        dimensions: int = 2,
        lower_bound: float = -5.12,
        upper_bound: float = 5.12,
        mode: str = "sequential",
    ) -> BirdSwarmOptimizer:
        return BirdSwarmOptimizer(
            swarm_config=SwarmConfig(
                birds=birds,
                flights=flights,
                inertia=0.7,
                cognitive_weight=1.7,
                social_weight=1.7,
                random_seed=seed,
            ),
            search_space=SearchSpaceConfig(
                dimensions=dimensions,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            ),
            evaluator=CrumbEvaluator(mode=mode),
        )

    def test_bandada_mejora_en_el_parque_simple(self) -> None:
        objective = get_objective("sphere")
        optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(
                birds=25,
                flights=60,
                inertia=0.6,
                cognitive_weight=1.5,
                social_weight=1.8,
                random_seed=11,
            ),
            search_space=SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12),
            evaluator=CrumbEvaluator(mode="sequential"),
        )

        result = optimizer.run(objective, include_history=True)

        self.assertLess(result.best_crumbs, 1e-2)
        self.assertIsNotNone(result.history)
        assert result.history is not None
        self.assertGreater(result.metrics.total_seconds, 0.0)
        self.assertGreaterEqual(result.metrics.evaluation_seconds, 0.0)
        self.assertGreaterEqual(
            result.history.snapshots[0].treasure_crumbs,
            result.history.snapshots[-1].treasure_crumbs,
        )

    def test_todos_los_pajaritos_se_mantienen_dentro_del_parque(self) -> None:
        objective = get_objective("sphere")
        optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(birds=10, flights=5, random_seed=3),
            search_space=SearchSpaceConfig(dimensions=3, lower_bound=-1.0, upper_bound=1.0),
            evaluator=CrumbEvaluator(mode="sequential"),
        )

        result = optimizer.run(objective, include_history=False)

        self.assertGreaterEqual(result.best_crumbs, 0.0)
        self.assertTrue(all(-1.0 <= coordinate <= 1.0 for coordinate in result.best_position))

    def test_numpy_y_asyncio_producen_resultados_validos(self) -> None:
        objective = get_objective("ackley")

        numpy_optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(birds=12, flights=12, random_seed=21),
            search_space=SearchSpaceConfig(dimensions=3, lower_bound=-5.0, upper_bound=5.0),
            evaluator=CrumbEvaluator(mode="numpy"),
        )
        asyncio_optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(birds=12, flights=12, random_seed=21),
            search_space=SearchSpaceConfig(dimensions=3, lower_bound=-5.0, upper_bound=5.0),
            evaluator=CrumbEvaluator(mode="asyncio", workers=4),
        )

        numpy_result = numpy_optimizer.run(objective, include_history=False)
        asyncio_result = asyncio_optimizer.run(objective, include_history=False)

        self.assertGreaterEqual(numpy_result.best_crumbs, 0.0)
        self.assertGreaterEqual(asyncio_result.best_crumbs, 0.0)

    def test_workers_invalidos_fallan_antes_de_construir_la_estrategia(self) -> None:
        with self.assertRaisesRegex(ValueError, "workers debe ser positiva"):
            build_fitness_evaluator(mode="thread", workers=0)

    def test_mismo_seed_produce_mismo_resultado(self) -> None:
        objective = get_objective("sphere")
        first_optimizer = self._build_optimizer(seed=19, flights=20)
        second_optimizer = self._build_optimizer(seed=19, flights=20)

        first_result = first_optimizer.run(objective, include_history=True)
        second_result = second_optimizer.run(objective, include_history=True)

        self.assertEqual(first_result.best_position, second_result.best_position)
        self.assertAlmostEqual(first_result.best_crumbs, second_result.best_crumbs, places=12)
        self.assertEqual(first_result.flights_completed, second_result.flights_completed)
        assert first_result.history is not None
        assert second_result.history is not None
        self.assertEqual(
            [snapshot.treasure_crumbs for snapshot in first_result.history.snapshots],
            [snapshot.treasure_crumbs for snapshot in second_result.history.snapshots],
        )

    def test_stop_after_stagnant_flights_none_preserva_comportamiento(self) -> None:
        objective = ObjectiveDefinition(
            name="constant",
            description="Objetivo constante para probar parada por estancamiento.",
            scalar_function=lambda position: 1.0,
            vectorized_function=lambda positions: np.full((positions.shape[0],), 1.0),
            suggested_lower_bound=-1.0,
            suggested_upper_bound=1.0,
        )
        optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(
                birds=8,
                flights=5,
                random_seed=13,
            ),
            search_space=SearchSpaceConfig(dimensions=2, lower_bound=-1.0, upper_bound=1.0),
            evaluator=CrumbEvaluator(mode="sequential"),
        )

        result = optimizer.run(objective, include_history=False)

        self.assertEqual(result.flights_completed, 5)

    def test_stop_after_stagnant_flights_detiene_antes_si_no_hay_mejora(self) -> None:
        objective = ObjectiveDefinition(
            name="constant",
            description="Objetivo constante que no mejora entre vuelos.",
            scalar_function=lambda position: 42.0,
            vectorized_function=lambda positions: np.full((positions.shape[0],), 42.0),
            suggested_lower_bound=-1.0,
            suggested_upper_bound=1.0,
        )
        optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(
                birds=8,
                flights=10,
                stop_after_stagnant_flights=2,
                random_seed=17,
            ),
            search_space=SearchSpaceConfig(dimensions=2, lower_bound=-1.0, upper_bound=1.0),
            evaluator=CrumbEvaluator(mode="sequential"),
        )

        result = optimizer.run(objective, include_history=False)

        self.assertEqual(result.flights_completed, 2)

    def test_stop_when_crumbs_below_sigue_funcionando_con_stagnation(self) -> None:
        objective = ObjectiveDefinition(
            name="constant",
            description="Objetivo constante para probar el umbral de parada.",
            scalar_function=lambda position: 42.0,
            vectorized_function=lambda positions: np.full((positions.shape[0],), 42.0),
            suggested_lower_bound=-1.0,
            suggested_upper_bound=1.0,
        )
        optimizer = BirdSwarmOptimizer(
            swarm_config=SwarmConfig(
                birds=8,
                flights=10,
                stop_after_stagnant_flights=5,
                stop_when_crumbs_below=50.0,
                random_seed=23,
            ),
            search_space=SearchSpaceConfig(dimensions=2, lower_bound=-1.0, upper_bound=1.0),
            evaluator=CrumbEvaluator(mode="sequential"),
        )

        result = optimizer.run(objective, include_history=False)

        self.assertEqual(result.flights_completed, 1)

    def test_stop_after_stagnant_flights_valor_no_positivo_falla(self) -> None:
        with self.assertRaisesRegex(ValueError, "stop_after_stagnant_flights"):
            SwarmConfig(birds=5, flights=5, stop_after_stagnant_flights=0)

        with self.assertRaisesRegex(ValueError, "stop_after_stagnant_flights"):
            SwarmConfig(birds=5, flights=5, stop_after_stagnant_flights=-3)

    def test_historial_guarda_particulas_dentro_del_parque(self) -> None:
        objective = get_objective("sphere")
        optimizer = self._build_optimizer(
            seed=13,
            birds=12,
            flights=10,
            dimensions=2,
            lower_bound=-1.5,
            upper_bound=1.5,
        )

        result = optimizer.run(objective, include_history=True)

        assert result.history is not None
        for snapshot in result.history.snapshots:
            self.assertIsNotNone(snapshot.particle_positions)
            assert snapshot.particle_positions is not None
            for position in snapshot.particle_positions:
                self.assertTrue(all(-1.5 <= coordinate <= 1.5 for coordinate in position))

    def test_gbest_no_empeora_durante_el_vuelo(self) -> None:
        objective = get_objective("sphere")
        optimizer = self._build_optimizer(seed=23, birds=16, flights=16)

        result = optimizer.run(objective, include_history=True)

        assert result.history is not None
        treasure_crumbs = [snapshot.treasure_crumbs for snapshot in result.history.snapshots]
        for previous, current in zip(treasure_crumbs, treasure_crumbs[1:]):
            self.assertLessEqual(current, previous + 1e-12)

    def test_sphere_mejora_claramente_desde_el_inicio(self) -> None:
        objective = get_objective("sphere")
        optimizer = self._build_optimizer(seed=29, birds=24, flights=25)

        result = optimizer.run(objective, include_history=True)

        assert result.history is not None
        initial_best = result.history.snapshots[0].treasure_crumbs
        final_best = result.history.snapshots[-1].treasure_crumbs
        self.assertLess(final_best, initial_best)
        self.assertLessEqual(final_best, initial_best * 0.25)


if __name__ == "__main__":
    unittest.main()
