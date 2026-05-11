"""Script simple para hacer volar la bandada una sola vez."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from pprint import pformat

from core.cli_utils import MODE_CHOICES, add_common_pso_arguments, build_search_space_from_args, build_swarm_config_from_args
from core.config import ArtifactConfig
from core.persistence_bridge import ArtifactWriter
from core.logging import JsonLinesBirdLogger, configure_project_logger, get_project_logger
from core.pso import BirdSwarmOptimizer
from objectives import OBJECTIVES, get_objective
from parallel import build_fitness_evaluator
from viz.visualization import write_visualization_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lanza una bandada PSO sobre un parque continuo.")
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--log-file", type=Path, default=None)
    add_common_pso_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configure_project_logger(log_file=args.log_file)
    logger = get_project_logger()
    objective = get_objective(args.objective)
    search_space = build_search_space_from_args(args, objective)
    artifact_config = ArtifactConfig(output_directory=args.output_dir)
    writer = ArtifactWriter(artifact_config)
    run_directory = writer.prepare_run_directory(objective.name, args.mode, 0)
    swarm_config = build_swarm_config_from_args(args)
    optimizer = BirdSwarmOptimizer(
        swarm_config=swarm_config,
        search_space=search_space,
        evaluator=build_fitness_evaluator(mode=args.mode, workers=args.workers, batch_size=args.batch_size),
        logger=JsonLinesBirdLogger.for_directory(run_directory, enabled=artifact_config.save_jsonl_log),
    )
    result = optimizer.run(objective, include_history=True)
    writer.write_run_artifacts(
        result,
        objective.name,
        args.mode,
        0,
        metadata={
            "objective": objective.name,
            "mode": args.mode,
            "workers": args.workers,
            "batch_size": args.batch_size,
            "search_space": asdict(search_space),
            "swarm": asdict(swarm_config),
        },
    )
    if run_directory is not None and result.history is not None and artifact_config.save_svg_plot:
        write_visualization_artifacts(run_directory, result.history, objective, search_space)

    logger.info("Modo: %s", result.evaluator_mode)
    logger.info("Parque: %s", objective.name)
    logger.info("Mejor sitio del grupo: %s", pformat(result.best_position))
    logger.info("Migas en el tesoro: %.10f", result.best_crumbs)
    logger.info("Vuelos completados: %d", result.flights_completed)
    logger.info("Tiempo total: %.4f s", result.metrics.total_seconds)
    logger.info("Tiempo fitness: %.4f s", result.metrics.evaluation_seconds)
    logger.info("Tiempo actualizacion: %.4f s", result.metrics.update_seconds)
    logger.info("Overhead: %.4f s", result.metrics.overhead_seconds)


if __name__ == "__main__":
    main()
