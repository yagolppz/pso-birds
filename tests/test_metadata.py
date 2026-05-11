import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.config import ArtifactConfig
from core.metadata import build_reproducibility_metadata
from core.persistence_bridge import ArtifactWriter
from core.results import BenchmarkResult, FlightMetrics, FlightResult
from core.swarm import SwarmHistory


class MetadataTests(unittest.TestCase):
    def test_build_reproducibility_metadata_contains_expected_values(self) -> None:
        metadata = build_reproducibility_metadata({"seed": 42, "mode": "sequential", "workers": 4})

        self.assertIn("timestamp", metadata)
        self.assertIn("git_commit", metadata)
        self.assertIn("git_branch", metadata)
        self.assertIn("repo_dirty", metadata)
        self.assertIn("python_version", metadata)
        self.assertIn("platform", metadata)
        self.assertIn("cpu_count", metadata)
        self.assertEqual(metadata["seed"], 42)
        self.assertEqual(metadata["mode"], "sequential")
        self.assertEqual(metadata["workers"], 4)
        self.assertIsInstance(metadata["repo_dirty"], bool)

    def test_artifact_writer_includes_metadata_in_summary_json(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            writer = ArtifactWriter(ArtifactConfig(output_directory=output_dir))
            summary = BenchmarkResult(
                mode="sequential",
                objective_name="sphere",
                repetitions=1,
                best_crumbs_mean=0.0,
                timings=FlightMetrics(0.0, 0.0, 0.0, 0.0),
                best_run=FlightResult(
                    best_position=[0.0, 0.0],
                    best_crumbs=0.0,
                    flights_completed=0,
                    history=SwarmHistory(),
                    metrics=FlightMetrics(0.0, 0.0, 0.0, 0.0),
                    evaluator_mode="sequential",
                ),
                seed_rows=[],
                average_history=[],
            )

            writer.write_summary_artifacts(summary, "sphere", "sequential", {"seed": 7, "mode": "sequential", "workers": None})
            summary_path = output_dir / "sphere" / "sequential" / "summary.json"
            self.assertTrue(summary_path.exists())

            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertIn("metadata", payload)
            self.assertEqual(payload["metadata"]["mode"], "sequential")
            self.assertEqual(payload["metadata"]["seed"], 7)
            self.assertIn("python_version", payload["metadata"])
            self.assertIn("platform", payload["metadata"])
            self.assertIsInstance(payload["metadata"]["repo_dirty"], bool)


if __name__ == "__main__":
    unittest.main()
