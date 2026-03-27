"""Script simple para hacer volar la bandada una sola vez."""

from __future__ import annotations

import argparse
from pprint import pformat

from core.cli_utils import MODE_CHOICES, add_common_pso_arguments, build_search_space_from_args, build_swarm_config_from_args
from core.config import SearchSpaceConfig, SwarmConfig
from core.pso import BirdSwarmOptimizer
from objectives import OBJECTIVES, get_objective
from parallel import build_fitness_evaluator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lanza una bandada PSO sobre un parque continuo.")
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    add_common_pso_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    objective = get_objective(args.objective)
    optimizer = BirdSwarmOptimizer(
        swarm_config=build_swarm_config_from_args(args),
        search_space=build_search_space_from_args(args, objective),
        evaluator=build_fitness_evaluator(mode=args.mode, workers=args.workers),
    )
    result = optimizer.run(objective, include_history=True)
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
