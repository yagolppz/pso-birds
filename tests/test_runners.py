import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def _run_command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *arguments],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_run_pso_script_funciona(self) -> None:
        process = self._run_command(
            "run_pso.py",
            "--objective",
            "sphere",
            "--mode",
            "sequential",
            "--birds",
            "8",
            "--dimensions",
            "2",
            "--flights",
            "6",
            "--seed",
            "7",
        )

        self.assertEqual(process.returncode, 0, msg=process.stderr)
        self.assertIn("Modo: sequential", process.stdout)
        self.assertIn("Parque: sphere", process.stdout)
        self.assertIn("Migas en el tesoro:", process.stdout)

    def test_run_benchmarks_run_funciona(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            process = self._run_command(
                "run_benchmarks.py",
                "run",
                "--objective",
                "sphere",
                "--mode",
                "sequential",
                "--birds",
                "8",
                "--dimensions",
                "2",
                "--flights",
                "5",
                "--repetitions",
                "1",
                "--output-dir",
                temporary_directory,
            )

            self.assertEqual(process.returncode, 0, msg=process.stderr)
            self.assertIn("Modo: sequential", process.stdout)
            self.assertIn("Repeticiones: 1", process.stdout)
            self.assertTrue((Path(temporary_directory) / "sphere" / "sequential" / "run_000" / "convergence.svg").exists())
            self.assertTrue((Path(temporary_directory) / "sphere" / "sequential" / "run_000" / "animation_2d.gif").exists())
            self.assertTrue((Path(temporary_directory) / "sphere" / "sequential" / "run_000" / "animation_3d.gif").exists())
            self.assertFalse((Path(temporary_directory) / "sphere" / "sequential" / "run_000" / "swarm_2d_frames").exists())

    def test_run_grid_search_funciona(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            process = self._run_command(
                "run_grid_search.py",
                "--objective",
                "sphere",
                "--mode",
                "sequential",
                "--birds",
                "8",
                "--dimensions",
                "2",
                "--flights",
                "4",
                "--repetitions",
                "1",
                "--grid-w",
                "0.5,0.7",
                "--grid-c1",
                "1.4,1.8",
                "--grid-c2",
                "1.4,1.8",
                "--grid-seeds",
                "7,8",
                "--output-dir",
                temporary_directory,
            )

            self.assertEqual(process.returncode, 0, msg=process.stderr)
            self.assertIn("'mode': 'sequential'", process.stdout)
            self.assertIn("'seed_count': 2", process.stdout)
            self.assertTrue((Path(temporary_directory) / "sphere" / "grid_search_sequential" / "grid_search.csv").exists())

    def test_run_benchmarks_suite_funciona(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            process = self._run_command(
                "run_benchmarks.py",
                "--objectives",
                "sphere",
                "--dimensions",
                "2",
                "--modes",
                "sequential,numpy",
                "--birds",
                "6",
                "--flights",
                "4",
                "--repetitions",
                "1",
                "--output-dir",
                temporary_directory,
            )

            self.assertEqual(process.returncode, 0, msg=process.stderr)
            self.assertIn("'objective': 'sphere'", process.stdout)
            self.assertTrue((Path(temporary_directory) / "benchmark_suite" / "tables" / "summary" / "summary.csv").exists())
            self.assertTrue(
                (Path(temporary_directory) / "benchmark_suite" / "tables" / "per_seed_metrics" / "per_seed_metrics.csv").exists()
            )
            self.assertTrue((Path(temporary_directory) / "benchmark_suite" / "tables" / "speedup" / "speedup.csv").exists())
            self.assertTrue((Path(temporary_directory) / "benchmark_suite" / "tables" / "overhead" / "overhead.csv").exists())
            self.assertTrue(
                (
                    Path(temporary_directory)
                    / "benchmark_suite"
                    / "curves"
                    / "sphere_d2_average_convergence.svg"
                ).exists()
            )
            self.assertTrue(
                (
                    Path(temporary_directory)
                    / "benchmark_suite"
                    / "boxplots"
                    / "sphere_d2_final_fitness_boxplot.svg"
                ).exists()
            )
            self.assertFalse((Path(temporary_directory) / "benchmark_suite" / "summary.csv").exists())

    def test_make_viz_genera_frames_y_html(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            process = self._run_command(
                "make_viz.py",
                "--objective",
                "sphere",
                "--mode",
                "sequential",
                "--birds",
                "8",
                "--dimensions",
                "3",
                "--flights",
                "5",
                "--output-dir",
                temporary_directory,
            )

            self.assertEqual(process.returncode, 0, msg=process.stderr)
            run_directory = Path(temporary_directory) / "sphere" / "sequential" / "run_000"
            self.assertTrue((run_directory / "swarm_3d.html").exists())
            self.assertTrue((run_directory / "swarm_3d_frames" / "frame_000.svg").exists())


if __name__ == "__main__":
    unittest.main()
