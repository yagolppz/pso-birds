"""Estrategias intercambiables para evaluar fitness."""

from .evaluators import CrumbEvaluator, build_fitness_evaluator
from .registry import FITNESS_EVALUATOR_REGISTRY
from .v0_sequential import V0SequentialEvaluator
from .v1_threading import V1ThreadingEvaluator
from .v2_multiprocessing import V2MultiprocessingEvaluator
from .v3_asyncio import V3AsyncioEvaluator
from .v4_numpy import V4NumpyEvaluator

__all__ = [
    "CrumbEvaluator",
    "FITNESS_EVALUATOR_REGISTRY",
    "V0SequentialEvaluator",
    "V1ThreadingEvaluator",
    "V2MultiprocessingEvaluator",
    "V3AsyncioEvaluator",
    "V4NumpyEvaluator",
    "build_fitness_evaluator",
]
