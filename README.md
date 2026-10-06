# Taller MLflow

Este proyecto levanta con Docker Compose un entorno de MLflow para entrenar y servir un modelo que predice la especie de un pingüino a partir de sus medidas, la isla y el sexo. Los datos se guardan en una base de datos PostgreSQL (una tabla con los datos crudos y otra con los procesados), los experimentos se registran en MLflow usando otra base PostgreSQL distinta para su metadata, los modelos quedan guardados en MinIO, y una API en FastAPI hace la inferencia tomando el modelo desde el Model Registry de MLflow.

## Servicios y puertos

| Servicio | Contenedor | URL local | URL en la VM |
|---|---|---|---|
| MLflow | tm_mlflow | http://localhost:8001 | http://10.43.97.104:8001 |
| Consola de MinIO | tm_minio | http://localhost:8002 | http://10.43.97.104:8002 |
| API de MinIO (S3) | tm_minio | http://localhost:8003 | http://10.43.97.104:8003 |
| JupyterLab | tm_jupyter | http://localhost:8004 | http://10.43.97.104:8004 |
| API de inferencia | tm_api | http://localhost:8005/docs | http://10.43.97.104:8005/docs |
| PostgreSQL de datos | tm_postgres_data | no se expone | no se expone |
| PostgreSQL de metadata | tm_postgres_mlflow | no se expone | no se expone |

Las dos bases de datos no publican puertos hacia afuera porque solo las usan los otros contenedores dentro de la red de Docker.

## Cómo levantarlo

Clonar el repositorio y entrar a la carpeta:

```
git clone <url-del-repo>
cd taller-mlflow
```

Crear el archivo .env a partir de la plantilla:

```
cp .env.example .env
```

Llenar los valores del .env. Las variables que hay que definir son:

- JUPYTER_UID: el id del usuario de Linux, se obtiene con id -u
- JUPYTER_TOKEN: el token para entrar a JupyterLab
- POSTGRES_DATA_USER, POSTGRES_DATA_PASSWORD, POSTGRES_DATA_DB: credenciales de la base de datos de los pingüinos
- POSTGRES_MLFLOW_USER, POSTGRES_MLFLOW_PASSWORD, POSTGRES_MLFLOW_DB: credenciales de la base de metadata de MLflow
- MINIO_ROOT_USER, MINIO_ROOT_PASSWORD: credenciales de MinIO, que también se usan como llaves de acceso S3
- MINIO_BUCKET: nombre del bucket donde MLflow guarda los artefactos

Levantar todo:

```
docker compose up -d --build
```

La primera vez tarda varios minutos porque construye las imágenes de MLflow, JupyterLab y la API.

Revisar que los servicios estén arriba:

```
docker compose ps
```

```
NAME                 IMAGE                        COMMAND                  SERVICE           CREATED         STATUS                            PORTS
tm_api               taller-mlflow-api            "uvicorn main:app --…"   api               2 hours ago     Up 2 hours                        0.0.0.0:8005->8000/tcp, [::]:8005->8000/tcp
tm_jupyter           taller-mlflow-jupyter        "tini -g -- start-no…"   jupyter           5 seconds ago   Up 2 seconds (health: starting)   0.0.0.0:8004->8888/tcp, [::]:8004->8888/tcp
tm_minio             bitnamilegacy/minio:latest   "/opt/bitnami/script…"   minio             5 hours ago     Up 5 hours (healthy)              0.0.0.0:8003->9000/tcp, [::]:8003->9000/tcp, 0.0.0.0:8002->9001/tcp, [::]:8002->9001/tcp
tm_mlflow            taller-mlflow-mlflow         "mlflow server --hos…"   mlflow            2 hours ago     Up 2 hours                        0.0.0.0:8001->5000/tcp, [::]:8001->5000/tcp
tm_postgres_data     postgres:14                  "docker-entrypoint.s…"   postgres_data     5 hours ago     Up 5 hours (healthy)              5432/tcp
tm_postgres_mlflow   postgres:14                  "docker-entrypoint.s…"   postgres_mlflow   5 hours ago     Up 5 hours (healthy)              5432/tcp
```
## Orden de ejecución de los notebooks

Entrar a JupyterLab en el puerto 8004 con el token definido en el .env. Los notebooks están en la carpeta work y hay que correrlos en este orden:

1. 01_carga_datos.ipynb: lee el CSV de pingüinos, lo carga sin procesar a la tabla raw.penguins_raw y luego guarda la versión procesada en clean.penguins_clean.
2. 02_experimentos.ipynb: lee los datos desde clean.penguins_clean, entrena los modelos variando hiperparámetros, registra todo en MLflow y deja el modelo elegido en el Model Registry con el alias produccion.

El segundo notebook necesita que el primero ya haya corrido, porque lee de la base de datos y no del CSV.

## Evidencia de funcionamiento

### Datos en las dos tablas

Este comando muestra cuántas filas quedaron en la tabla de datos crudos y en la de procesados:

```
docker compose exec postgres_data psql -U penguins_user -d penguins_db -c "SELECT (SELECT COUNT(*) FROM raw.penguins_raw) AS crudos, (SELECT COUNT(*) FROM clean.penguins_clean) AS limpios;"
```

El usuario y la base del comando salen de POSTGRES_DATA_USER y POSTGRES_DATA_DB del .env. Si los cambias, ajusta el comando.

```
 crudos | limpios
--------+---------
    344 |     333
(1 row)
```

### Experimentos en MLflow
![Runs del experimento en MLflow](https://github.com/user-attachments/assets/14bb5120-4011-4347-b062-0906fe2bf840)

<img width="900" alt="Scatter plot de max_depth contra accuracy" src="https://github.com/user-attachments/assets/6523bd0f-cb65-49f7-a2d8-89b199be31d4" />

En la pestaña Models está el modelo registrado con sus dos versiones:
<img width="900" alt="Modelo penguins-classifier con sus dos versiones" src="https://github.com/user-attachments/assets/f7c5a03c-ae66-4a9a-8338-2f0933265eb4" />

El detalle de la versión 2, que es la que tiene el alias produccion:
<img width="900" alt="Detalle de la version 2 con el alias produccion" src="https://github.com/user-attachments/assets/69c715e4-f8c1-4a00-beaf-22b20dbbeaef" />

El esquema de entrada que muestra MLflow son las seis variables que recibe la API, y el alias produccion es el que aparece en el campo modelo de las respuestas de /predict.

### Artefactos en MinIO

En MinIO está el bucket donde MLflow guarda los artefactos. Las carpetas 1 y 2 son los dos experimentos:
<img width="900" alt="Bucket mlflow-artifacts en MinIO" src="https://github.com/user-attachments/assets/9a644637-84dc-495c-800b-c229a18a4313" />

Dentro de cada experimento hay una carpeta por ejecución, con el modelo y sus archivos:
<img width="900" alt="Carpetas de los runs dentro del experimento 2" src="https://github.com/user-attachments/assets/6c13bef6-a818-4007-93c7-735f34fc47b7" />

Son 378 objetos en total, que corresponden a los modelos de los 54 runs con sus archivos asociados. Los nombres de las carpetas son los identificadores de cada ejecución, y la relación entre esos identificadores y los parámetros de cada run está en la base de metadata de MLflow.


### Inferencia con la API

Revisar que la API tenga el modelo cargado:

```
curl -s http://localhost:8005/health
```

```
{"estado":"ok","modelo_cargado":true,"uri":"models:/penguins-classifier@produccion"}
```

Pedir una predicción:

```
curl -s -X POST http://localhost:8005/predict -H "Content-Type: application/json" -d '{"culmen_length_mm": 39.1, "culmen_depth_mm": 18.7, "flipper_length_mm": 181, "body_mass_g": 3750, "island": "Torgersen", "sex": "MALE"}'
```

```
{"especie_predicha":"Adelie","modelo":"models:/penguins-classifier@produccion"}
```

Otra predicción con medidas distintas:

```
curl -s -X POST http://localhost:8005/predict -H "Content-Type: application/json" -d '{"culmen_length_mm": 49.1, "culmen_depth_mm": 14.8, "flipper_length_mm": 220, "body_mass_g": 5150, "island": "Biscoe", "sex": "FEMALE"}'
```

```
{"especie_predicha":"Gentoo","modelo":"models:/penguins-classifier@produccion"}
```

Las medidas de la primera petición corresponden a un pingüino Adelie del dataset y las de la segunda a un Gentoo, así que las dos predicciones son correctas.
También se puede probar desde el navegador en http://10.43.97.104:8005/docs, que es la documentación que genera FastAPI.

<img width="900" alt="Prediccion ejecutada desde la documentacion de la API" src="https://github.com/user-attachments/assets/12033524-d4a0-4304-bcc6-66d7fce34e03" />


### Dos observaciones sobre los resultados

Con las seis variables (las cuatro medidas más isla y sexo) casi todos los modelos dieron exactitud de 1.0 sobre el conjunto de prueba, así que los hiperparámetros no cambiaban nada. El problema resultó demasiado fácil para este dataset. Por eso corrí un segundo experimento usando solo dos variables (culmen_depth_mm y body_mass_g), que son las menos discriminantes, y ahí sí se ve diferencia entre configuraciones: la exactitud baja y los modelos con max_depth=10 quedan peor que los de max_depth=3, que entiendo como sobreajuste.

Primer experimento, con las seis variables:
```
[01/27] n=50 d=3 s=2 -> acc=1.0000 f1=1.0000
[02/27] n=50 d=3 s=5 -> acc=1.0000 f1=1.0000
[03/27] n=50 d=3 s=10 -> acc=1.0000 f1=1.0000
[07/27] n=50 d=10 s=2 -> acc=0.9851 f1=0.9873
[27/27] n=200 d=10 s=10 -> acc=1.0000 f1=1.0000
```

Segundo experimento, solo con dos variables:
```
[01/27] n=50 d=3 s=2 -> acc=0.7910 f1=0.6019
[04/27] n=50 d=5 s=2 -> acc=0.7612 f1=0.5905
[07/27] n=50 d=10 s=2 -> acc=0.7164 f1=0.6010
[16/27] n=100 d=10 s=2 -> acc=0.7164 f1=0.6010
[27/27] n=200 d=10 s=10 -> acc=0.7761 f1=0.6334
```
También quedaron dos versiones del modelo en el registro. La primera la registré ordenando los runs con order_by de search_runs, pero MLflow guarda los parámetros como texto y el orden salió alfabético en vez de numérico ("100" antes que "50", "10" antes que "3"), así que eligió uno de los modelos más complejos. En la versión 2 hice el ordenamiento en Python convirtiendo los parámetros a entero, y ahí sí quedó el más simple entre los empatados. Dejé las dos versiones en vez de borrar la primera, porque la idea del registro es que quede el historial. El alias produccion apunta a la versión 2.

```
Empatados en accuracy maxima: 26
Mas simple entre ellos: rf_03_n50_d3_s10
  n_estimators=50, max_depth=3, min_samples_split=10

Registrado como version 2
```
## Cómo cambiar el modelo que usa la API

La API no apunta a un archivo sino al alias produccion del Model Registry, como se ve en la variable MODELO_URI del docker-compose.yaml:

```
MODELO_URI: models:/penguins-classifier@produccion
```

Para poner otro modelo en producción hay dos pasos.

Primero, mover el alias a la versión que se quiera, desde la interfaz de MLflow (pestaña Models, en la versión correspondiente) o desde Python:
```
from mlflow.tracking import MlflowClient

client = MlflowClient()
client.set_registered_model_alias(
    name="penguins-classifier",
    alias="produccion",
    version=3,
)
```

Segundo, pedirle a la API que vuelva a cargar el modelo, porque lo guarda en memoria después de la primera carga:

```
curl -s -X POST http://localhost:8005/reload
```

No hay que reiniciar el contenedor ni cambiar el código de la API.

```
{"mensaje":"Modelo recargado desde MLflow","uri":"models:/penguins-classifier@produccion"}
```
