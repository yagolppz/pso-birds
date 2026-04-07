"""Campanas de benchmark y suite reproducible del proyecto."""

from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pformat

from core.benchmark import compare_benchmark, run_benchmark
from core.cli_utils import MODE_CHOICES, NON_SEQUENTIAL_MODE_CHOICES, add_common_pso_arguments
from core.config import ArtifactConfig, BenchmarkConfig, SearchSpaceConfig, SwarmConfig
from core.persistence_bridge import ArtifactWriter
from core.logging import configure_project_logger, get_project_logger
from objectives import OBJECTIVES, get_objective


def build_compare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Banco de pruebas PSO para comparar vuelos.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser("compare")
    _add_common_arguments(compare_parser)
    compare_parser.add_argument("--candidate-mode", choices=NON_SEQUENTIAL_MODE_CHOICES, default="process")
    compare_parser.add_argument("--repetitions", type=int, default=3)

    run_parser = subparsers.add_parser("run")
    _add_common_arguments(run_parser)
    run_parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    run_parser.add_argument("--repetitions", type=int, default=1)

    return parser


def build_suite_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suite reproducible de benchmarks para PSO-BIRDS.")
    parser.add_argument("--objectives", default="sphere,ackley,rastrigin,rosenbrock")
    parser.add_argument("--dimensions", default="2,10,30")
    parser.add_argument("--modes", default=",".join(MODE_CHOICES))
    parser.add_argument("--birds", type=int, default=12)
    parser.add_argument("--flights", type=int, default=20)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--log-file", type=Path, default=None)
    return parser


def main_compare_cli() -> None:
    args = build_compare_parser().parse_args()
    configure_project_logger(log_file=args.log_file)
    logger = get_project_logger()
    objective = get_objective(args.objective)
    config = BenchmarkConfig(
        objective=objective,
        swarm=_build_swarm(args),
        search_space=_build_search_space(args.dimensions, objective),
        evaluator_mode=getattr(args, "mode", "sequential"),
        repetitions=args.repetitions,
        workers=args.workers,
        artifacts=ArtifactConfig(output_directory=args.output_dir),
    )

    if args.command == "run":
        print_summary(run_benchmark(config))
        return

    comparison = compare_benchmark(config, candidate_mode=args.candidate_mode, workers=args.workers)
    print_summary(comparison["baseline"])
    logger.info("")
    print_summary(comparison["candidate"])
    logger.info("")
    logger.info("Aceleracion estimada: x%.3f", comparison["speedup"])


def main_suite_cli() -> None:
    args = build_suite_parser().parse_args()
    configure_project_logger(log_file=args.log_file)
    logger = get_project_logger()
    rows = run_benchmark_suite(
        objective_names=_parse_csv(args.objectives),
        dimensions=[int(value) for value in _parse_csv(args.dimensions)],
        modes=_parse_csv(args.modes),
        birds=args.birds,
        flights=args.flights,
        repetitions=args.repetitions,
        workers=args.workers,
        seed=args.seed,
        output_directory=args.output_dir,
    )
    for row in rows[:12]:
        logger.info("%s", pformat(row))


def run_benchmark_suite(
    objective_names: list[str],
    dimensions: list[int],
    modes: list[str],
    birds: int,
    flights: int,
    repetitions: int,
    workers: int | None,
    seed: int,
    output_directory: Path,
) -> list[dict[str, object]]:
    """Ejecuta la suite completa de benchmarks y resume speedups."""

    writer = ArtifactWriter(ArtifactConfig(output_directory=output_directory))
    summaries: dict[tuple[str, int, str], object] = {}
    rows: list[dict[str, object]] = []

    for objective_name in objective_names:
        objective = get_objective(objective_name)
        for dimensions_value in dimensions:
            for mode in modes:
                summary = run_benchmark(
                    BenchmarkConfig(
                        objective=objective,
                        swarm=SwarmConfig(birds=birds, flights=flights, random_seed=seed),
                        search_space=SearchSpaceConfig(
                            dimensions=dimensions_value,
                            lower_bound=objective.suggested_lower_bound,
                            upper_bound=objective.suggested_upper_bound,
                        ),
                        evaluator_mode=mode,
                        repetitions=repetitions,
                        workers=workers,
                        include_history=(dimensions_value in {2, 3}),
                        artifacts=ArtifactConfig(output_directory=output_directory),
                    )
                )
                summaries[(objective_name, dimensions_value, mode)] = summary

    for objective_name in objective_names:
        for dimensions_value in dimensions:
            baseline = summaries[(objective_name, dimensions_value, "sequential")]
            for mode in modes:
                summary = summaries[(objective_name, dimensions_value, mode)]
                rows.append(
                    {
                        "objective": objective_name,
                        "dimensions": dimensions_value,
                        "mode": mode,
                        "birds": birds,
                        "flights": flights,
                        "repetitions": repetitions,
                        "workers": workers,
                        "best_crumbs_mean": summary.best_crumbs_mean,
                        "best_crumbs_final": summary.best_run.best_crumbs,
                        "total_seconds_mean": summary.timings.total_seconds_mean,
                        "evaluation_seconds_mean": summary.timings.evaluation_seconds_mean,
                        "update_seconds_mean": summary.timings.update_seconds_mean,
                        "overhead_seconds_mean": summary.timings.overhead_seconds_mean,
                        "speedup_vs_sequential": baseline.timings.total_seconds_mean / summary.timings.total_seconds_mean,
                    }
                )

    rows.sort(key=lambda row: (row["objective"], row["dimensions"], row["mode"]))
    writer.write_named_rows_artifacts(Path("benchmark_suite"), "summary", rows)
    return rows


def print_summary(summary) -> None:
    logger = get_project_logger()
    logger.info("Modo: %s", summary.mode)
    logger.info("Parque: %s", summary.objective_name)
    logger.info("Repeticiones: %d", summary.repetitions)
    logger.info("Mejor sitio del grupo: %s", pformat(summary.best_run.best_position))
    logger.info("Migas en el tesoro: %.10f", summary.best_run.best_crumbs)
    logger.info("Vuelos completados: %d", summary.best_run.flights_completed)
    logger.info("Tiempo total medio: %.4f s", summary.timings.total_seconds_mean)
    logger.info("Tiempo fitness medio: %.4f s", summary.timings.evaluation_seconds_mean)
    logger.info("Tiempo actualizacion medio: %.4f s", summary.timings.update_seconds_mean)
    logger.info("Overhead medio: %.4f s", summary.timings.overhead_seconds_mean)
    logger.info("Promedio de migas finales: %.10f", summary.best_crumbs_mean)


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    add_common_pso_arguments(parser)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--log-file", type=Path, default=None)


def _build_swarm(arguments: argparse.Namespace) -> SwarmConfig:
    return SwarmConfig(
        birds=arguments.birds,
        flights=arguments.flights,
        inertia=arguments.w,
        cognitive_weight=arguments.c1,
        social_weight=arguments.c2,
        random_seed=arguments.seed,
        stop_when_crumbs_below=arguments.stop_when_crumbs_below,
        velocity_limit_factor=arguments.velocity_limit_factor,
    )


def _build_search_space(dimensions: int, objective) -> SearchSpaceConfig:
    return SearchSpaceConfig(
        dimensions=dimensions,
        lower_bound=objective.suggested_lower_bound,
        upper_bound=objective.suggested_upper_bound,
    )


def _parse_csv(raw: str) -> list[str]:
    return [piece.strip() for piece in raw.split(",") if piece.strip()]
