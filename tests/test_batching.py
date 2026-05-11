import unittest

from core.config import SearchSpaceConfig, SwarmConfig
from core.pso import BirdSwarmOptimizer
from objectives import get_objective
from parallel import CrumbEvaluator, build_fitness_evaluator


class BatchingTests(unittest.TestCase):
    def test_multiprocessing_with_batching_produces_same_results_as_sequential(self) -> None:
        objective = get_objective("sphere")
        search_space = SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12)
        swarm_config = SwarmConfig(birds=12, flights=8, random_seed=42)

        sequential_optimizer = BirdSwarmOptimizer(
            swarm_config=swarm_config,
            search_space=search_space,
            evaluator=CrumbEvaluator(mode="sequential"),
        )
        process_batched_optimizer = BirdSwarmOptimizer(
            swarm_config=swarm_config,
            search_space=search_space,
            evaluator=CrumbEvaluator(mode="process", workers=2, batch_size=3),
        )

        sequential_result = sequential_optimizer.run(objective, include_history=False)
        process_result = process_batched_optimizer.run(objective, include_history=False)

        self.assertAlmostEqual(sequential_result.best_crumbs, process_result.best_crumbs, places=12)
        self.assertEqual(sequential_result.best_position, process_result.best_position)

    def test_multiprocessing_with_different_batch_sizes_produces_same_results(self) -> None:
        objective = get_objective("sphere")
        search_space = SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12)
        swarm_config = SwarmConfig(birds=10, flights=6, random_seed=23)

        optimizer_batch_1 = BirdSwarmOptimizer(
            swarm_config=swarm_config,
            search_space=search_space,
            evaluator=CrumbEvaluator(mode="process", workers=2, batch_size=1),
        )
        optimizer_batch_5 = BirdSwarmOptimizer(
            swarm_config=swarm_config,
            search_space=search_space,
            evaluator=CrumbEvaluator(mode="process", workers=2, batch_size=5),
        )

        result_batch_1 = optimizer_batch_1.run(objective, include_history=False)
        result_batch_5 = optimizer_batch_5.run(objective, include_history=False)

        self.assertAlmostEqual(result_batch_1.best_crumbs, result_batch_5.best_crumbs, places=12)
        self.assertEqual(result_batch_1.best_position, result_batch_5.best_position)

    def test_build_fitness_evaluator_rejects_non_positive_batch_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "batch_size debe ser positivo"):
            build_fitness_evaluator(mode="process", workers=2, batch_size=0)

        with self.assertRaisesRegex(ValueError, "batch_size debe ser positivo"):
            build_fitness_evaluator(mode="process", workers=2, batch_size=-1)

    def test_multiprocessing_without_explicit_batch_size_still_works(self) -> None:
        objective = get_objective("sphere")
        search_space = SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12)
        swarm_config = SwarmConfig(birds=8, flights=4, random_seed=99)

        optimizer = BirdSwarmOptimizer(
            swarm_config=swarm_config,
            search_space=search_space,
            evaluator=CrumbEvaluator(mode="process", workers=2),
        )

        result = optimizer.run(objective, include_history=False)

        self.assertGreaterEqual(result.best_crumbs, 0.0)
        self.assertLess(result.best_crumbs, 100.0)

    def test_batch_size_validation_in_crumb_evaluator(self) -> None:
        with self.assertRaisesRegex(ValueError, "batch_size debe ser positivo"):
            CrumbEvaluator(mode="process", workers=2, batch_size=-5)


if __name__ == "__main__":
    unittest.main()
