"""Utilidades de benchmark y grid search para el proyecto."""

from __future__ import annotations

from dataclasses import asdict
from itertools import product

from .config import BenchmarkConfig, SwarmConfig
from .persistence_bridge import ArtifactWriter
from .logging import JsonLinesBirdLogger
from .pso import BirdSwarmOptimizer, _swarm_for_repetition, _swarm_with_overrides
from .results import BenchmarkResult, BenchmarkTimingSummary, FlightResult
from parallel import build_fitness_evaluator


def run_benchmark(config: BenchmarkConfig) -> BenchmarkResult:
    """Ejecuta varias repeticiones y resume que tan bien vuela la bandada."""

    runs: list[FlightResult] = []
    writer = ArtifactWriter(config.artifacts)

    for repetition in range(config.repetitions):
        run_directory = writer.prepare_run_directory(config.objective.name, config.evaluator_mode, repetition)
        optimizer = BirdSwarmOptimizer(
            swarm_config=_swarm_for_repetition(config.swarm, repetition),
            search_space=config.search_space,
            evaluator=build_fitness_evaluator(mode=config.evaluator_mode, workers=config.workers),
            logger=JsonLinesBirdLogger.for_directory(run_directory, enabled=config.artifacts.save_jsonl_log),
        )
        run = optimizer.run(config.objective, include_history=config.include_history)
        runs.append(run)
        writer.write_run_artifacts(
            run,
            config.objective.name,
            config.evaluator_mode,
            repetition,
            metadata=_run_metadata(config, repetition),
        )
        if run.history is not None and run_directory is not None and config.artifacts.save_svg_plot:
            from viz.visualization import cleanup_animation_residues, export_animation, write_visualization_artifacts
            if config.search_space.dimensions in {2, 3}:
                write_visualization_artifacts(
                    run_directory,
                    run.history,
                    config.objective,
                    config.search_space,
                    include_animation_assets=False,
                )
                animation_path = export_animation(
                    run_directory,
                    "gif",
                    run.history,
                    config.objective,
                    config.search_space,
                )
                if animation_path is not None:
                    cleanup_animation_residues(run_directory)
            else:
                write_visualization_artifacts(run_directory, run.history, config.objective, config.search_space)

    best_run = min(runs, key=lambda run: run.best_crumbs)
    summary = BenchmarkResult(
        mode=config.evaluator_mode,
        objective_name=config.objective.name,
        repetitions=config.repetitions,
        best_crumbs_mean=sum(run.best_crumbs for run in runs) / len(runs),
        timings=BenchmarkTimingSummary(
            total_seconds_mean=sum(run.metrics.total_seconds for run in runs) / len(runs),
            evaluation_seconds_mean=sum(run.metrics.evaluation_seconds for run in runs) / len(runs),
            update_seconds_mean=sum(run.metrics.update_seconds for run in runs) / len(runs),
            overhead_seconds_mean=sum(run.metrics.overhead_seconds for run in runs) / len(runs),
        ),
        best_run=best_run,
    )
    writer.write_summary_artifacts(
        summary,
        config.objective.name,
        config.evaluator_mode,
        metadata=_benchmark_metadata(config, config.evaluator_mode),
    )
    return summary


def compare_benchmark(config: BenchmarkConfig, candidate_mode: str, workers: int | None = None) -> dict[str, object]:
    """Compara el vuelo secuencial con otra forma de contar migas."""

    baseline = run_benchmark(config)
    candidate = run_benchmark(
        BenchmarkConfig(
            objective=config.objective,
            swarm=config.swarm,
            search_space=config.search_space,
            evaluator_mode=candidate_mode,
            repetitions=config.repetitions,
            workers=workers,
            include_history=config.include_history,
            artifacts=config.artifacts,
        )
    )
    payload = {
        "baseline": baseline,
        "candidate": candidate,
        "speedup": baseline.timings.total_seconds_mean / candidate.timings.total_seconds_mean,
    }
    ArtifactWriter(config.artifacts).write_comparison_artifacts(
        payload,
        config.objective.name,
        candidate_mode,
        metadata={
            **_benchmark_metadata(config, "sequential"),
            "candidate_mode": candidate_mode,
        },
    )
    return payload


def grid_search_benchmark(
    config: BenchmarkConfig,
    grid: dict[str, list[float | int]],
    mode: str | None = None,
    seeds: list[int] | None = None,
) -> list[dict[str, object]]:
    """Prueba varias combinaciones de bandada y ordena las mejores."""

    rows: list[dict[str, object]] = []
    run_mode = mode or config.evaluator_mode
    keys = list(grid)
    selected_seeds = seeds or [config.swarm.random_seed]

    for values in product(*(grid[key] for key in keys)):
        varied = dict(zip(keys, values, strict=True))
        seed_summaries: list[tuple[int, BenchmarkResult]] = []

        for seed in selected_seeds:
            summary = run_benchmark(
                BenchmarkConfig(
                    objective=config.objective,
                    swarm=_swarm_with_overrides(config.swarm, {**varied, "random_seed": seed}),
                    search_space=config.search_space,
                    evaluator_mode=run_mode,
                    repetitions=config.repetitions,
                    workers=config.workers,
                    include_history=config.include_history,
                    artifacts=config.artifacts,
                )
            )
            seed_summaries.append((seed, summary))

        rows.append(_build_grid_row(config, run_mode, varied, seed_summaries))

    rows.sort(key=lambda row: (row["best_crumbs_mean"], row["total_seconds_mean"]))
    ArtifactWriter(config.artifacts).write_grid_search_artifacts(
        rows,
        config.objective.name,
        run_mode,
        metadata={
            **_benchmark_metadata(config, run_mode),
            "grid": grid,
            "seeds": selected_seeds,
        },
    )
    return rows


def _run_metadata(config: BenchmarkConfig, repetition: int) -> dict[str, object]:
    swarm = _swarm_for_repetition(config.swarm, repetition)
    return {
        "objective": config.objective.name,
        "mode": config.evaluator_mode,
        "repetition": repetition,
        "workers": config.workers,
        "search_space": asdict(config.search_space),
        "swarm": asdict(swarm),
    }


def _benchmark_metadata(config: BenchmarkConfig, mode: str) -> dict[str, object]:
    return {
        "objective": config.objective.name,
        "mode": mode,
        "workers": config.workers,
        "repetitions": config.repetitions,
        "seeds": [config.swarm.random_seed + repetition for repetition in range(config.repetitions)],
        "search_space": asdict(config.search_space),
        "swarm": asdict(config.swarm),
    }


def _build_grid_row(
    config: BenchmarkConfig,
    run_mode: str,
    varied: dict[str, float | int],
    seed_summaries: list[tuple[int, BenchmarkResult]],
) -> dict[str, object]:
    summaries = [summary for _, summary in seed_summaries]
    best_seed, best_summary = min(
        seed_summaries,
        key=lambda item: (item[1].best_crumbs_mean, item[1].timings.total_seconds_mean),
    )
    return {
        **varied,
        "swarm_size": int(varied.get("birds", config.swarm.birds)),
        "w": float(varied.get("inertia", config.swarm.inertia)),
        "c1": float(varied.get("cognitive_weight", config.swarm.cognitive_weight)),
        "c2": float(varied.get("social_weight", config.swarm.social_weight)),
        "mode": run_mode,
        "objective_name": config.objective.name,
        "seeds": ",".join(str(seed) for seed, _ in seed_summaries),
        "seed_count": len(seed_summaries),
        "best_seed": best_seed,
        "best_crumbs_mean": sum(summary.best_crumbs_mean for summary in summaries) / len(summaries),
        "best_crumbs_min": min(summary.best_run.best_crumbs for summary in summaries),
        "total_seconds_mean": sum(summary.timings.total_seconds_mean for summary in summaries) / len(summaries),
        "evaluation_seconds_mean": sum(summary.timings.evaluation_seconds_mean for summary in summaries) / len(summaries),
        "update_seconds_mean": sum(summary.timings.update_seconds_mean for summary in summaries) / len(summaries),
        "overhead_seconds_mean": sum(summary.timings.overhead_seconds_mean for summary in summaries) / len(summaries),
        "best_position": best_summary.best_run.best_position,
    }
