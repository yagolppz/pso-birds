"""Genera visualizaciones y animaciones reproducibles del enjambre."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from pprint import pformat

from core.cli_utils import MODE_CHOICES, add_common_pso_arguments, build_search_space_from_args, build_swarm_config_from_args
from core.config import ArtifactConfig
from core.logging import JsonLinesBirdLogger
from core.persistence import ArtifactWriter
from core.pso import BirdSwarmOptimizer
from core.visualization import export_animation, write_visualization_artifacts
from objectives import OBJECTIVES, get_objective
from parallel import build_fitness_evaluator


def _cleanup_animation_residues(run_directory: Path) -> None:
    for directory_name in ("swarm_2d_frames", "swarm_3d_frames"):
        directory_path = run_directory / directory_name
        if directory_path.exists():
            shutil.rmtree(directory_path)

    for pattern in ("frame_*.svg", "frame_*.png", "animation.gif", "animation.mp4"):
        for frame_path in run_directory.glob(pattern):
            frame_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Genera visualizaciones y frames animados para PSO-BIRDS.")
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--export", choices=("none", "gif", "mp4"), default="none")
    add_common_pso_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    objective = get_objective(args.objective)
    search_space = build_search_space_from_args(args, objective)
    artifact_config = ArtifactConfig(output_directory=args.output_dir)
    writer = ArtifactWriter(artifact_config)
    run_directory = writer.prepare_run_directory(objective.name, args.mode, 0)
    optimizer = BirdSwarmOptimizer(
        swarm_config=build_swarm_config_from_args(args),
        search_space=search_space,
        evaluator=build_fitness_evaluator(mode=args.mode, workers=args.workers),
        logger=JsonLinesBirdLogger.for_directory(run_directory, enabled=artifact_config.save_jsonl_log),
    )
    result = optimizer.run(objective, include_history=True)
    writer.write_run_artifacts(result, objective.name, args.mode, 0)
    if run_directory is not None and result.history is not None:
        write_visualization_artifacts(
            run_directory,
            result.history,
            objective,
            search_space,
            include_animation_assets=args.export == "none",
        )
        print(f"Visualizaciones escritas en: {run_directory}")
        animation_path = export_animation(run_directory, args.export, result.history, objective, search_space)
        if animation_path is not None:
            _cleanup_animation_residues(run_directory)
            print(f"Animation saved at: {animation_path}")
    print(f"Modo: {result.evaluator_mode}")
    print(f"Parque: {objective.name}")
    print(f"Mejor sitio del grupo: {pformat(result.best_position)}")
    print(f"Migas en el tesoro: {result.best_crumbs:.10f}")


if __name__ == "__main__":
    main()
