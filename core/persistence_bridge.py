"""Puente de compatibilidad hacia la persistencia real en `io/`.

Python reserva el nombre `io` para la biblioteca estandar, por lo que
`import io.persistence` no funciona desde la raiz del proyecto. Para no
duplicar la logica, este modulo solo reexporta la implementacion canonica.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
import sys


def _load_io_persistence_module() -> ModuleType:
    module_name = "_pso_birds_io_persistence"
    existing_module = sys.modules.get(module_name)
    if existing_module is not None:
        return existing_module

    module_path = Path(__file__).resolve().parents[1] / "io" / "persistence.py"
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el modulo de persistencia: {module_path}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ArtifactWriter = _load_io_persistence_module().ArtifactWriter

__all__ = ["ArtifactWriter"]
