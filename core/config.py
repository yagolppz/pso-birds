"""Configuracion del parque, la bandada y los benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .types import EVALUATION_MODES, ObjectiveDefinition


@dataclass(slots=True)
class SearchSpaceConfig:
    """Define el parque donde vuelan los pajaritos."""

    dimensions: int
    lower_bound: float
    upper_bound: float
    clamp_positions: bool = True

    def __post_init__(self) -> None:
        if self.dimensions <= 0:
            raise ValueError("El parque debe tener al menos una dimension.")
        if self.lower_bound >= self.upper_bound:
            raise ValueError("Los limites del parque deben dejar espacio para volar.")
        if not self.clamp_positions:
            raise ValueError("El clamp minimo obligatorio debe permanecer activo.")


@dataclass(slots=True)
class SwarmConfig:
    """Hiperparametros de la bandada."""

    birds: int = 30
    flights: int = 100
    inertia: float = 0.7
    cognitive_weight: float = 1.7
    social_weight: float = 1.7
    random_seed: int = 7
    stop_when_crumbs_below: float | None = None
    stop_after_stagnant_flights: int | None = None
    velocity_limit_factor: float = 0.2

    def __post_init__(self) -> None:
        if self.birds <= 0:
            raise ValueError("Debe haber al menos un pajarito en la bandada.")
        if self.flights <= 0:
            raise ValueError("Debe programarse al menos un vuelo.")
        if self.inertia < 0:
            raise ValueError("La inercia no puede ser negativa.")
        if self.cognitive_weight < 0 or self.social_weight < 0:
            raise ValueError("Los pesos de memoria y cooperacion no pueden ser negativos.")
        if self.velocity_limit_factor <= 0:
            raise ValueError("El limite de velocidad debe ser positivo.")
        if self.stop_after_stagnant_flights is not None and self.stop_after_stagnant_flights <= 0:
            raise ValueError("stop_after_stagnant_flights debe ser un entero positivo o None.")


@dataclass(slots=True)
class ArtifactConfig:
    """Decide donde guardar los cuadernos del experimento."""

    output_directory: Path | None = None
    save_json: bool = True
    save_csv: bool = True
    save_yaml: bool = True
    save_svg_plot: bool = True
    save_jsonl_log: bool = True


@dataclass(slots=True)
class BenchmarkConfig:
    """Configura una campaña de comparacion de vuelos."""

    objective: ObjectiveDefinition
    swarm: SwarmConfig
    search_space: SearchSpaceConfig
    evaluator_mode: str = "sequential"
    repetitions: int = 1
    workers: int | None = None
    batch_size: int | None = None
    include_history: bool = True
    artifacts: ArtifactConfig = field(default_factory=ArtifactConfig)

    def __post_init__(self) -> None:
        if self.evaluator_mode not in EVALUATION_MODES:
            available = ", ".join(sorted(EVALUATION_MODES))
            raise ValueError(f"El modo de evaluacion debe ser uno de: {available}.")
        if self.repetitions <= 0:
            raise ValueError("La campaña debe repetirse al menos una vez.")
        if self.workers is not None and self.workers <= 0:
            raise ValueError("La cantidad de workers debe ser positiva.")
