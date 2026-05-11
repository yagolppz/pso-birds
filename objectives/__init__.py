"""Parques benchmark del proyecto."""

from .ackley import ackley_definition
from .rastrigin import rastrigin_definition
from .rosenbrock import rosenbrock_definition
from .sphere import sleepy_sphere_definition, sphere_definition
from .wifi_router import wifi_router_definition

OBJECTIVES = {
    "sphere": sphere_definition(),
    "sleepy_sphere": sleepy_sphere_definition(),
    "rastrigin": rastrigin_definition(),
    "ackley": ackley_definition(),
    "rosenbrock": rosenbrock_definition(),
    "wifi_router": wifi_router_definition(),
}


def get_objective(name: str):
    try:
        return OBJECTIVES[name]
    except KeyError as error:
        available = ", ".join(sorted(OBJECTIVES))
        raise ValueError(f"Parque desconocido: {name}. Opciones: {available}.") from error
