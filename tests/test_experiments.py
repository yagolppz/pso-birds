import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.benchmark import compare_benchmark, grid_search_benchmark
from core.config import ArtifactConfig, BenchmarkConfig, SearchSpaceConfig, SwarmConfig
from objectives import get_objective


class ExperimentTests(unittest.TestCase):
    def test_comparacion_devuelve_metricas_consistentes(self) -> None:
        config = BenchmarkConfig(
            objective=get_objective("sphere"),
            swarm=SwarmConfig(birds=12, flights=10, random_seed=5),
            search_space=SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12),
            evaluator_mode="sequential",
            repetitions=2,
            include_history=False,
        )

        comparison = compare_benchmark(config, candidate_mode="thread", workers=2)

        self.assertEqual(comparison["baseline"].mode, "sequential")
        self.assertEqual(comparison["candidate"].mode, "thread")
        self.assertGreater(comparison["speedup"], 0)

    def test_grid_search_y_persistencia_generan_artifactos(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            config = BenchmarkConfig(
                objective=get_objective("sphere"),
                swarm=SwarmConfig(birds=10, flights=6, random_seed=2),
                search_space=SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12),
                evaluator_mode="numpy",
                repetitions=1,
                include_history=True,
                artifacts=ArtifactConfig(output_directory=output_dir),
            )

            result = grid_search_benchmark(
                config,
                {
                    "birds": [8, 10],
                    "inertia": [0.5, 0.7],
                },
                mode="numpy",
                seeds=[2, 3],
            )

            self.assertEqual(len(result), 4)
            self.assertEqual(result[0]["seed_count"], 2)
            self.assertIn("w", result[0])
            self.assertIn("c1", result[0])
            self.assertIn("c2", result[0])
            self.assertIn("swarm_size", result[0])
            self.assertTrue((output_dir / "sphere" / "grid_search_numpy" / "grid_search.csv").exists())
            self.assertTrue((output_dir / "sphere" / "numpy" / "summary.json").exists())

    def test_benchmark_config_rechaza_workers_no_positivos(self) -> None:
        with self.assertRaisesRegex(ValueError, "workers debe ser positiva"):
            BenchmarkConfig(
                objective=get_objective("sphere"),
                swarm=SwarmConfig(birds=10, flights=6, random_seed=2),
                search_space=SearchSpaceConfig(dimensions=2, lower_bound=-5.12, upper_bound=5.12),
                evaluator_mode="thread",
                repetitions=1,
                workers=0,
            )


if __name__ == "__main__":
    unittest.main()
