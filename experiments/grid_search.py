"""Grid search reproducible para PSO-BIRDS."""

from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pformat

from core.benchmark import grid_search_benchmark
from core.config import ArtifactConfig, BenchmarkConfig, SearchSpaceConfig, SwarmConfig
from core.logging import configure_project_logger, get_project_logger
from objectives import OBJECTIVES, get_objective
from parallel import FITNESS_EVALUATOR_REGISTRY

MODE_CHOICES = sorted(FITNESS_EVALUATOR_REGISTRY)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grid search reproducible para PSO-BIRDS.")
    parser.add_argument("--objective", choices=sorted(OBJECTIVES), default="sphere")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="sequential")
    parser.add_argument("--dimensions", type=int, default=2)
    parser.add_argument("--birds", type=int, default=20)
    parser.add_argument("--flights", type=int, default=30)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--grid-w", default="0.4,0.7,0.9")
    parser.add_argument("--grid-c1", default="1.3,1.7,2.1")
    parser.add_argument("--grid-c2", default="1.3,1.7,2.1")
    parser.add_argument("--grid-seeds", default="7,8,9")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--log-file", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configure_project_logger(log_file=args.log_file)
    logger = get_project_logger()
    objective = get_objective(args.objective)
    config = BenchmarkConfig(
        objective=objective,
        swarm=SwarmConfig(birds=args.birds, flights=args.flights, random_seed=args.seed),
        search_space=SearchSpaceConfig(
            dimensions=args.dimensions,
            lower_bound=objective.suggested_lower_bound,
            upper_bound=objective.suggested_upper_bound,
        ),
        evaluator_mode=args.mode,
        repetitions=args.repetitions,
        workers=args.workers,
        include_history=False,
        artifacts=ArtifactConfig(output_directory=args.output_dir),
    )
    grid = {
        "inertia": _parse_float_grid(args.grid_w),
        "cognitive_weight": _parse_float_grid(args.grid_c1),
        "social_weight": _parse_float_grid(args.grid_c2),
    }
    rows = grid_search_benchmark(config, grid, mode=args.mode, seeds=_parse_int_grid(args.grid_seeds))
    for row in rows[:10]:
        logger.info("%s", pformat(row))


def _parse_float_grid(raw: str) -> list[float]:
    return [float(piece.strip()) for piece in raw.split(",") if piece.strip()]


def _parse_int_grid(raw: str) -> list[int]:
    return [int(piece.strip()) for piece in raw.split(",") if piece.strip()]
