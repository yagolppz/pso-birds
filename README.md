# pso-birds

## 1. Descripcion

Este proyecto implementa `Particle Swarm Optimization (PSO)` en Python con una arquitectura modular y varias estrategias de ejecucion para estudiar el impacto del paralelismo y la concurrencia sobre el tiempo de evaluacion.

El objetivo del trabajo no es modificar el comportamiento matematico del algoritmo, sino comparar distintas formas de ejecutar la evaluacion del fitness manteniendo fijo el mismo PSO base. Para ello, el repositorio incluye una suite experimental reproducible con metricas agregadas, curvas promedio de convergencia, boxplots de fitness final, speedup y overhead.

## 2. Estructura del proyecto

- `core/`: implementacion principal del algoritmo PSO, configuracion, tipos, resultados y utilidades base de benchmark.
- `objectives/`: funciones objetivo disponibles para los experimentos (`sphere`, `sleepy_sphere`, `ackley`, `rastrigin`, `rosenbrock`).
- `parallel/`: estrategias de evaluacion del fitness.
- `experiments/`: ejecucion de benchmarks y grid search.
- `io/`: persistencia de resultados y tablas agregadas.
- `viz/`: generacion de visualizaciones y exportacion de animaciones.
- `results/`: artefactos generados por las ejecuciones.
- `tests/`: pruebas automatizadas del proyecto.

Dentro de `results/benchmark_suite/` la organizacion actual es:

- `boxplots/`: comparacion del fitness final entre estrategias.
- `curves/`: curvas promedio de convergencia por objetivo y dimension.
- `tables/`: metricas agregadas en `csv`, `json` y `yaml`.
- `campaign_runs/`: ejecuciones crudas de cada campaña experimental.

Y dentro de `results/benchmark_suite/tables/`:

- `summary/`: resumen agregado por objetivo, dimension y estrategia.
- `speedup/`: tablas de speedup respecto a `sequential`.
- `overhead/`: tablas de overhead medio y su proporcion sobre el tiempo total.
- `per_seed_metrics/`: metricas por seed.
- `average_curves/`: datos agregados por iteracion para construir curvas promedio.
- `protocol/`: configuracion general del protocolo experimental.

## 3. Instalacion

El proyecto puede instalarse en modo editable con:

```bash
python3 -m pip install -e .
```

## 4. Uso basico

Ejecucion simple del optimizador:

```bash
python3 run_pso.py
```

Suite de benchmarks:

```bash
python3 run_benchmarks.py
```

Grid search:

```bash
python3 run_grid_search.py
```

Generacion de visualizaciones:

```bash
python3 make_viz.py
```

Los scripts aceptan argumentos adicionales para fijar objetivo, dimension, numero de particulas, numero de iteraciones, modo de ejecucion, directorio de salida y otras opciones del experimento.

## 5. Estrategias implementadas

- `sequential`: version base sin paralelismo. Se usa como referencia para comparar tiempos.
- `thread`: paralelismo con hilos. Reutiliza memoria compartida, pero puede verse limitado por el GIL.
- `process`: paralelismo con procesos. Evita el GIL, pero introduce coste de serializacion y comunicacion.
- `asyncio`: coordinacion asincrona de tareas concurrentes.
- `numpy`: evaluacion vectorizada mediante operaciones sobre arrays.

## 6. Protocolo experimental

La suite experimental se ha preparado para un protocolo reproducible centrado en comparar estrategias de ejecucion:

- dimensiones analizadas: `2`, `10` y `30`
- `5` seeds por configuracion
- grid search reducido sobre `w`, `c1` y `c2`
- comparacion entre todas las estrategias implementadas

Las metricas principales analizadas son:

- curvas promedio de convergencia por iteracion
- boxplots del fitness final por estrategia
- speedup respecto a la version secuencial
- overhead medio de cada estrategia

La salida agregada se guarda en `results/benchmark_suite/`, mientras que las ejecuciones crudas de cada campaña se guardan en `results/benchmark_suite/campaign_runs/`.

## 7. Resultados y analisis

La interpretacion del experimento se apoya en una idea central: el algoritmo base no cambia entre estrategias. Por eso, el fitness final esperado debe ser comparable entre `sequential`, `thread`, `process`, `asyncio` y `numpy` cuando se usan la misma funcion objetivo, la misma dimension, las mismas seeds y los mismos hiperparametros.

En las curvas promedio de convergencia es normal que varias lineas aparezcan muy solapadas. Eso no indica un error: refleja que todas las estrategias siguen la misma trayectoria de optimizacion, ya que la paralelizacion afecta al tiempo de ejecucion, no a la logica del PSO.

Por tanto, el analisis principal del trabajo se centra en los tiempos:

- `speedup`: relacion entre el tiempo secuencial y el tiempo de una estrategia concreta.
- `overhead`: parte del tiempo total que no corresponde directamente ni a la evaluacion del fitness ni a la actualizacion de particulas.

Una estrategia puede no mejorar a `sequential` si el coste de coordinacion, serializacion o gestion de tareas supera el trabajo util que se paraleliza.

## 8. Validacion

Para ejecutar la bateria de tests:

```bash
python3 -m unittest discover -s tests
```

Tambien es posible comprobar los scripts principales con:

```bash
python3 run_pso.py --help
python3 run_benchmarks.py --help
python3 run_grid_search.py --help
python3 make_viz.py --help
```


## Notas personales y limitaciones

El proyecto cubre la gran parte de los requisitos del enunciado. Estas son las cosas que faltan o que podrían mejorarse:

### Lo que no dio tiempo a finalizar

- **Criterio de parada por tolerancia o estancamiento**  
  El enunciado pide parada por iteraciones, tolerancia y estancamiento. Solo se implementan iteraciones fijas. El early stopping se queda pendiente.

- **Informacion de hardware en los resultados**  
  El enunciado dice "info de hardware si se puede". No se ha sabido hacerlo de forma limpia y se han priorizado otras cosas.


### Cosas que el enunciado menciona como opcionales y no se hizo

- Topologia local-best (solo global-best)
- Comparacion con scipy.optimize
- Dashboard con Streamlit/Gradio
- Apartados Bonus

### Lo que funciona correctamente

El PSO base, las 5 estrategias de paralelismo (sequential, thread, process, asyncio, numpy), la persistencia en multiples formatos, el grid search basico, las visualizaciones y los tests. El docente puede ejecutar los scripts y verificar los resultados en la carpeta `results/`.

### Conclusion personal

Se priorizo que el codigo funcionara y que las 5 versiones paralelas estuvieran bien implementadas. 
