"""Visualizaciones estaticas y animadas del vuelo del enjambre."""

from __future__ import annotations

import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

from core.config import SearchSpaceConfig
from core.particle import Vector
from core.swarm import FlightSnapshot, SwarmHistory
from core.types import ObjectiveDefinition


def render_convergence_svg(history: SwarmHistory, width: int = 900, height: int = 360) -> str:
    """Dibuja la ruta del mejor fitness por iteracion."""

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
  <text x="{padding}" y="24" font-size="18" fill="#3f2d1b">Best fitness por iteracion</text>
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
    """Dibuja una cuadricula de snapshots del enjambre 2D."""

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


def write_visualization_artifacts(
    directory: Path,
    history: SwarmHistory,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
    include_animation_assets: bool = True,
) -> None:
    """Escribe visualizaciones del vuelo del enjambre."""

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "convergence.svg").write_text(render_convergence_svg(history), encoding="utf-8")

    if not include_animation_assets:
        return

    if search_space.dimensions == 2:
        (directory / "swarm_2d.svg").write_text(render_swarm_2d_svg(history), encoding="utf-8")
        frames = write_swarm_2d_frames(directory / "swarm_2d_frames", history, objective, search_space)
        (directory / "swarm_2d.html").write_text(
            render_animation_html(
                title=f"PSO Birds 2D - {objective.name}",
                frames=frames,
                history=history,
                convergence_filename="convergence.svg",
                dimension_label="2D",
                note="Frames SVG + reproductor HTML. El fondo incluye un contorno aproximado de la funcion objetivo.",
            ),
            encoding="utf-8",
        )
    if search_space.dimensions == 3:
        frames = write_swarm_3d_frames(directory / "swarm_3d_frames", history, objective, search_space)
        (directory / "swarm_3d.html").write_text(
            render_animation_html(
                title=f"PSO Birds 3D - {objective.name}",
                frames=frames,
                history=history,
                convergence_filename="convergence.svg",
                dimension_label="3D",
                note="Frames SVG + reproductor HTML. Cada frame muestra el enjambre en 3D y una superficie de corte de la funcion.",
            ),
            encoding="utf-8",
        )


def write_swarm_2d_frames(
    directory: Path,
    history: SwarmHistory,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
) -> list[str]:
    """Genera frames numerados SVG para la animacion 2D."""

    snapshots = _require_snapshots(history)
    _require_2d_snapshots(snapshots)
    directory.mkdir(parents=True, exist_ok=True)
    grid = _sample_objective_grid(objective, search_space, fixed_tail=[])
    frame_names: list[str] = []
    for index, snapshot in enumerate(snapshots):
        frame_name = f"frame_{index:03d}.svg"
        frame_names.append(f"{directory.name}/{frame_name}")
        (directory / frame_name).write_text(
            render_swarm_2d_frame_svg(snapshot, search_space, grid),
            encoding="utf-8",
        )
    return frame_names


def write_swarm_3d_frames(
    directory: Path,
    history: SwarmHistory,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
) -> list[str]:
    """Genera frames numerados SVG para la animacion 3D."""

    snapshots = _require_snapshots(history)
    _require_3d_snapshots(snapshots)
    directory.mkdir(parents=True, exist_ok=True)
    z_slice = snapshots[-1].treasure_position[2]
    grid = _sample_objective_grid(objective, search_space, fixed_tail=[z_slice])
    frame_names: list[str] = []
    for index, snapshot in enumerate(snapshots):
        frame_name = f"frame_{index:03d}.svg"
        frame_names.append(f"{directory.name}/{frame_name}")
        (directory / frame_name).write_text(
            render_swarm_3d_frame_svg(snapshot, search_space, grid, z_slice),
            encoding="utf-8",
        )
    return frame_names


def render_animation_html(
    title: str,
    frames: list[str],
    history: SwarmHistory,
    convergence_filename: str,
    dimension_label: str,
    note: str,
) -> str:
    """Construye un reproductor HTML ligero para los frames generados."""

    snapshots = _require_snapshots(history)
    metadata = [
        {
            "flight_number": snapshot.flight_number,
            "best_crumbs": snapshot.treasure_crumbs,
            "particles": len(snapshot.particle_positions or []),
        }
        for snapshot in snapshots
    ]
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ margin: 0; background: #efe7d6; color: #2d2217; font-family: Georgia, serif; }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    .layout {{ display: grid; grid-template-columns: 2fr 1fr; gap: 18px; }}
    .panel {{ background: #fffaf0; border: 1px solid #7c6248; border-radius: 14px; padding: 14px; box-shadow: 0 12px 28px rgba(70, 43, 12, 0.08); }}
    h1, h2 {{ margin-top: 0; }}
    img {{ width: 100%; display: block; border-radius: 10px; border: 1px solid #b89f7d; background: #f5efe2; }}
    .controls {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 12px; }}
    .controls button {{ border: 1px solid #7c6248; background: #bf5b04; color: #fffaf0; border-radius: 999px; padding: 8px 16px; cursor: pointer; }}
    .controls input {{ flex: 1; min-width: 240px; }}
    .stats {{ display: grid; grid-template-columns: repeat(2, minmax(140px, 1fr)); gap: 10px; margin-top: 14px; }}
    .stat {{ background: #f7f0e4; border: 1px solid #d7c2a5; border-radius: 10px; padding: 10px 12px; }}
    .stat strong {{ display: block; font-size: 12px; color: #6e5740; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
    .note {{ color: #6e5740; line-height: 1.4; }}
    @media (max-width: 980px) {{ .layout {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="page">
    <h1>{title}</h1>
    <div class="layout">
      <section class="panel">
        <h2>Animacion {dimension_label}</h2>
        <img id="frame-viewer" src="{frames[0]}" alt="Frame de la animacion" />
        <div class="controls">
          <button id="toggle" type="button">Pausar</button>
          <input id="frame-slider" type="range" min="0" max="{max(0, len(frames) - 1)}" value="0" />
        </div>
        <div class="stats">
          <div class="stat"><strong>Vista</strong><span>{dimension_label}</span></div>
          <div class="stat"><strong>Vuelo</strong><span id="flight-value">{metadata[0]['flight_number']}</span></div>
          <div class="stat"><strong>Best Fitness</strong><span id="best-value">{metadata[0]['best_crumbs']:.6g}</span></div>
          <div class="stat"><strong>Particulas</strong><span id="particles-value">{metadata[0]['particles']}</span></div>
        </div>
        <p class="note">{note}</p>
      </section>
      <aside class="panel">
        <h2>Curva de convergencia</h2>
        <img src="{convergence_filename}" alt="Curva de convergencia" />
        <p class="note">La metrica best fitness vs iteracion se mantiene en <code>convergence.svg</code>.</p>
      </aside>
    </div>
  </div>
  <script>
    const frames = {json.dumps(frames, ensure_ascii=True)};
    const metadata = {json.dumps(metadata, ensure_ascii=True)};
    const viewer = document.getElementById('frame-viewer');
    const slider = document.getElementById('frame-slider');
    const toggle = document.getElementById('toggle');
    const flightValue = document.getElementById('flight-value');
    const bestValue = document.getElementById('best-value');
    const particlesValue = document.getElementById('particles-value');
    let current = 0;
    let playing = true;
    let lastStep = 0;

    function render(index) {{
      current = index;
      viewer.src = frames[index];
      slider.value = String(index);
      flightValue.textContent = String(metadata[index].flight_number);
      bestValue.textContent = Number(metadata[index].best_crumbs).toPrecision(6);
      particlesValue.textContent = String(metadata[index].particles);
    }}

    slider.addEventListener('input', () => render(Number(slider.value)));
    toggle.addEventListener('click', () => {{
      playing = !playing;
      toggle.textContent = playing ? 'Pausar' : 'Reproducir';
    }});

    function tick(timestamp) {{
      if (playing && frames.length > 1 && timestamp - lastStep > 480) {{
        lastStep = timestamp;
        render((current + 1) % frames.length);
      }}
      window.requestAnimationFrame(tick);
    }}

    render(0);
    window.requestAnimationFrame(tick);
  </script>
</body>
</html>
"""


def render_swarm_2d_frame_svg(
    snapshot: FlightSnapshot,
    search_space: SearchSpaceConfig,
    grid: dict[str, object],
    width: int = 920,
    height: int = 520,
) -> str:
    """Renderiza un frame 2D con contorno, particulas y mejor global."""

    assert snapshot.particle_positions is not None
    padding = 48
    plot_width = width - 2 * padding
    plot_height = height - 2 * padding
    cells = _render_contour_cells(grid, padding, padding, plot_width, plot_height)
    points: list[str] = []
    for position in snapshot.particle_positions:
        x_value = _scale_value(position[0], search_space.lower_bound, search_space.upper_bound, padding, width - padding)
        y_value = _scale_value(position[1], search_space.lower_bound, search_space.upper_bound, height - padding, padding)
        points.append(
            f'<circle cx="{x_value:.2f}" cy="{y_value:.2f}" r="5.6" fill="#2f6c8f" fill-opacity="0.84" stroke="#163848" stroke-width="1.0" />'
        )
    best_x = _scale_value(snapshot.treasure_position[0], search_space.lower_bound, search_space.upper_bound, padding, width - padding)
    best_y = _scale_value(snapshot.treasure_position[1], search_space.lower_bound, search_space.upper_bound, height - padding, padding)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#efe7d6" />
  <rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="14" fill="#fffaf0" stroke="#66513a" />
  <text x="36" y="36" font-size="22" fill="#3f2d1b">Enjambre 2D - vuelo {snapshot.flight_number}</text>
  <text x="{width - 36}" y="36" text-anchor="end" font-size="13" fill="#6e5740">Best fitness: {snapshot.treasure_crumbs:.6g}</text>
  <rect x="{padding}" y="{padding}" width="{plot_width}" height="{plot_height}" fill="#f5efe2" stroke="#9d8466" />
  {cells}
  <rect x="{padding}" y="{padding}" width="{plot_width}" height="{plot_height}" fill="none" stroke="#7c6248" stroke-width="1.2" />
  {''.join(points)}
  <circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="8.8" fill="#e07a1f" stroke="#8b3d09" stroke-width="2.0" />
  <circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="16" fill="none" stroke="#e07a1f" stroke-width="1.3" stroke-dasharray="4 3" />
  <text x="{padding}" y="{height - 16}" font-size="12" fill="#6e5740">x,y en [{search_space.lower_bound:.3g}, {search_space.upper_bound:.3g}]</text>
</svg>
"""


def render_swarm_3d_frame_svg(
    snapshot: FlightSnapshot,
    search_space: SearchSpaceConfig,
    grid: dict[str, object],
    z_slice: float,
    width: int = 1180,
    height: int = 480,
) -> str:
    """Renderiza un frame 3D con particulas y superficie de corte."""

    assert snapshot.particle_positions is not None
    left_panel_width = 500
    right_panel_width = 604
    content_height = height - 112
    left = _render_swarm_3d_left_panel(snapshot, search_space, width=left_panel_width, height=content_height)
    right = _render_surface_panel(snapshot, search_space, grid, z_slice, width=right_panel_width, height=content_height)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#efe7d6" />
  <rect x="16" y="16" width="{width - 32}" height="{height - 32}" rx="14" fill="#fffaf0" stroke="#66513a" />
  <text x="32" y="36" font-size="21" fill="#3f2d1b">Enjambre 3D - vuelo {snapshot.flight_number}</text>
  <text x="32" y="54" font-size="12" fill="#6e5740">Azul: particulas | Naranja: mejor global</text>
  <text x="{width - 32}" y="45" text-anchor="end" font-size="13" fill="#6e5740">Best fitness: {snapshot.treasure_crumbs:.6g}</text>
  <rect x="24" y="68" width="{left_panel_width + 16}" height="{content_height + 12}" rx="12" fill="#f7f0e4" stroke="#cfb899" />
  <rect x="548" y="68" width="{right_panel_width + 16}" height="{content_height + 12}" rx="12" fill="#f7f0e4" stroke="#cfb899" />
  <g transform="translate(32, 78)">{left}</g>
  <g transform="translate(556, 78)">{right}</g>
</svg>
"""


def render_swarm_surface_3d_frame_svg(
    snapshot: FlightSnapshot,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
    grid: dict[str, object],
    width: int = 1180,
    height: int = 480,
) -> str:
    """Renderiza una vista 3D de la funcion 2D con el enjambre sobre la superficie."""

    left_panel_width = 500
    right_panel_width = 604
    content_height = height - 112
    left = _render_swarm_surface_left_panel(snapshot, objective, search_space, grid, width=left_panel_width, height=content_height)
    right = _render_surface_panel(
        snapshot,
        search_space,
        grid,
        0.0,
        width=right_panel_width,
        height=content_height,
        subtitle="f(x, y)",
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#efe7d6" />
  <rect x="16" y="16" width="{width - 32}" height="{height - 32}" rx="14" fill="#fffaf0" stroke="#66513a" />
  <text x="32" y="36" font-size="21" fill="#3f2d1b">Enjambre 3D - vuelo {snapshot.flight_number}</text>
  <text x="32" y="54" font-size="12" fill="#6e5740">Azul: particulas | Naranja: mejor global</text>
  <text x="{width - 32}" y="45" text-anchor="end" font-size="13" fill="#6e5740">Best fitness: {snapshot.treasure_crumbs:.6g}</text>
  <rect x="24" y="68" width="{left_panel_width + 16}" height="{content_height + 12}" rx="12" fill="#f7f0e4" stroke="#cfb899" />
  <rect x="548" y="68" width="{right_panel_width + 16}" height="{content_height + 12}" rx="12" fill="#f7f0e4" stroke="#cfb899" />
  <g transform="translate(32, 78)">{left}</g>
  <g transform="translate(556, 78)">{right}</g>
</svg>
"""


def _render_swarm_surface_left_panel(
    snapshot: FlightSnapshot,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
    grid: dict[str, object],
    width: int,
    height: int,
) -> str:
    xy_bounds = (search_space.lower_bound, search_space.upper_bound)
    z_bounds = (grid["z_min"], grid["z_max"])
    origin_x, origin_y, scale = _fit_surface_projection(
        grid=grid,
        xy_bounds=xy_bounds,
        z_bounds=z_bounds,
        width=width,
        height=height,
    )
    particles: list[str] = []
    assert snapshot.particle_positions is not None
    for position in snapshot.particle_positions:
        surface_value = objective.scalar_function(position[:2])
        x_value, y_value = _project_surface_point(
            position[0],
            position[1],
            surface_value,
            xy_bounds,
            z_bounds,
            origin_x,
            origin_y,
            scale,
        )
        particles.append(
            f'<circle cx="{x_value:.2f}" cy="{y_value:.2f}" r="5.6" fill="#2f6c8f" fill-opacity="0.84" stroke="#163848" stroke-width="1.0" />'
        )
    best_x, best_y = _project_surface_point(
        snapshot.treasure_position[0],
        snapshot.treasure_position[1],
        snapshot.treasure_crumbs,
        xy_bounds,
        z_bounds,
        origin_x,
        origin_y,
        scale,
    )
    return f"""
  <text x="16" y="20" font-size="17" fill="#3f2d1b">Posiciones del enjambre</text>
  <text x="16" y="40" font-size="12" fill="#6e5740">Proyeccion isometrica del enjambre sobre f(x, y)</text>
  {''.join(particles)}
  <circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="8.8" fill="#e07a1f" stroke="#8b3d09" stroke-width="2.0" />
  <circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="16" fill="none" stroke="#e07a1f" stroke-width="1.3" stroke-dasharray="4 3" />
"""


def _render_swarm_3d_left_panel(snapshot: FlightSnapshot, search_space: SearchSpaceConfig, width: int, height: int) -> str:
    bounds = (search_space.lower_bound, search_space.upper_bound)
    origin_x, origin_y, scale = _fit_iso_cube_projection(bounds, width, height)
    axis_points = [
        _project_iso_3d([bounds[0], bounds[0], bounds[0]], bounds, origin_x, origin_y, scale),
        _project_iso_3d([bounds[1], bounds[0], bounds[0]], bounds, origin_x, origin_y, scale),
        _project_iso_3d([bounds[0], bounds[1], bounds[0]], bounds, origin_x, origin_y, scale),
        _project_iso_3d([bounds[0], bounds[0], bounds[1]], bounds, origin_x, origin_y, scale),
    ]
    particles = []
    assert snapshot.particle_positions is not None
    for position in snapshot.particle_positions:
        x_value, y_value = _project_iso_3d(position, bounds, origin_x, origin_y, scale)
        particles.append(
            f'<circle cx="{x_value:.2f}" cy="{y_value:.2f}" r="5.6" fill="#2f6c8f" fill-opacity="0.84" stroke="#163848" stroke-width="1.0" />'
        )
    best_x, best_y = _project_iso_3d(snapshot.treasure_position, bounds, origin_x, origin_y, scale)
    return f"""
  <text x="16" y="20" font-size="17" fill="#3f2d1b">Posiciones del enjambre</text>
  <text x="16" y="40" font-size="12" fill="#6e5740">Proyeccion isometrica del espacio de busqueda 3D</text>
  <line x1="{axis_points[0][0]:.2f}" y1="{axis_points[0][1]:.2f}" x2="{axis_points[1][0]:.2f}" y2="{axis_points[1][1]:.2f}" stroke="#7c6248" stroke-width="1.5" />
  <line x1="{axis_points[0][0]:.2f}" y1="{axis_points[0][1]:.2f}" x2="{axis_points[2][0]:.2f}" y2="{axis_points[2][1]:.2f}" stroke="#7c6248" stroke-width="1.5" />
  <line x1="{axis_points[0][0]:.2f}" y1="{axis_points[0][1]:.2f}" x2="{axis_points[3][0]:.2f}" y2="{axis_points[3][1]:.2f}" stroke="#7c6248" stroke-width="1.5" />
  {''.join(particles)}
  <circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="8.8" fill="#e07a1f" stroke="#8b3d09" stroke-width="2.0" />
  <circle cx="{best_x:.2f}" cy="{best_y:.2f}" r="16" fill="none" stroke="#e07a1f" stroke-width="1.3" stroke-dasharray="4 3" />
"""


def _render_surface_panel(
    snapshot: FlightSnapshot,
    search_space: SearchSpaceConfig,
    grid: dict[str, object],
    z_slice: float,
    width: int,
    height: int,
    subtitle: str | None = None,
) -> str:
    x_values = grid["x_values"]
    y_values = grid["y_values"]
    z_values = grid["z_values"]
    z_bounds = (grid["z_min"], grid["z_max"])
    xy_bounds = (search_space.lower_bound, search_space.upper_bound)
    origin_x, origin_y, scale = _fit_surface_projection(
        grid=grid,
        xy_bounds=xy_bounds,
        z_bounds=z_bounds,
        width=width,
        height=height,
    )
    surface_subtitle = subtitle or f"f(x, y, z_const) con z_const = {z_slice:.6g}"
    lines: list[str] = [
        '<text x="16" y="20" font-size="17" fill="#3f2d1b">Superficie de corte de la funcion</text>',
        f'<text x="16" y="40" font-size="12" fill="#6e5740">{surface_subtitle}</text>',
    ]

    for row_index, y_value in enumerate(y_values):
        projected_row = [
            _project_surface_point(x_value, y_value, z_values[row_index][column_index], xy_bounds, z_bounds, origin_x, origin_y, scale)
            for column_index, x_value in enumerate(x_values)
        ]
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in projected_row)
        lines.append(f'<polyline fill="none" stroke="#8f6b3d" stroke-width="1" points="{points}" />')

    for column_index, x_value in enumerate(x_values):
        projected_column = [
            _project_surface_point(x_value, y_value, z_values[row_index][column_index], xy_bounds, z_bounds, origin_x, origin_y, scale)
            for row_index, y_value in enumerate(y_values)
        ]
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in projected_column)
        lines.append(f'<polyline fill="none" stroke="#b9894f" stroke-width="1" points="{points}" />')

    marker_value = _surface_marker_value(snapshot, z_slice, z_bounds)
    marker_x, marker_y = _project_surface_point(
        snapshot.treasure_position[0],
        snapshot.treasure_position[1],
        marker_value,
        xy_bounds,
        z_bounds,
        origin_x,
        origin_y,
        scale,
    )
    lines.append(f'<circle cx="{marker_x:.2f}" cy="{marker_y:.2f}" r="7" fill="#e07a1f" stroke="#8b3d09" stroke-width="1.8" />')
    lines.append(f'<text x="16" y="{height - 18}" font-size="12" fill="#6e5740">Rango z proyectado: [{z_bounds[0]:.3g}, {z_bounds[1]:.3g}]</text>')
    return "".join(lines)


def _surface_marker_value(
    snapshot: FlightSnapshot,
    z_slice: float,
    z_bounds: tuple[float, float],
) -> float:
    if len(snapshot.treasure_position) < 3:
        return max(z_bounds[0], min(z_bounds[1], snapshot.treasure_crumbs))
    marker_value = snapshot.treasure_crumbs + abs(snapshot.treasure_position[2] - z_slice) * 0.0
    return max(z_bounds[0], min(z_bounds[1], marker_value))


def _render_contour_cells(
    grid: dict[str, object],
    plot_x: float,
    plot_y: float,
    plot_width: float,
    plot_height: float,
) -> str:
    cells: list[str] = []
    x_values = grid["x_values"]
    y_values = grid["y_values"]
    z_values = grid["z_values"]
    x_step = plot_width / max(1, len(x_values) - 1)
    y_step = plot_height / max(1, len(y_values) - 1)
    for row_index in range(len(y_values) - 1):
        for column_index in range(len(x_values) - 1):
            color = _color_for_value(z_values[row_index][column_index], grid["z_min"], grid["z_max"])
            x_value = plot_x + column_index * x_step
            y_value = plot_y + plot_height - (row_index + 1) * y_step
            cells.append(
                f'<rect x="{x_value:.2f}" y="{y_value:.2f}" width="{x_step + 1:.2f}" height="{y_step + 1:.2f}" fill="{color}" />'
            )
    return "".join(cells)


def _sample_objective_grid(
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
    fixed_tail: list[float],
    grid_points: int = 26,
) -> dict[str, object]:
    x_values = [
        search_space.lower_bound + (search_space.upper_bound - search_space.lower_bound) * index / max(1, grid_points - 1)
        for index in range(grid_points)
    ]
    y_values = [
        search_space.lower_bound + (search_space.upper_bound - search_space.lower_bound) * index / max(1, grid_points - 1)
        for index in range(grid_points)
    ]
    z_values: list[list[float]] = []
    for y_value in y_values:
        row: list[float] = []
        for x_value in x_values:
            row.append(objective.scalar_function([x_value, y_value, *fixed_tail]))
        z_values.append(row)
    flattened = [value for row in z_values for value in row]
    z_min, z_max = _expand_axis_bounds(min(flattened), max(flattened))
    return {
        "x_values": x_values,
        "y_values": y_values,
        "z_values": z_values,
        "z_min": z_min,
        "z_max": z_max,
    }


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


def _require_3d_snapshots(snapshots: list[FlightSnapshot]) -> None:
    for snapshot in snapshots:
        if len(snapshot.treasure_position) != 3:
            raise ValueError("La visualizacion 3D necesita exactamente tres dimensiones.")
        if snapshot.particle_positions is None:
            raise ValueError("La historia no incluye posiciones de particulas para dibujar la bandada.")
        for position in snapshot.particle_positions:
            if len(position) != 3:
                raise ValueError("La visualizacion 3D necesita posiciones de particulas en tres dimensiones.")


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


def _project_iso_3d(point: Vector, bounds: tuple[float, float], origin_x: float, origin_y: float, scale: float) -> tuple[float, float]:
    projected_x_component, projected_y_component = _iso_project_components(point, bounds)
    x_value = origin_x + projected_x_component * scale
    y_value = origin_y + projected_y_component * scale
    return x_value, y_value


def _project_surface_point(
    x_value: float,
    y_value: float,
    z_value: float,
    xy_bounds: tuple[float, float],
    z_bounds: tuple[float, float],
    origin_x: float,
    origin_y: float,
    scale: float,
) -> tuple[float, float]:
    projected_x_component, projected_y_component = _surface_project_components(x_value, y_value, z_value, xy_bounds, z_bounds)
    projected_x = origin_x + projected_x_component * scale
    projected_y = origin_y + projected_y_component * scale
    return projected_x, projected_y


def _iso_project_components(point: Vector, bounds: tuple[float, float]) -> tuple[float, float]:
    normalized = [
        _scale_value(coordinate, bounds[0], bounds[1], -1.0, 1.0)
        for coordinate in point[:3]
    ]
    return normalized[0] - normalized[1], -(normalized[0] + normalized[1]) * 0.45 - normalized[2]


def _surface_project_components(
    x_value: float,
    y_value: float,
    z_value: float,
    xy_bounds: tuple[float, float],
    z_bounds: tuple[float, float],
) -> tuple[float, float]:
    normalized_x = _scale_value(x_value, xy_bounds[0], xy_bounds[1], -1.0, 1.0)
    normalized_y = _scale_value(y_value, xy_bounds[0], xy_bounds[1], -1.0, 1.0)
    normalized_z = _scale_value(z_value, z_bounds[0], z_bounds[1], -1.0, 1.0)
    return normalized_x - normalized_y, -(normalized_x + normalized_y) * 0.38 - normalized_z * 1.1


def _fit_iso_cube_projection(bounds: tuple[float, float], width: int, height: int) -> tuple[float, float, float]:
    components = [
        _iso_project_components([x_value, y_value, z_value], bounds)
        for x_value in bounds
        for y_value in bounds
        for z_value in bounds
    ]
    return _fit_projected_components(
        components,
        width=width,
        height=height,
        left_margin=58.0,
        right_margin=50.0,
        top_margin=82.0,
        bottom_margin=66.0,
        content_padding=24.0,
    )


def _fit_surface_projection(
    grid: dict[str, object],
    xy_bounds: tuple[float, float],
    z_bounds: tuple[float, float],
    width: int,
    height: int,
) -> tuple[float, float, float]:
    components = [
        _surface_project_components(x_value, y_value, grid["z_values"][row_index][column_index], xy_bounds, z_bounds)
        for row_index, y_value in enumerate(grid["y_values"])
        for column_index, x_value in enumerate(grid["x_values"])
    ]
    return _fit_projected_components(
        components,
        width=width,
        height=height,
        left_margin=52.0,
        right_margin=42.0,
        top_margin=78.0,
        bottom_margin=44.0,
        content_padding=20.0,
    )


def _fit_projected_components(
    components: list[tuple[float, float]],
    width: int,
    height: int,
    left_margin: float,
    right_margin: float,
    top_margin: float,
    bottom_margin: float,
    content_padding: float = 0.0,
) -> tuple[float, float, float]:
    min_x = min(point[0] for point in components)
    max_x = max(point[0] for point in components)
    min_y = min(point[1] for point in components)
    max_y = max(point[1] for point in components)
    available_width = max(1.0, width - left_margin - right_margin - 2.0 * content_padding)
    available_height = max(1.0, height - top_margin - bottom_margin - 2.0 * content_padding)
    span_x = max(1e-9, max_x - min_x)
    span_y = max(1e-9, max_y - min_y)
    scale = min(available_width / span_x, available_height / span_y)
    origin_x = left_margin + content_padding + (available_width - span_x * scale) / 2.0 - min_x * scale
    origin_y = top_margin + content_padding + (available_height - span_y * scale) / 2.0 - min_y * scale
    return origin_x, origin_y, scale


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


def _color_for_value(value: float, lower: float, upper: float) -> str:
    palette = ["#f6f2d5", "#e8d9a5", "#d9b46b", "#c4893a", "#9d5b17", "#6b350d"]
    if upper == lower:
        return palette[0]
    ratio = max(0.0, min(0.9999, (value - lower) / (upper - lower)))
    return palette[min(len(palette) - 1, int(ratio * len(palette)))]


def export_animation(
    directory: Path,
    export_format: str,
    history: SwarmHistory | None = None,
    objective: ObjectiveDefinition | None = None,
    search_space: SearchSpaceConfig | None = None,
) -> Path | None:
    """Exporta solo las animaciones finales 2D y 3D, sin alias redundantes."""

    if export_format == "none":
        return None

    animations, primary_label = _collect_named_animation_images(directory, history, objective, search_space)
    if not animations:
        return None

    legacy_path = directory / f"animation.{export_format}"
    if legacy_path.exists():
        legacy_path.unlink()

    primary_path: Path | None = None
    for label, images in animations.items():
        output_path = directory / f"{label}.{export_format}"
        _save_animation(images, output_path, export_format)
        if label == primary_label:
            primary_path = output_path

    return primary_path


def _save_animation(images: list[Image.Image], output_path: Path, export_format: str) -> None:
    if export_format == "gif":
        palette_frames = [image.convert("P", palette=Image.ADAPTIVE) for image in images]
        palette_frames[0].save(
            output_path,
            save_all=True,
            append_images=palette_frames[1:],
            duration=480,
            loop=0,
            disposal=2,
        )
        return

    if export_format == "mp4":
        try:
            import imageio.v2 as imageio
            import numpy as np
        except ModuleNotFoundError as error:
            raise RuntimeError("La exportacion MP4 requiere imageio instalado.") from error

        frames = [np.asarray(image.convert("RGB")) for image in images]
        imageio.mimsave(output_path, frames, fps=2)
        return

    raise ValueError(f"Formato de exportacion desconocido: {export_format}")


def _collect_named_animation_images(
    directory: Path,
    history: SwarmHistory | None,
    objective: ObjectiveDefinition | None,
    search_space: SearchSpaceConfig | None,
) -> tuple[dict[str, list[Image.Image]], str]:
    if history is not None and objective is not None and search_space is not None:
        return _render_named_animation_images(history, objective, search_space)

    frame_paths = _discover_animation_frames(directory)
    if not frame_paths:
        raise ValueError("No hay frames generados para exportar animacion.")
    return {"animation_2d": [_svg_frame_to_image(path) for path in frame_paths]}, "animation_2d"


def _render_named_animation_images(
    history: SwarmHistory,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
) -> tuple[dict[str, list[Image.Image]], str]:
    snapshots = _require_snapshots(history)
    if search_space.dimensions == 2:
        _require_2d_snapshots(snapshots)
        grid = _sample_objective_grid(objective, search_space, fixed_tail=[])
        return (
            {
                "animation_2d": [
                    _svg_markup_to_image(render_swarm_2d_frame_svg(snapshot, search_space, grid))
                    for snapshot in snapshots
                ],
                "animation_3d": [
                    _svg_markup_to_image(render_swarm_surface_3d_frame_svg(snapshot, objective, search_space, grid))
                    for snapshot in snapshots
                ],
            },
            "animation_2d",
        )
    if search_space.dimensions == 3:
        _require_3d_snapshots(snapshots)
        z_slice = snapshots[-1].treasure_position[2]
        grid = _sample_objective_grid(objective, search_space, fixed_tail=[z_slice])
        return (
            {
                "animation_2d": [
                    _svg_markup_to_image(render_swarm_2d_frame_svg(snapshot, search_space, grid))
                    for snapshot in snapshots
                ],
                "animation_3d": [
                    _svg_markup_to_image(render_swarm_3d_frame_svg(snapshot, search_space, grid, z_slice))
                    for snapshot in snapshots
                ],
            },
            "animation_3d",
        )
    raise ValueError("La exportacion de animaciones solo esta disponible para 2D y 3D.")


def _collect_animation_images(
    directory: Path,
    history: SwarmHistory | None,
    objective: ObjectiveDefinition | None,
    search_space: SearchSpaceConfig | None,
) -> list[Image.Image]:
    animations, legacy_label = _collect_named_animation_images(directory, history, objective, search_space)
    return animations[legacy_label]


def _render_animation_images(
    history: SwarmHistory,
    objective: ObjectiveDefinition,
    search_space: SearchSpaceConfig,
) -> list[Image.Image]:
    animations, legacy_label = _render_named_animation_images(history, objective, search_space)
    return animations[legacy_label]


def _discover_animation_frames(directory: Path) -> list[Path]:
    for folder_name in ("swarm_2d_frames", "swarm_3d_frames"):
        frame_directory = directory / folder_name
        if frame_directory.exists():
            return sorted(frame_directory.glob("frame_*.svg")) or sorted(frame_directory.glob("frame_*.png"))
    return []


def _svg_frame_to_image(path: Path) -> Image.Image:
    if path.suffix.lower() == ".png":
        return Image.open(path).convert("RGBA")
    return _svg_markup_to_image(path.read_text(encoding="utf-8"))


def _svg_markup_to_image(svg_markup: str) -> Image.Image:
    root = ET.fromstring(svg_markup)
    width = int(float(root.attrib.get("width", "960")))
    height = int(float(root.attrib.get("height", "540")))
    image = Image.new("RGBA", (width, height), (255, 250, 240, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default()
    _draw_svg_node(draw, root, font, 0.0, 0.0)
    return image


def _draw_svg_node(
    draw: ImageDraw.ImageDraw,
    element: ET.Element,
    font: ImageFont.ImageFont,
    offset_x: float,
    offset_y: float,
) -> None:
    tag = element.tag.rsplit("}", 1)[-1]
    translate_x, translate_y = _parse_translate(element.attrib.get("transform"))
    current_x = offset_x + translate_x
    current_y = offset_y + translate_y

    if tag == "g":
        for child in element:
            _draw_svg_node(draw, child, font, current_x, current_y)
        return

    if tag == "rect":
        x0 = current_x + float(element.attrib.get("x", "0"))
        y0 = current_y + float(element.attrib.get("y", "0"))
        x1 = x0 + float(element.attrib.get("width", "0"))
        y1 = y0 + float(element.attrib.get("height", "0"))
        fill = _parse_svg_color(element.attrib.get("fill"), element.attrib.get("fill-opacity"))
        outline = _parse_svg_color(element.attrib.get("stroke"), None)
        width_value = max(1, int(round(float(element.attrib.get("stroke-width", "1"))))) if outline else 0
        draw.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=width_value)
        return

    if tag == "circle":
        cx = current_x + float(element.attrib.get("cx", "0"))
        cy = current_y + float(element.attrib.get("cy", "0"))
        radius = float(element.attrib.get("r", "0"))
        fill = _parse_svg_color(element.attrib.get("fill"), element.attrib.get("fill-opacity"))
        outline = _parse_svg_color(element.attrib.get("stroke"), None)
        width_value = max(1, int(round(float(element.attrib.get("stroke-width", "1"))))) if outline else 0
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill, outline=outline, width=width_value)
        return

    if tag == "line":
        stroke = _parse_svg_color(element.attrib.get("stroke"), None)
        if stroke is None:
            return
        width_value = max(1, int(round(float(element.attrib.get("stroke-width", "1")))))
        draw.line(
            (
                current_x + float(element.attrib.get("x1", "0")),
                current_y + float(element.attrib.get("y1", "0")),
                current_x + float(element.attrib.get("x2", "0")),
                current_y + float(element.attrib.get("y2", "0")),
            ),
            fill=stroke,
            width=width_value,
        )
        return

    if tag == "polyline":
        stroke = _parse_svg_color(element.attrib.get("stroke"), None)
        if stroke is None:
            return
        width_value = max(1, int(round(float(element.attrib.get("stroke-width", "1")))))
        points = []
        for pair in element.attrib.get("points", "").split():
            if "," not in pair:
                continue
            x_text, y_text = pair.split(",", 1)
            points.append((current_x + float(x_text), current_y + float(y_text)))
        if len(points) >= 2:
            draw.line(points, fill=stroke, width=width_value)
        return

    if tag == "text":
        fill = _parse_svg_color(element.attrib.get("fill"), None) or (45, 34, 23, 255)
        x_value = current_x + float(element.attrib.get("x", "0"))
        y_value = current_y + float(element.attrib.get("y", "0"))
        text_value = "".join(element.itertext())
        if element.attrib.get("text-anchor") == "end":
            try:
                bbox = draw.textbbox((0, 0), text_value, font=font)
                text_width = bbox[2] - bbox[0]
            except ValueError:
                text_width = draw.textlength(text_value, font=font)
            x_value -= text_width
        draw.text((x_value, y_value - 10), text_value, fill=fill, font=font)
        return

    for child in element:
        _draw_svg_node(draw, child, font, current_x, current_y)


def _parse_translate(raw: str | None) -> tuple[float, float]:
    if not raw or not raw.startswith("translate(") or not raw.endswith(")"):
        return 0.0, 0.0
    values = [piece.strip() for piece in raw[len("translate("):-1].replace(",", " ").split() if piece.strip()]
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(values[0]), float(values[1])


def _parse_svg_color(raw: str | None, opacity: str | None) -> tuple[int, int, int, int] | None:
    if raw in {None, "none"}:
        return None
    value = raw.strip()
    alpha = 255 if opacity is None else max(0, min(255, int(float(opacity) * 255)))
    if value.startswith("#") and len(value) == 7:
        return (
            int(value[1:3], 16),
            int(value[3:5], 16),
            int(value[5:7], 16),
            alpha,
        )
    named = {
        "white": (255, 255, 255, alpha),
        "black": (0, 0, 0, alpha),
    }
    return named.get(value.lower(), (45, 34, 23, alpha))
