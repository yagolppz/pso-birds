# pso-birds

Proyecto de `Particle Swarm Optimization (PSO)` con arquitectura modular, estrategias de evaluacion paralela, persistencia de resultados, grid search y visualizacion animada del enjambre.

## Estructura

- `core/`
  Motor PSO, configuracion, tipos, resultados y wrappers de compatibilidad.
- `objectives/`
  Funciones objetivo disponibles: `sphere`, `ackley`, `rastrigin`, `rosenbrock`, `sleepy_sphere`.
- `parallel/`
  Estrategias seleccionables: `sequential`, `thread`, `process`, `asyncio`, `numpy`.
- `experiments/`
  Suite de benchmarks reproducibles y grid search.
- `io/`
  Persistencia centralizada de `result.json/yaml`, `summary.json/yaml`, `history.csv`, `flights.jsonl` y tablas agregadas.
- `viz/`
  Visualizaciones estaticas y animadas, incluyendo GIF automatico para 2D y 3D.
- `results/`
  Artefactos generados por ejecuciones y experimentos.
- `tests/`
  Tests del motor, experimentos y runners.

## Modulos clave

- `core/pso.py`
  Motor `BirdSwarmOptimizer`.
- `core/benchmark.py`
  Benchmark base y comparacion entre modos.
- `experiments/benchmarks.py`
  Suite completa para objetivos y dimensiones de la practica.
- `experiments/grid_search.py`
  Grid search reproducible sobre `w`, `c1`, `c2` y semillas multiples.
- `io/persistence.py`
  Escritura de JSON, YAML, CSV y reportes tabulares.
- `viz/visualization.py`
  `convergence.svg`, `swarm_2d.svg` y `animation.gif` para visualizacion 2D y 3D.

## Estrategias paralelas

- `sequential`
  Baseline sin paralelismo.
- `thread`
  Evaluacion con `ThreadPoolExecutor`.
- `process`
  Evaluacion con `ProcessPoolExecutor`.
- `asyncio`
  Coordinacion asincrona con tareas concurrentes.
- `numpy`
  Evaluacion vectorizada usando NumPy.

## Scripts principales

Ejecucion simple del optimizador:

```bash
python3 run_pso.py --objective sphere --mode sequential --birds 30 --dimensions 2 --flights 80
```

Benchmark CLI principal:

```bash
python3 run_benchmarks.py run --objective sphere --mode numpy --birds 20 --dimensions 10 --flights 40 --repetitions 2 --output-dir results
python3 run_benchmarks.py compare --objective ackley --candidate-mode process --birds 20 --dimensions 10 --flights 40 --workers 4 --repetitions 2 --output-dir results
```

Suite completa de benchmarks:

```bash
python3 run_benchmarks.py
python3 run_benchmarks.py --objectives sphere,ackley --dimensions 2,10 --modes sequential,numpy,process --birds 16 --flights 25 --repetitions 1 --output-dir results
```

Grid search:

```bash
python3 run_grid_search.py
python3 run_grid_search.py --objective sphere --mode sequential --dimensions 2 --grid-w 0.4,0.7,0.9 --grid-c1 1.3,1.7 --grid-c2 1.3,1.7 --grid-seeds 7,8,9 --output-dir results
```

Visualizacion y animaciones:

```bash
python3 make_viz.py --objective sphere --dimensions 2 --birds 20 --flights 40 --output-dir results --export gif
python3 make_viz.py --objective ackley --dimensions 3 --birds 20 --flights 40 --output-dir results --export gif
```

## Resultados esperados

En `results/<objective>/<mode>/run_000/` pueden aparecer:

- `result.json`, `result.yaml`
- `history.csv`
- `flights.jsonl`
- `convergence.svg`
- `swarm_2d.svg` si `d=2`
- `animation.gif` si `d=2` o `d=3`

En `results/<objective>/<mode>/`:

- `summary.json`, `summary.yaml`

En `results/<objective>/compare_sequential_vs_<mode>/`:

- `comparison.json`, `comparison.yaml`

En `results/<objective>/grid_search_<mode>/`:

- `grid_search.json`, `grid_search.yaml`, `grid_search.csv`

En `results/benchmark_suite/`:

- `summary.json`, `summary.yaml`, `summary.csv`

## Visualizaciones

- `convergence.svg`
  Curva `best fitness vs iteracion`.
- `swarm_2d.svg`
  Mosaico estatico de snapshots del enjambre 2D.
- `animation.gif`
  Animacion final del enjambre para `d=2` y `d=3`, con particulas, mejor global y la vista correspondiente de la funcion objetivo.

## Validacion

Comandos que deben funcionar:

```bash
python3 run_pso.py
python3 run_benchmarks.py
python3 run_grid_search.py
python3 make_viz.py
python3 -m unittest discover -s tests -v
```
