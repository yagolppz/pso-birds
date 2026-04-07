import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.benchmark import compare_benchmark, grid_search_benchmark, run_benchmark
from core.config import ArtifactConfig, BenchmarkConfig, SearchSpaceConfig, SwarmConfig
from experiments.benchmark_suite import run_benchmark_suite
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
            self.assertTrue((output_dir / "sphere" / "numpy" / "run_000" / "animation_2d.gif").exists())
            self.assertTrue((output_dir / "sphere" / "numpy" / "run_000" / "animation_3d.gif").exists())
            self.assertFalse((output_dir / "sphere" / "numpy" / "run_000" / "swarm_2d_frames").exists())

    def test_benchmark_3d_genera_animation_gif(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            summary = run_benchmark(
                BenchmarkConfig(
                    objective=get_objective("sphere"),
                    swarm=SwarmConfig(birds=8, flights=5, random_seed=4),
                    search_space=SearchSpaceConfig(dimensions=3, lower_bound=-5.12, upper_bound=5.12),
                    evaluator_mode="sequential",
                    repetitions=1,
                    include_history=True,
                    artifacts=ArtifactConfig(output_directory=output_dir),
                )
            )

            self.assertEqual(summary.mode, "sequential")
            self.assertTrue((output_dir / "sphere" / "sequential" / "run_000" / "animation_2d.gif").exists())
            self.assertTrue((output_dir / "sphere" / "sequential" / "run_000" / "animation_3d.gif").exists())
            self.assertFalse((output_dir / "sphere" / "sequential" / "run_000" / "swarm_3d_frames").exists())

    def test_suite_de_benchmarks_genera_resumen(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            rows = run_benchmark_suite(
                objective_names=["sphere"],
                dimensions=[2],
                modes=["sequential", "numpy"],
                birds=6,
                flights=4,
                repetitions=1,
                workers=None,
                seed=7,
                output_directory=Path(temporary_directory),
            )

            self.assertEqual(len(rows), 2)
            self.assertTrue((Path(temporary_directory) / "benchmark_suite" / "summary.csv").exists())
            self.assertIn("speedup_vs_sequential", rows[0])

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
