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
from viz.visualization import render_average_convergence_svg, render_boxplot_svg


DEFAULT_PROTOCOL_DIMENSIONS = [2, 10, 30]
DEFAULT_PROTOCOL_SEEDS = [7, 8, 9, 10, 11]
DEFAULT_GRID_W = [0.4, 0.7, 0.9]
DEFAULT_GRID_C1 = [1.3, 1.7, 2.1]
DEFAULT_GRID_C2 = [1.3, 1.7, 2.1]


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
    parser.add_argument("--dimensions", default=",".join(str(value) for value in DEFAULT_PROTOCOL_DIMENSIONS))
    parser.add_argument("--modes", default=",".join(MODE_CHOICES))
    parser.add_argument("--birds", type=int, default=12)
    parser.add_argument("--flights", type=int, default=20)
    parser.add_argument("--repetitions", type=int, default=len(DEFAULT_PROTOCOL_SEEDS))
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_PROTOCOL_SEEDS[0])
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

    if "sequential" not in modes:
        raise ValueError("La suite experimental necesita incluir el modo sequential para calcular speedup.")

    writer = ArtifactWriter(ArtifactConfig(output_directory=output_directory))
    summaries: dict[tuple[str, int, str], object] = {}
    rows: list[dict[str, object]] = []
    per_seed_rows: list[dict[str, object]] = []
    curve_rows: list[dict[str, object]] = []

    for objective_name in objective_names:
        objective = get_objective(objective_name)
        for dimensions_value in dimensions:
            for mode in modes:
                campaign_output_directory = (
                    output_directory
                    / "benchmark_suite"
                    / "campaign_runs"
                    / objective_name
                    / f"d{dimensions_value}"
                )
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
                        include_history=True,
                        artifacts=ArtifactConfig(output_directory=campaign_output_directory),
                    )
                )
                summaries[(objective_name, dimensions_value, mode)] = summary
                per_seed_rows.extend(summary.seed_rows)
                curve_rows.extend(
                    {
                        "objective": objective_name,
                        "dimensions": dimensions_value,
                        "mode": mode,
                        **point,
                    }
                    for point in summary.average_history
                )

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
                        "overhead_ratio_mean": _safe_divide(
                            summary.timings.overhead_seconds_mean,
                            summary.timings.total_seconds_mean,
                        ),
                        "speedup_vs_sequential": _safe_divide(
                            baseline.timings.total_seconds_mean,
                            summary.timings.total_seconds_mean,
                        ),
                        "seed_start": seed,
                        "seed_end": seed + repetitions - 1,
                    }
                )

    rows.sort(key=lambda row: (row["objective"], row["dimensions"], row["mode"]))
    tables_directory = Path("benchmark_suite") / "tables"
    writer.write_named_rows_artifacts(tables_directory / "summary", "summary", rows)
    writer.write_named_rows_artifacts(tables_directory / "per_seed_metrics", "per_seed_metrics", per_seed_rows)
    writer.write_named_rows_artifacts(tables_directory / "average_curves", "average_curves", curve_rows)
    writer.write_named_rows_artifacts(tables_directory / "speedup", "speedup", _build_speedup_rows(rows))
    writer.write_named_rows_artifacts(tables_directory / "overhead", "overhead", _build_overhead_rows(rows))
    writer.write_named_payload_artifacts(
        tables_directory / "protocol",
        "protocol",
        {
            "dimensions": dimensions,
            "modes": modes,
            "seeds": list(range(seed, seed + repetitions)),
            "grid_search": {
                "w": DEFAULT_GRID_W,
                "c1": DEFAULT_GRID_C1,
                "c2": DEFAULT_GRID_C2,
            },
        },
    )
    _write_protocol_svgs(output_directory, objective_names, dimensions, modes, summaries)
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


def _build_speedup_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "objective": row["objective"],
            "dimensions": row["dimensions"],
            "mode": row["mode"],
            "speedup_vs_sequential": row["speedup_vs_sequential"],
            "total_seconds_mean": row["total_seconds_mean"],
        }
        for row in rows
    ]


def _build_overhead_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "objective": row["objective"],
            "dimensions": row["dimensions"],
            "mode": row["mode"],
            "overhead_seconds_mean": row["overhead_seconds_mean"],
            "overhead_ratio_mean": row["overhead_ratio_mean"],
            "evaluation_seconds_mean": row["evaluation_seconds_mean"],
            "update_seconds_mean": row["update_seconds_mean"],
        }
        for row in rows
    ]


def _write_protocol_svgs(
    output_directory: Path,
    objective_names: list[str],
    dimensions: list[int],
    modes: list[str],
    summaries: dict[tuple[str, int, str], object],
) -> None:
    logger = get_project_logger()
    curves_directory = output_directory / "benchmark_suite" / "curves"
    boxplots_directory = output_directory / "benchmark_suite" / "boxplots"
    curves_directory.mkdir(parents=True, exist_ok=True)
    boxplots_directory.mkdir(parents=True, exist_ok=True)

    for objective_name in objective_names:
        for dimensions_value in dimensions:
            curves_by_mode: dict[str, list[float]] = {}
            samples_by_mode: dict[str, list[float]] = {}
            for mode in modes:
                summary = summaries[(objective_name, dimensions_value, mode)]
                if summary.average_history:
                    curves_by_mode[mode] = [point["treasure_crumbs_mean"] for point in summary.average_history]
                if summary.seed_rows:
                    samples_by_mode[mode] = [row["best_crumbs"] for row in summary.seed_rows]

            if curves_by_mode:
                logger.info(
                    "Render curvas promedio | objective=%s | dimensions=%s | curve_count=%d | modes=%s",
                    objective_name,
                    dimensions_value,
                    len(curves_by_mode),
                    ",".join(sorted(curves_by_mode)),
                )
                (curves_directory / f"{objective_name}_d{dimensions_value}_average_convergence.svg").write_text(
                    render_average_convergence_svg(
                        curves_by_mode,
                        title=f"{objective_name} | d={dimensions_value} | Curvas promedio",
                    ),
                    encoding="utf-8",
                )
            if samples_by_mode:
                (boxplots_directory / f"{objective_name}_d{dimensions_value}_final_fitness_boxplot.svg").write_text(
                    render_boxplot_svg(
                        samples_by_mode,
                        title=f"{objective_name} | d={dimensions_value} | Fitness final por estrategia",
                    ),
                    encoding="utf-8",
                )


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
