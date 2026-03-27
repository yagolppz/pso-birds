"""Visualizaciones del vuelo del enjambre."""

from __future__ import annotations

import math

from .particle import Vector
from .swarm import FlightSnapshot, SwarmHistory


def render_convergence_svg(history: SwarmHistory, width: int = 900, height: int = 360) -> str:
    """Dibuja la ruta del tesoro de la bandada en formato SVG."""

    snapshots = _require_snapshots(history)
    padding = 40
    crumbs = [snapshot.treasure_crumbs for snapshot in snapshots]
    min_crumbs = min(crumbs)
    max_crumbs = max(crumbs)
    points: list[str] = []

    for index, snapshot in enumerate(snapshots):
        x = _scale_value(index, 0, max(1, len(snapshots) - 1), padding, width - padding)
        y = _scale_value(snapshot.treasure_crumbs, min_crumbs, max_crumbs, height - padding, padding)
        points.append(f"{x:.2f},{y:.2f}")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#f5efe2" />
  <rect x="{padding}" y="{padding}" width="{width - 2 * padding}" height="{height - 2 * padding}" fill="#fffaf0" stroke="#66513a" />
  <polyline fill="none" stroke="#bf5b04" stroke-width="3" points="{' '.join(points)}" />
  <text x="{padding}" y="24" font-size="18" fill="#3f2d1b">Migas del mejor sitio por vuelo</text>
  <text x="{padding}" y="{height - 10}" font-size="12" fill="#3f2d1b">Vuelos</text>
  <text x="{width - padding}" y="24" text-anchor="end" font-size="12" fill="#3f2d1b">Min: {min_crumbs:.6g} | Max: {max_crumbs:.6g}</text>
</svg>
"""


def render_swarm_2d_svg(
    history: SwarmHistory,
    width: int = 960,
    panel_height: int = 220,
    columns: int = 4,
) -> str:
    """Dibuja el estado 2D de la bandada en cada iteracion."""

    snapshots = _require_snapshots(history)
    _require_2d_snapshots(snapshots)

    columns = max(1, columns)
    panel_width = max(220, width // columns)
    rows = math.ceil(len(snapshots) / columns)
    total_height = rows * panel_height
    padding = 18
    plot_padding = 26
    x_min, x_max, y_min, y_max = _history_bounds_2d(snapshots)
    fragments: list[str] = []

    for index, snapshot in enumerate(snapshots):
        column = index % columns
        row = index // columns
        panel_x = column * panel_width
        panel_y = row * panel_height
        plot_x = panel_x + plot_padding
        plot_y = panel_y + 42
        plot_width = panel_width - 2 * plot_padding
        plot_height = panel_height - 58

        fragments.append(
            f'<g transform="translate({panel_x},{panel_y})">'
            f'<rect x="{padding / 2:.1f}" y="{padding / 2:.1f}" width="{panel_width - padding:.1f}" height="{panel_height - padding:.1f}" rx="10" fill="#fffaf0" stroke="#66513a" />'
            f'<text x="{plot_x}" y="24" font-size="15" fill="#3f2d1b">Vuelo {snapshot.flight_number}</text>'
            f'<text x="{plot_x}" y="38" font-size="11" fill="#6e5740">Best: {snapshot.treasure_crumbs:.6g}</text>'
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" fill="#f5efe2" stroke="#b89f7d" />'
            f'<text x="{plot_x}" y="{panel_height - 14}" font-size="10" fill="#6e5740">x [{x_min:.3g}, {x_max:.3g}]</text>'
            f'<text x="{plot_x + plot_width}" y="{panel_height - 14}" text-anchor="end" font-size="10" fill="#6e5740">y [{y_min:.3g}, {y_max:.3g}]</text>'
        )
        fragments.extend(
            _render_swarm_points(
                snapshot=snapshot,
                plot_x=plot_x,
                plot_y=plot_y,
                plot_width=plot_width,
                plot_height=plot_height,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
            )
        )
        fragments.append("</g>")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}">
  <rect width="{width}" height="{total_height}" fill="#efe7d6" />
  <text x="24" y="28" font-size="20" fill="#3f2d1b">Bandada 2D por vuelo</text>
  <text x="{width - 24}" y="28" text-anchor="end" font-size="12" fill="#6e5740">Azul: particulas | Naranja: mejor global</text>
  {''.join(fragments)}
</svg>
"""


def _require_snapshots(history: SwarmHistory) -> list[FlightSnapshot]:
    if not history.snapshots:
        raise ValueError("No hay vuelos registrados para dibujar.")
    return history.snapshots


def _require_2d_snapshots(snapshots: list[FlightSnapshot]) -> None:
    for snapshot in snapshots:
        if len(snapshot.treasure_position) != 2:
            raise ValueError("La visualizacion 2D necesita exactamente dos dimensiones.")
        if snapshot.particle_positions is None:
            raise ValueError("La historia no incluye posiciones de particulas para dibujar la bandada.")
        for position in snapshot.particle_positions:
            if len(position) != 2:
                raise ValueError("La visualizacion 2D necesita posiciones de particulas en dos dimensiones.")


def _history_bounds_2d(snapshots: list[FlightSnapshot]) -> tuple[float, float, float, float]:
    x_values: list[float] = []
    y_values: list[float] = []

    for snapshot in snapshots:
        assert snapshot.particle_positions is not None
        for x_value, y_value in snapshot.particle_positions:
            x_values.append(x_value)
            y_values.append(y_value)
        x_values.append(snapshot.treasure_position[0])
        y_values.append(snapshot.treasure_position[1])

    x_min, x_max = _expand_axis_bounds(min(x_values), max(x_values))
    y_min, y_max = _expand_axis_bounds(min(y_values), max(y_values))
    return x_min, x_max, y_min, y_max


def _render_swarm_points(
    snapshot: FlightSnapshot,
    plot_x: float,
    plot_y: float,
    plot_width: float,
    plot_height: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> list[str]:
    assert snapshot.particle_positions is not None

    fragments: list[str] = []
    for position in snapshot.particle_positions:
        x_pos, y_pos = _project_point_2d(position, plot_x, plot_y, plot_width, plot_height, x_min, x_max, y_min, y_max)
        fragments.append(
            f'<circle cx="{x_pos:.2f}" cy="{y_pos:.2f}" r="4.2" fill="#2f6c8f" fill-opacity="0.78" stroke="#163848" stroke-width="0.7" />'
        )

    treasure_x, treasure_y = _project_point_2d(
        snapshot.treasure_position,
        plot_x,
        plot_y,
        plot_width,
        plot_height,
        x_min,
        x_max,
        y_min,
        y_max,
    )
    fragments.append(
        f'<circle cx="{treasure_x:.2f}" cy="{treasure_y:.2f}" r="7" fill="#e07a1f" stroke="#8b3d09" stroke-width="1.5" />'
    )
    fragments.append(
        f'<circle cx="{treasure_x:.2f}" cy="{treasure_y:.2f}" r="11" fill="none" stroke="#e07a1f" stroke-width="1.2" stroke-dasharray="4 3" />'
    )
    return fragments


def _project_point_2d(
    point: Vector,
    plot_x: float,
    plot_y: float,
    plot_width: float,
    plot_height: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[float, float]:
    x_pos = _scale_value(point[0], x_min, x_max, plot_x, plot_x + plot_width)
    y_pos = _scale_value(point[1], y_min, y_max, plot_y + plot_height, plot_y)
    return x_pos, y_pos


def _expand_axis_bounds(lower: float, upper: float) -> tuple[float, float]:
    if lower == upper:
        margin = 1.0 if lower == 0.0 else abs(lower) * 0.1
        return lower - margin, upper + margin
    span = upper - lower
    margin = span * 0.05
    return lower - margin, upper + margin


def _scale_value(value: float, data_min: float, data_max: float, target_min: float, target_max: float) -> float:
    if data_min == data_max:
        return (target_min + target_max) / 2.0
    ratio = (value - data_min) / (data_max - data_min)
    return target_min + ratio * (target_max - target_min)
