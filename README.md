# pso-birds

Proyecto de `Particle Swarm Optimization (PSO)` con arquitectura modular, ejecucion reproducible, comparacion de estrategias de evaluacion paralela, persistencia de resultados y generacion de visualizaciones.

## Descripcion general

El repositorio esta organizado para separar responsabilidades:

- `core/`: logica principal del PSO, configuracion, tipos, resultados y benchmarking base.
- `objectives/`: funciones objetivo disponibles (`sphere`, `sleepy_sphere`, `ackley`, `rastrigin`, `rosenbrock`).
- `parallel/`: estrategias de evaluacion de fitness (`sequential`, `thread`, `process`, `asyncio`, `numpy`).
- `experiments/`: orquestacion de benchmarks y grid search.
- `io/`: persistencia de resultados y tablas agregadas.
- `viz/`: renderizado SVG y exportacion de animaciones.
- `tests/`: pruebas automáticas del motor, runners y experimentos.
- `results/`: artefactos generados por las ejecuciones.

## Estructura actual

Modulos principales del estado actual del repositorio:

- `core/pso.py`: implementa `BirdSwarmOptimizer`.
- `core/benchmark.py`: benchmark base, comparacion entre modos y grid search base.
- `core/persistence_bridge.py`: puente de compatibilidad hacia la persistencia real ubicada en `io/persistence.py`.
- `io/persistence.py`: escritura de `json`, `yaml`, `csv` y tablas agregadas.
- `experiments/benchmark_suite.py`: CLI y suite reproducible de benchmarks.
- `experiments/grid_search.py`: CLI de grid search reproducible.
- `viz/visualization.py`: visualizacion 2D/3D, SVG y exportacion de animaciones.

## Instalacion

El proyecto incluye `pyproject.toml` y puede instalarse en modo editable:

```bash
python3 -m pip install -e .
```

Si el entorno usa una version antigua de `setuptools` o no tiene acceso a red, puede ser util:

```bash
python3 -m pip install -e . --no-build-isolation
```

Requisitos actuales:

- Python 3.10 o superior

## Uso basico

Ejecucion simple del optimizador:

```bash
python3 run_pso.py --objective sphere --mode sequential --birds 30 --dimensions 2 --flights 80
```

Benchmark puntual:

```bash
python3 run_benchmarks.py run --objective sphere --mode numpy --birds 20 --dimensions 10 --flights 40 --repetitions 2 --output-dir results
```

Comparacion entre baseline secuencial y un modo candidato:

```bash
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
python3 make_viz.py --objective ackley --dimensions 3 --birds 20 --flights 40 --output-dir results --export mp4
```

## Scripts principales

- `run_pso.py`: ejecuta una sola corrida PSO y, si corresponde, genera artefactos de visualizacion.
- `run_benchmarks.py`: sirve tanto para una suite completa como para los subcomandos `run` y `compare`.
- `run_grid_search.py`: ejecuta una busqueda en rejilla sobre `w`, `c1`, `c2` y semillas.
- `make_viz.py`: ejecuta una corrida PSO y genera artefactos visuales adicionales.

## Estrategias paralelas

Las estrategias disponibles se implementan en `parallel/`:

- `sequential`: baseline sin paralelismo.
- `thread`: evaluacion con `ThreadPoolExecutor`.
- `process`: evaluacion con `ProcessPoolExecutor`.
- `asyncio`: coordinacion asincrona de evaluaciones.
- `numpy`: evaluacion vectorizada con NumPy.

La comparacion experimental se centra en la evaluacion del fitness, manteniendo fija la logica del PSO.

## Persistencia

La persistencia real se centraliza en `io/persistence.py` mediante `ArtifactWriter`.

Por compatibilidad con el nombre reservado `io` de la biblioteca estandar de Python, el resto del proyecto usa `core/persistence_bridge.py` como punto de acceso estable. No es una segunda implementacion: solo redirige a la persistencia canonica.

Segun el script ejecutado y la configuracion usada, pueden generarse artefactos como:

- `result.json`, `result.yaml`
- `summary.json`, `summary.yaml`
- `comparison.json`, `comparison.yaml`
- `grid_search.json`, `grid_search.yaml`, `grid_search.csv`
- `history.csv`
- `benchmark_suite/summary.json`, `benchmark_suite/summary.yaml`, `benchmark_suite/summary.csv`

Los artefactos se escriben bajo `results/` cuando se proporciona o se usa un directorio de salida.

## Visualizacion

El paquete `viz/` concentra el renderizado de artefactos visuales:

- `convergence.svg`: evolucion del mejor fitness por iteracion.
- `swarm_2d.svg`: vista estatica del enjambre en problemas bidimensionales.
- animaciones `gif` o `mp4` generadas desde `make_viz.py` segun el valor de `--export`.

En ejecuciones 2D y 3D se pueden generar vistas adaptadas a la dimensionalidad del problema. La limpieza de residuos temporales de animacion tambien se gestiona desde `viz/visualization.py`.

## Validacion rapida

Comandos utiles para comprobar que el proyecto sigue operativo:

```bash
python3 run_pso.py --help
python3 run_benchmarks.py --help
python3 run_benchmarks.py run --help
python3 run_benchmarks.py compare --help
python3 run_grid_search.py --help
python3 make_viz.py --help
python3 -m unittest discover -s tests
```

## Notas

- Este README describe el estado actual del repositorio, sin adelantar cambios experimentales que todavia no formen parte del codigo.
- `results/` contiene salidas generadas y no forma parte de la logica del paquete.
