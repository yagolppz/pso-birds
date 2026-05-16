# pso-birds

## 1. Descripcion

Este proyecto implementa `Particle Swarm Optimization (PSO)` en Python con una arquitectura modular y varias estrategias de ejecucion para estudiar el impacto del paralelismo y la concurrencia sobre el tiempo de evaluacion.

El objetivo del trabajo no es modificar el comportamiento matematico del algoritmo, sino comparar distintas formas de ejecutar la evaluacion del fitness manteniendo fijo el mismo PSO base. Para ello, el repositorio incluye una suite experimental reproducible con metricas agregadas, curvas promedio de convergencia, boxplots de fitness final, speedup y overhead.

## 2. Estructura del proyecto

- `core/`: implementacion principal del algoritmo PSO, configuracion, tipos, resultados y utilidades base de benchmark.
- `objectives/`: funciones objetivo disponibles para los experimentos (`sphere`, `ackley`, `rastrigin`, `rosenbrock`, `wifi_router`).
- `parallel/`: estrategias de evaluacion del fitness.
- `experiments/`: ejecucion de benchmarks y grid search.
- `io/`: persistencia de resultados y tablas agregadas.
- `viz/`: generacion de visualizaciones y exportacion de animaciones.
- `results/`: artefactos generados por las ejecuciones.
- `tests/`: pruebas automatizadas del proyecto.

Dentro de `results/benchmark_suite/` la organizacion general es:

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

En la Entrega 2 tambien se incluyen carpetas finales especificas para los resultados cerrados:

- `results/final_benchmark_classic/`
- `results/final_benchmark_wifi_full/`
- `results/final_grid_search/`
- `results/final_rastrigin_viz/`
- `results/final_wifi_viz/`

## 3. Instalacion

El proyecto puede instalarse en modo editable con:

```bash
python3 -m pip install -e .
```

Dependencias practicas del proyecto:

- `numpy`: obligatorio para las funciones objetivo vectorizadas y el modo `numpy`.
- `Pillow`: necesario para generar animaciones `gif`.
- `imageio`: opcional, solo necesario para exportar animaciones `mp4`.

Si el entorno no las incluye ya, puede ser necesario instalarlas manualmente.

## 4. Uso basico

Ejecucion simple del optimizador:

```bash
python3 run_pso.py --objective sphere --mode sequential --dimensions 2 --birds 30 --flights 80
```

Ejecucion simple con el caso de uso WiFi:

```bash
python3 run_pso.py --objective wifi_router --mode sequential --dimensions 3 --birds 12 --flights 30
```

Benchmark individual sobre una configuracion concreta:

```bash
python3 run_benchmarks.py run --objective sphere --mode sequential --dimensions 2 --birds 20 --flights 30 --repetitions 1
```

Comparacion entre `sequential` y otra estrategia:

```bash
python3 run_benchmarks.py compare --objective sleepy_sphere --candidate-mode process --dimensions 10 --birds 20 --flights 30 --repetitions 3 --workers 4
```

Suite reproducible final sobre funciones clasicas:

```bash
python3 run_benchmarks.py --objectives sphere,ackley,rastrigin,rosenbrock --dimensions 2,10,30 --modes sequential,thread,process,asyncio,numpy --birds 12 --flights 20 --repetitions 3 --workers 4 --batch-size 4
```

Suite reproducible final sobre el caso de uso WiFi:

```bash
python3 run_benchmarks.py --objectives wifi_router --dimensions 3 --modes sequential,thread,process,asyncio,numpy --birds 12 --flights 30 --repetitions 3 --workers 4 --batch-size 4
```

Grid search:

```bash
python3 run_grid_search.py --objective sphere --mode sequential --dimensions 2 --grid-w 0.4,0.7,0.9 --grid-c1 1.3,1.7,2.1 --grid-c2 1.3,1.7,2.1 --grid-seeds 7,8,9,10,11
```

Generacion de visualizaciones y animaciones:

```bash
python3 make_viz.py --objective sphere --mode sequential --dimensions 2 --export gif
```

Generacion de visualizacion para el caso WiFi:

```bash
python3 make_viz.py --objective wifi_router --mode sequential --dimensions 3 --export gif
```

Los scripts aceptan argumentos adicionales para fijar objetivo, dimension, numero de particulas, numero de iteraciones, modo de ejecucion, directorio de salida y otras opciones del experimento.

Argumentos importantes expuestos por CLI:

- `--workers`: numero de workers para `thread`, `process` y `asyncio`.
- `--batch-size`: tamaño de lote usado por `process` para agrupar evaluaciones y reducir el coste de crear tareas individuales.
- `--seed`: semilla reproducible.
- `--w`, `--c1`, `--c2`: hiperparametros del PSO.
- `--lower-bound`, `--upper-bound`: limites explicitos del espacio de busqueda.
- `--velocity-limit-factor`: factor de limite de velocidad por dimension.
- `--stop-when-crumbs-below`: parada temprana por umbral de fitness.
- `--stop-after-stagnant-flights`: parada opcional por estancamiento cuando no mejora el mejor fitness durante varias iteraciones.
- `--output-dir`: directorio de salida.
- `--log-file`: fichero opcional de logging.

La configuracion de ejecucion se hace por CLI. El proyecto genera salidas en YAML, pero no usa YAML como formato de entrada para configurar experimentos.

## 5. Objetivos implementados

El proyecto incluye funciones benchmark clasicas y un caso de uso aplicado:

- `sphere`: funcion convexa sencilla, util para comprobar convergencia basica.
- `ackley`: funcion multimodal con varios minimos locales.
- `rastrigin`: funcion multimodal exigente para analizar exploracion y explotacion.
- `rosenbrock`: funcion no convexa con valle estrecho, util para evaluar estabilidad.
- `wifi_router`: caso de uso real de optimizacion de ubicacion de un router WiFi en 3D.

El objetivo `wifi_router` modela la colocacion de un router en un espacio tridimensional teniendo en cuenta dispositivos fijos, obstaculos, restricciones de altura y penalizaciones. Se usa como caso aplicado para demostrar que el PSO no solo funciona sobre funciones matematicas de benchmark, sino tambien sobre un problema de optimizacion interpretable.

## 6. Estrategias implementadas

- `sequential`: version base sin paralelismo. Se usa como referencia para comparar tiempos.
- `thread`: paralelismo con hilos. Reutiliza memoria compartida, pero puede verse limitado por el GIL.
- `process`: paralelismo con procesos. Evita el GIL, pero introduce coste de serializacion y comunicacion entre procesos.
- `asyncio`: coordinacion asincrona de tareas concurrentes.
- `numpy`: evaluacion vectorizada mediante operaciones sobre arrays.

Nota: `numpy` no es paralelismo clasico, sino evaluacion vectorizada. En el repositorio se trata como una estrategia adicional de ejecucion para comparar rendimiento.

## 7. Protocolo experimental

La suite experimental se ha preparado para comparar las distintas estrategias de ejecucion manteniendo fijo el mismo nucleo PSO. De esta forma, la comparacion se centra en el coste temporal de cada estrategia y no en cambios de comportamiento del algoritmo.

En la Entrega 2 se han generado dos campañas finales de benchmark:

### Benchmark clasico

Ubicacion:

- `results/final_benchmark_classic/`

Configuracion principal:

- objetivos: `sphere`, `ackley`, `rastrigin`, `rosenbrock`
- dimensiones: `2`, `10` y `30`
- modos: `sequential`, `thread`, `process`, `asyncio`, `numpy`
- particulas: `12`
- iteraciones: `20`
- repeticiones: `3`
- workers: `4`
- batch size: `4`

### Benchmark del caso de uso WiFi

Ubicacion:

- `results/final_benchmark_wifi_full/`

Configuracion principal:

- objetivo: `wifi_router`
- dimension: `3`
- modos: `sequential`, `thread`, `process`, `asyncio`, `numpy`
- particulas: `12`
- iteraciones: `30`
- repeticiones: `3`
- workers: `4`
- batch size: `4`

Las metricas principales analizadas son:

- tiempo total de ejecucion
- tiempo de evaluacion del fitness
- tiempo de actualizacion del enjambre
- overhead de coordinacion
- speedup respecto a `sequential`
- fitness final
- curvas promedio de convergencia
- boxplots del fitness final por estrategia

La suite necesita incluir siempre el modo `sequential`, ya que se usa como baseline para calcular `speedup_vs_sequential`.

Adicionalmente, el proyecto mantiene soporte para grid search reducido sobre `w`, `c1` y `c2`, con control de semillas, para analizar la sensibilidad del PSO ante distintos hiperparametros.

## 8. Persistencia y artefactos

El proyecto guarda resultados en varios formatos para facilitar tanto la revision manual como el analisis posterior:

- `result.json` y `result.yaml`: resultado completo de una ejecucion individual.
- `history.csv`: historial por iteracion.
- `flights.jsonl`: eventos estructurados del vuelo y snapshots del experimento.
- `summary.json` y `summary.yaml`: resumen agregado por modo y objetivo.
- `comparison.json` y `comparison.yaml`: comparacion entre `sequential` y otro modo.
- `grid_search.csv`, `grid_search.json` y `grid_search.yaml`: resultados del grid search.
- tablas agregadas en `csv`, `json` y `yaml` dentro de las carpetas de benchmark.

En la Entrega 2, los resultados finales se han dejado separados en carpetas especificas:

- `results/final_benchmark_classic/`: benchmark principal sobre funciones clasicas.
- `results/final_benchmark_wifi_full/`: benchmark completo del caso de uso `wifi_router`.
- `results/final_rastrigin_viz/`: visualizacion final sobre `rastrigin`.
- `results/final_wifi_viz/`: visualizacion final del caso de uso WiFi.
- `results/final_grid_search/`: resultados finales del grid search reducido sobre hiperparametros del PSO.

Las carpetas de benchmark incluyen, entre otros artefactos:

- tablas resumen por objetivo, dimension y estrategia.
- tablas de speedup respecto a `sequential`.
- tablas de overhead medio.
- metricas por repeticion/seed.
- curvas promedio de convergencia.
- boxplots de fitness final.
- fichero `protocol.json` con la configuracion experimental usada.

Las carpetas de visualizacion incluyen artefactos como:

- `convergence.svg`
- `animation_2d.gif`
- `animation_3d.gif`
- `history.csv`
- `result.json`
- `result.yaml`
- `flights.jsonl`

Ademas, los resultados incorporan metadata de reproducibilidad, incluyendo informacion de ejecucion como semilla, modo, numero de workers, batch size, plataforma, version de Python, CPU disponible, rama y commit cuando es posible obtenerlo.

## 9. Resultados y analisis

La interpretacion del experimento se apoya en una idea central: el algoritmo base no cambia entre estrategias. Por eso, el fitness final esperado debe ser comparable entre `sequential`, `thread`, `process`, `asyncio` y `numpy` cuando se usan la misma funcion objetivo, la misma dimension, las mismas seeds y los mismos hiperparametros.

En las curvas promedio de convergencia es normal que varias lineas aparezcan muy solapadas. Eso no indica un error: refleja que todas las estrategias siguen la misma trayectoria de optimizacion, ya que la paralelizacion afecta al tiempo de ejecucion, no a la logica del PSO.

Por tanto, el analisis principal del trabajo se centra en los tiempos:

- `speedup`: relacion entre el tiempo secuencial y el tiempo de una estrategia concreta.
- `overhead`: parte del tiempo total que no corresponde directamente ni a la evaluacion del fitness ni a la actualizacion de particulas.

Una estrategia puede no mejorar a `sequential` si el coste de coordinacion, serializacion o gestion de tareas supera el trabajo util que se paraleliza.

## 10. Validacion

Para ejecutar la bateria de tests:

```bash
python3 -m unittest discover -s tests
```

Tambien se puede ejecutar la validacion con `pytest`:

```bash
python3 -m pytest
```

Es posible comprobar los scripts principales con:

```bash
python3 run_pso.py --help
python3 run_benchmarks.py --help
python3 run_grid_search.py --help
python3 make_viz.py --help
```

## 11. Cumplimiento de requisitos de la Entrega 2

La Entrega 2 se ha orientado a cerrar el proyecto como una solucion PSO completa, reproducible y preparada para comparar estrategias de concurrencia y paralelizacion. El objetivo principal ha sido mantener un nucleo PSO comun y sustituir unicamente la estrategia de evaluacion del fitness, de forma que la comparacion entre modos sea justa.

Resumen de cumplimiento:

| Requisito | Estado | Evidencia en el proyecto |
|---|---|---|
| PSO base secuencial | Cumplido | Motor principal en `core/` y modo `sequential` como baseline |
| Arquitectura modular | Cumplido | Separacion en `core/`, `objectives/`, `parallel/`, `experiments/`, `io/`, `viz/` y `tests/` |
| Funciones benchmark | Cumplido | `sphere`, `ackley`, `rastrigin` y `rosenbrock` |
| Caso de uso aplicado | Cumplido | `wifi_router`, optimizacion de ubicacion de router WiFi en 3D |
| Estrategias V0-V4 | Cumplido | `sequential`, `thread`, `process`, `asyncio` y `numpy` |
| Batching en multiprocessing | Cumplido | Parametro `--batch-size` y agrupacion de evaluaciones en `process` |
| Reproducibilidad | Cumplido | Registro de seed, modo, workers, batch size, entorno, plataforma, rama y commit |
| Criterios de parada | Cumplido | Iteraciones, umbral de fitness y parada opcional por estancamiento |
| Persistencia | Cumplido | Salidas en `json`, `yaml`, `csv` y `jsonl` |
| Grid search configurable | Cumplido | Script `run_grid_search.py` con exploracion de `w`, `c1`, `c2` y control de seeds |
| Analisis experimental | Cumplido | Tablas de resumen, speedup, overhead, curvas promedio y boxplots |
| Visualizacion 2D/3D | Cumplido | Animaciones y curvas en `results/final_rastrigin_viz/` y `results/final_wifi_viz/` |
| Tests automatizados | Cumplido | Validacion final con `36 passed` |

## 12. Decisiones de diseño relevantes

El diseño del proyecto se ha basado en una idea principal: evitar crear cinco versiones diferentes del algoritmo PSO. En su lugar, se mantiene un nucleo comun y se intercambia la estrategia de evaluacion. Esta decision facilita la comparacion experimental, reduce duplicidad de codigo y hace que los resultados sean mas interpretables.

Las decisiones mas importantes son:

- Se usa `sequential` como linea base para calcular el speedup del resto de estrategias.
- Se implementa `thread` para estudiar concurrencia con hilos y observar el efecto del GIL en cargas CPU-bound.
- Se implementa `process` para evaluar paralelismo real mediante procesos, teniendo en cuenta el coste de serializacion e IPC.
- Se añade `batch_size` en `process` para reducir overhead agrupando varias particulas por tarea.
- Se implementa `asyncio` como estrategia concurrente cooperativa, especialmente util para razonar sobre evaluaciones asimetricas o con latencia.
- Se implementa `numpy` como paralelismo implicito/vectorizacion, aprovechando operaciones sobre arrays.
- Se registra metadata de reproducibilidad para que cada resultado pueda relacionarse con su configuracion experimental.
- Se añade `stop_after_stagnant_flights` como criterio opcional de parada por estancamiento.
- Se mantiene `stop_when_crumbs_below` como parada temprana por umbral de calidad.
- Se incorpora `wifi_router` como caso de uso real para demostrar la aplicabilidad del PSO fuera de funciones matematicas clasicas.

## 13. Interpretacion esperada de los resultados

En este proyecto, que una estrategia paralela no supere siempre a `sequential` no se interpreta como un fallo. La comparacion mide precisamente si el trabajo util de evaluar el fitness compensa el coste adicional de coordinar hilos, procesos, tareas asincronas o estructuras vectorizadas.

La interpretacion general debe hacerse considerando:

- En problemas pequenos o con pocas particulas, el overhead puede ser mayor que el beneficio de paralelizar.
- En `thread`, el GIL puede limitar la mejora cuando el trabajo es principalmente CPU-bound en Python.
- En `process`, se evita el GIL, pero aparece coste de serializacion, comunicacion entre procesos y reparto de tareas.
- El batching reduce parte de ese coste al enviar bloques de particulas en lugar de tareas individuales.
- `asyncio` tiene sentido sobre todo cuando la evaluacion puede modelar esperas, latencias o tareas cooperativas.
- `numpy` puede ser competitivo porque reduce bucles Python y desplaza calculo a operaciones vectorizadas.
- La dimension del problema y el coste de la funcion objetivo son factores clave para que el paralelismo pueda compensar.

Por este motivo, el analisis final no se centra solo en encontrar la estrategia mas rapida, sino en explicar bajo que condiciones cada estrategia resulta conveniente.

## 14. Limitaciones y trabajo futuro

Aunque el proyecto cubre los requisitos principales de la Entrega 2, se han dejado algunas extensiones como trabajo futuro:

- Incorporar topologias adicionales como `local-best`, `ring` o `von Neumann`.
- Comparar algunos resultados con un optimizador externo como `scipy.optimize`.
- Construir un dashboard con Streamlit o Gradio para explorar resultados de forma interactiva.
- Ampliar el numero de repeticiones y tamanos de enjambre para estudiar escalabilidad con mayor profundidad.
- Ejecutar benchmarks en maquinas con mas nucleos para analizar mejor la saturacion de CPU.
- Ampliar el caso WiFi con mapas reales, mas obstaculos o modelos de propagacion mas detallados.

Estas extensiones no son necesarias para demostrar el objetivo central de la practica, pero servirian para ampliar el proyecto hacia una herramienta experimental mas completa.

## 15. Estado final de validacion

La validacion final de la rama `feature/entrega2-final` se realizo ejecutando:

```bash
python3 -m pytest
```

Resultado obtenido:

```text
36 passed, 11 warnings
```

Los warnings observados estan relacionados con librerias de visualizacion/animacion y no impiden la ejecucion correcta del proyecto.

La rama `feature/entrega2-final` contiene los cambios tecnicos y experimentales de la Entrega 2. No se ha creado Pull Request todavia porque primero se esta cerrando la documentacion final y el paquete de entrega.
