"""Script para comparar estrategias de vuelo y lanzar grid search."""

from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pformat

from core.benchmark import compare_benchmark, grid_search_benchmark, run_benchmark
from core.cli_utils import (
    MODE_CHOICES,
    NON_SEQUENTIAL_MODE_CHOICES,
    add_common_pso_arguments,
    build_search_space_from_args,
    build_swarm_config_from_args,
)
from core.config import ArtifactConfig, BenchmarkConfig, SearchSpaceConfig, SwarmConfig
from objectives import OBJECTIVES, get_objective


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Banco de pruebas PSO para comparar vuelos.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser("compare")
    _add_common_arguments(compare_parser)
    compare_parser.add_argument("--candidate-mode", choices=NON_SEQUENTIAL_MODE_CHOICES, default="process")
    compare_parser.add_argument("--repetitions", type=int, default=3)

    grid_parser = subparsers.add_parser("grid-search")
    _add_common_arguments(grid_parser)
    grid_parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    grid_parser.add_argument("--repetitions", type=int, default=1)
    grid_parser.add_argument("--grid-birds", default="")
    grid_parser.add_argument("--grid-flights", default="")
    grid_parser.add_argument("--grid-w", default="")
    grid_parser.add_argument("--grid-c1", default="")
    grid_parser.add_argument("--grid-c2", default="")
    grid_parser.add_argument("--grid-velocity-limit", default="")
    grid_parser.add_argument("--grid-seeds", default="")

    run_parser = subparsers.add_parser("run")
    _add_common_arguments(run_parser)
    run_parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    run_parser.add_argument("--repetitions", type=int, default=1)

    return parser


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    add_common_pso_arguments(parser)
    parser.add_argument("--output-dir", type=Path, default=None)


def main() -> None:
    args = build_parser().parse_args()
    objective = get_objective(args.objective)
    config = BenchmarkConfig(
        objective=objective,
        swarm=build_swarm_config_from_args(args),
        search_space=build_search_space_from_args(args, objective),
        evaluator_mode=getattr(args, "mode", "sequential"),
        repetitions=args.repetitions,
        workers=args.workers,
        artifacts=ArtifactConfig(output_directory=args.output_dir),
    )

    if args.command == "run":
        print_summary(run_benchmark(config))
        return

    if args.command == "compare":
        comparison = compare_benchmark(config, candidate_mode=args.candidate_mode, workers=args.workers)
        print_summary(comparison["baseline"])
        print()
        print_summary(comparison["candidate"])
        print()
        print(f"Aceleracion estimada: x{comparison['speedup']:.3f}")
        return

    grid = {
        "birds": _parse_int_grid(args.grid_birds),
        "flights": _parse_int_grid(args.grid_flights),
        "inertia": _parse_float_grid(args.grid_w),
        "cognitive_weight": _parse_float_grid(args.grid_c1),
        "social_weight": _parse_float_grid(args.grid_c2),
        "velocity_limit_factor": _parse_float_grid(args.grid_velocity_limit),
    }
    filtered_grid = {key: values for key, values in grid.items() if values}
    if not filtered_grid:
        raise ValueError("Grid search necesita al menos un parametro con varias opciones.")
    seeds = _parse_int_grid(args.grid_seeds) or [args.seed]
    for row in grid_search_benchmark(config, filtered_grid, mode=args.mode, seeds=seeds)[:10]:
        print(pformat(row))


def print_summary(summary) -> None:
    print(f"Modo: {summary.mode}")
    print(f"Parque: {summary.objective_name}")
    print(f"Repeticiones: {summary.repetitions}")
    print(f"Mejor sitio del grupo: {pformat(summary.best_run.best_position)}")
    print(f"Migas en el tesoro: {summary.best_run.best_crumbs:.10f}")
    print(f"Vuelos completados: {summary.best_run.flights_completed}")
    print(f"Tiempo total medio: {summary.timings.total_seconds_mean:.4f} s")
    print(f"Tiempo fitness medio: {summary.timings.evaluation_seconds_mean:.4f} s")
    print(f"Tiempo actualizacion medio: {summary.timings.update_seconds_mean:.4f} s")
    print(f"Overhead medio: {summary.timings.overhead_seconds_mean:.4f} s")
    print(f"Promedio de migas finales: {summary.best_crumbs_mean:.10f}")


def _parse_int_grid(raw: str) -> list[int]:
    return [int(piece.strip()) for piece in raw.split(",") if piece.strip()]


def _parse_float_grid(raw: str) -> list[float]:
    return [float(piece.strip()) for piece in raw.split(",") if piece.strip()]


if __name__ == "__main__":
    main()
