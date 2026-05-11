"""Optimización de ubicación de router WiFi en espacio 3D."""

from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from core.particle import Vector
from core.types import ObjectiveDefinition

# Dispositivos fijos que necesitan cobertura WiFi
DEVICES: List[Tuple[float, float, float]] = [
    (0.0, 0.0, 1.5),    # Centro habitación principal
    (3.0, 2.0, 1.0),    # Habitación secundaria
    (-2.0, -1.5, 0.8),  # Cocina
    (1.5, -3.0, 1.2),   # Sala de estar
    (-1.0, 3.0, 0.5),   # Estudio
]

# Obstáculos simplificados: cajas (x_min, x_max, y_min, y_max, z_min, z_max)
OBSTACLES: List[Tuple[float, float, float, float, float, float]] = [
    (-0.5, 0.5, -0.5, 0.5, 0.0, 2.0),  # Pared central
    (1.0, 2.0, 1.0, 2.0, 0.0, 1.8),    # Mueble grande
    (-3.0, -2.0, 0.0, 1.0, 0.0, 2.5),  # Estantería
]

# Altura razonable para router (metros sobre el suelo)
MIN_HEIGHT = 2.0
MAX_HEIGHT = 4.0
HEIGHT_PENALTY_FACTOR = 10.0

# Factor de penalización por obstáculos
OBSTACLE_PENALTY_FACTOR = 50.0


def wifi_router(position: Vector) -> float:
    """Coste de ubicación del router WiFi considerando cobertura y obstáculos."""
    if len(position) != 3:
        raise ValueError("La posición del router debe ser 3D [x, y, z]")
    
    x, y, z = position
    
    # Coste base: suma de distancias euclidianas a dispositivos
    coverage_cost = sum(
        math.sqrt((x - dx)**2 + (y - dy)**2 + (z - dz)**2)
        for dx, dy, dz in DEVICES
    )
    
    # Penalización por altura no razonable
    height_penalty = 0.0
    if z < MIN_HEIGHT:
        height_penalty = HEIGHT_PENALTY_FACTOR * (MIN_HEIGHT - z)**2
    elif z > MAX_HEIGHT:
        height_penalty = HEIGHT_PENALTY_FACTOR * (z - MAX_HEIGHT)**2
    
    # Penalización por obstáculos
    obstacle_penalty = 0.0
    for ox_min, ox_max, oy_min, oy_max, oz_min, oz_max in OBSTACLES:
        if (ox_min <= x <= ox_max and 
            oy_min <= y <= oy_max and 
            oz_min <= z <= oz_max):
            # Centro del obstáculo para calcular distancia
            obstacle_center = (
                (ox_min + ox_max) / 2,
                (oy_min + oy_max) / 2,
                (oz_min + oz_max) / 2
            )
            distance_to_obstacle = math.sqrt(
                (x - obstacle_center[0])**2 +
                (y - obstacle_center[1])**2 +
                (z - obstacle_center[2])**2
            )
            obstacle_penalty += OBSTACLE_PENALTY_FACTOR / (distance_to_obstacle + 0.1)
    
    return coverage_cost + height_penalty + obstacle_penalty


def wifi_router_numpy(positions: np.ndarray) -> np.ndarray:
    """Versión vectorizada del coste de ubicación del router WiFi."""
    if positions.shape[1] != 3:
        raise ValueError("Las posiciones del router deben ser 3D")
    
    x = positions[:, 0:1]  # Shape (n, 1)
    y = positions[:, 1:2]
    z = positions[:, 2:3]
    
    # Coste base: suma de distancias euclidianas a dispositivos
    coverage_cost = np.zeros((positions.shape[0],), dtype=float)
    for dx, dy, dz in DEVICES:
        distances = np.sqrt((x - dx)**2 + (y - dy)**2 + (z - dz)**2)
        coverage_cost += distances.flatten()
    
    # Penalización por altura no razonable
    height_penalty = np.zeros_like(coverage_cost)
    too_low = z.flatten() < MIN_HEIGHT
    too_high = z.flatten() > MAX_HEIGHT
    
    height_penalty[too_low] = HEIGHT_PENALTY_FACTOR * (MIN_HEIGHT - z.flatten()[too_low])**2
    height_penalty[too_high] = HEIGHT_PENALTY_FACTOR * (z.flatten()[too_high] - MAX_HEIGHT)**2
    
    # Penalización por obstáculos
    obstacle_penalty = np.zeros_like(coverage_cost)
    for ox_min, ox_max, oy_min, oy_max, oz_min, oz_max in OBSTACLES:
        in_obstacle = (
            (x.flatten() >= ox_min) & (x.flatten() <= ox_max) &
            (y.flatten() >= oy_min) & (y.flatten() <= oy_max) &
            (z.flatten() >= oz_min) & (z.flatten() <= oz_max)
        )
        
        if np.any(in_obstacle):
            obstacle_center = (
                (ox_min + ox_max) / 2,
                (oy_min + oy_max) / 2,
                (oz_min + oz_max) / 2
            )
            distances = np.sqrt(
                (x.flatten()[in_obstacle] - obstacle_center[0])**2 +
                (y.flatten()[in_obstacle] - obstacle_center[1])**2 +
                (z.flatten()[in_obstacle] - obstacle_center[2])**2
            )
            obstacle_penalty[in_obstacle] += OBSTACLE_PENALTY_FACTOR / (distances + 0.1)
    
    return coverage_cost + height_penalty + obstacle_penalty


def wifi_router_definition() -> ObjectiveDefinition:
    return ObjectiveDefinition(
        name="wifi_router",
        description="Optimización de ubicación de router WiFi en espacio 3D con obstáculos.",
        scalar_function=wifi_router,
        vectorized_function=wifi_router_numpy,
        suggested_lower_bound=-10.0,
        suggested_upper_bound=10.0,
    )