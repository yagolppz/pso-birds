"""Utilidades compartidas para los runners de consola."""

from __future__ import annotations

import argparse

from .config import SearchSpaceConfig, SwarmConfig
from .types import EVALUATION_MODES, ObjectiveDefinition


MODE_CHOICES = sorted(EVALUATION_MODES)
NON_SEQUENTIAL_MODE_CHOICES = sorted(EVALUATION_MODES - {"sequential"})


def add_common_pso_arguments(parser: argparse.ArgumentParser) -> None:
    """Añade los argumentos comunes para lanzar una bandada en un parque."""

    parser.add_argument("--birds", type=int, default=30)
    parser.add_argument("--dimensions", type=int, default=2)
    parser.add_argument("--flights", type=int, default=80)
    parser.add_argument("--w", type=float, default=0.7)
    parser.add_argument("--c1", type=float, default=1.7)
    parser.add_argument("--c2", type=float, default=1.7)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--lower-bound", type=float, default=None)
    parser.add_argument("--upper-bound", type=float, default=None)
    parser.add_argument("--stop-when-crumbs-below", type=float, default=None)
    parser.add_argument("--velocity-limit-factor", type=float, default=0.2)


def build_swarm_config_from_args(arguments: argparse.Namespace) -> SwarmConfig:
    """Construye la configuracion de la bandada a partir del CLI."""

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


def build_search_space_from_args(
    arguments: argparse.Namespace,
    objective: ObjectiveDefinition,
) -> SearchSpaceConfig:
    """Construye el parque usando los limites dados o los sugeridos por el benchmark."""

    return SearchSpaceConfig(
        dimensions=arguments.dimensions,
        lower_bound=(
            arguments.lower_bound
            if arguments.lower_bound is not None
            else objective.suggested_lower_bound
        ),
        upper_bound=(
            arguments.upper_bound
            if arguments.upper_bound is not None
            else objective.suggested_upper_bound
        ),
    )
