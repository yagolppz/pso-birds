# pso-birds

Proyecto de `Particle Swarm Optimization (PSO)` con analogia de pajaritos buscando migas en un parque continuo.

## Idea

- Particula = pajarito
- Fitness = migas
- `pBest` = mejor recuerdo individual
- `gBest` = mejor sitio global encontrado
- Iteracion = vuelo

## Arquitectura actual

- `core/`
  Motor PSO, configuracion, resultados, logging, persistencia, benchmark y visualizacion.
- `objectives/`
  Funciones objetivo desacopladas del motor.
- `parallel/`
  Estrategias de evaluacion intercambiables: `sequential`, `thread`, `process`, `asyncio`, `numpy`.
- `tests/`
  Tests de motor, benchmark y runners finales.
- `run_pso.py`
  Ejecucion simple del optimizador.
- `run_benchmark.py`
  Benchmark, comparativas y grid search.

## Funcionalidades

- Motor PSO limpio con `BirdSwarmOptimizer`
- Evaluacion desacoplada por estrategia
- Benchmark y comparacion entre modos
- Grid search de hiperparametros
- Persistencia de resultados en `json`, `yaml`, `csv`
- Visualizacion SVG:
  - `convergence.svg`
  - `swarm_2d.svg` para corridas en 2D

## Objetivos disponibles

- `sphere`
- `sleepy_sphere`
- `rastrigin`
- `ackley`
- `rosenbrock`

## Uso rapido

Ejecucion simple:

```bash
python3 run_pso.py --objective sphere --mode sequential --birds 30 --dimensions 2 --flights 80
```

Benchmark de una configuracion:

```bash
python3 run_benchmark.py run --objective sphere --mode numpy --birds 30 --dimensions 2 --flights 50 --repetitions 3 --output-dir artifacts
```

Comparativa entre baseline secuencial y otra estrategia:

```bash
python3 run_benchmark.py compare --objective sleepy_sphere --candidate-mode process --birds 40 --dimensions 8 --flights 60 --workers 4 --repetitions 3 --output-dir artifacts
```

Grid search:

```bash
python3 run_benchmark.py grid-search --objective sphere --mode sequential --dimensions 2 --flights 40 --grid-birds 20,30 --grid-w 0.5,0.7 --grid-c1 1.4,1.8 --grid-c2 1.4,1.8 --grid-seeds 7,8 --output-dir artifacts
```

## Artefactos

Cuando se usa `--output-dir`, el proyecto puede generar:

- `result.json`
- `result.yaml`
- `history.csv`
- `summary.json`
- `comparison.json`
- `grid_search.csv`
- `flights.jsonl`
- `convergence.svg`
- `swarm_2d.svg` en ejecuciones 2D

## Tests

La suite cubre:

- reproducibilidad por `seed`
- limites del `search space`
- monotonicidad de `gBest`
- convergencia basica en `Sphere`
- ejecucion real de `run_pso.py` y `run_benchmark.py`

Ejecucion:

```bash
python3 -m unittest discover -s tests -v
```
