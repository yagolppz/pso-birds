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

    def test_run_benchmark_run_funciona(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            process = self._run_command(
                "run_benchmark.py",
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
            self.assertTrue(
                (Path(temporary_directory) / "sphere" / "sequential" / "run_000" / "convergence.svg").exists()
            )

    def test_run_benchmark_grid_search_funciona(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            process = self._run_command(
                "run_benchmark.py",
                "grid-search",
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
                "--grid-birds",
                "6,8",
                "--grid-w",
                "0.5,0.7",
                "--grid-seeds",
                "7,8",
                "--output-dir",
                temporary_directory,
            )

            self.assertEqual(process.returncode, 0, msg=process.stderr)
            self.assertIn("'mode': 'sequential'", process.stdout)
            self.assertIn("'seed_count': 2", process.stdout)
            self.assertTrue(
                (Path(temporary_directory) / "sphere" / "grid_search_sequential" / "grid_search.csv").exists()
            )


if __name__ == "__main__":
    unittest.main()
