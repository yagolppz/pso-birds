"""Script simple para hacer volar la bandada una sola vez."""

from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pformat

from core.cli_utils import MODE_CHOICES, add_common_pso_arguments, build_search_space_from_args, build_swarm_config_from_args
from core.config import ArtifactConfig
from core.logging import JsonLinesBirdLogger
from core.persistence import ArtifactWriter
from core.pso import BirdSwarmOptimizer
from core.visualization import write_visualization_artifacts
from objectives import OBJECTIVES, get_objective
from parallel import build_fitness_evaluator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lanza una bandada PSO sobre un parque continuo.")
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    parser.add_argument("--output-dir", type=Path, default=None)
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
    if run_directory is not None and result.history is not None and artifact_config.save_svg_plot:
        write_visualization_artifacts(run_directory, result.history, objective, search_space)

    print(f"Modo: {result.evaluator_mode}")
    print(f"Parque: {objective.name}")
    print(f"Mejor sitio del grupo: {pformat(result.best_position)}")
    print(f"Migas en el tesoro: {result.best_crumbs:.10f}")
    print(f"Vuelos completados: {result.flights_completed}")
    print(f"Tiempo total: {result.metrics.total_seconds:.4f} s")
    print(f"Tiempo fitness: {result.metrics.evaluation_seconds:.4f} s")
    print(f"Tiempo actualizacion: {result.metrics.update_seconds:.4f} s")
    print(f"Overhead: {result.metrics.overhead_seconds:.4f} s")


if __name__ == "__main__":
    main()
