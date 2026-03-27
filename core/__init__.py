"""Nucleo del juego de los pajaritos y las migas."""

from .config import ArtifactConfig, BenchmarkConfig, SearchSpaceConfig, SwarmConfig
from .benchmark import compare_benchmark, grid_search_benchmark, run_benchmark
from .logging import JsonLinesBirdLogger, StructuredLogger
from .particle import BirdParticle, Vector
from .persistence import ArtifactWriter
from .pso import BirdSwarmOptimizer
from .results import BenchmarkResult, BenchmarkTimingSummary, EvaluationReport, FlightMetrics, FlightResult
from .swarm import FlightSnapshot, FlockTreasure, SwarmHistory
from .types import EVALUATION_MODES, FitnessEvaluator, ObjectiveDefinition
from .visualization import render_convergence_svg, render_swarm_2d_svg
from parallel import CrumbEvaluator

__all__ = [
    "ArtifactConfig",
    "BenchmarkConfig",
    "BenchmarkResult",
    "BenchmarkTimingSummary",
    "BirdParticle",
    "BirdSwarmOptimizer",
    "CrumbEvaluator",
    "EVALUATION_MODES",
    "EvaluationReport",
    "FitnessEvaluator",
    "FlightMetrics",
    "FlightResult",
    "FlightSnapshot",
    "FlockTreasure",
    "JsonLinesBirdLogger",
    "ObjectiveDefinition",
    "SearchSpaceConfig",
    "StructuredLogger",
    "SwarmConfig",
    "SwarmHistory",
    "Vector",
    "ArtifactWriter",
    "compare_benchmark",
    "grid_search_benchmark",
    "render_convergence_svg",
    "render_swarm_2d_svg",
    "run_benchmark",
]
