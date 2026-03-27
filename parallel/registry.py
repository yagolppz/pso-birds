"""Registro central de estrategias de evaluacion."""

from __future__ import annotations

from .v0_sequential import V0SequentialEvaluator
from .v1_threading import V1ThreadingEvaluator
from .v2_multiprocessing import V2MultiprocessingEvaluator
from .v3_asyncio import V3AsyncioEvaluator
from .v4_numpy import V4NumpyEvaluator


FITNESS_EVALUATOR_REGISTRY = {
    "sequential": V0SequentialEvaluator,
    "thread": V1ThreadingEvaluator,
    "process": V2MultiprocessingEvaluator,
    "asyncio": V3AsyncioEvaluator,
    "numpy": V4NumpyEvaluator,
}
