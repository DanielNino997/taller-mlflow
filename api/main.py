"""API de inferencia que consume el modelo desde el Model Registry de MLflow."""
import os

import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODELO_URI = os.getenv("MODELO_URI", "models:/penguins-classifier@produccion")

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])

app = FastAPI(
    title="API Penguins - Taller MLflow",
    description="Predice la especie de un penguin tomando el modelo desde MLflow",
    version="1.0",
)

_modelo = None


class Penguin(BaseModel):
    culmen_length_mm: float = Field(..., example=39.1)
    culmen_depth_mm: float = Field(..., example=18.7)
    flipper_length_mm: float = Field(..., example=181.0)
    body_mass_g: float = Field(..., example=3750.0)
    island: str = Field(..., example="Torgersen")
    sex: str = Field(..., example="MALE")


def obtener_modelo():
    global _modelo
    if _modelo is None:
        try:
            _modelo = mlflow.sklearn.load_model(MODELO_URI)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo cargar el modelo desde MLflow: {e}",
            )
    return _modelo


@app.get("/")
def inicio():
    return {
        "mensaje": "API de inferencia activa",
        "modelo": MODELO_URI,
        "documentacion": "/docs",
    }


@app.get("/health")
def salud():
    try:
        obtener_modelo()
        return {"estado": "ok", "modelo_cargado": True, "uri": MODELO_URI}
    except HTTPException:
        return {"estado": "degradado", "modelo_cargado": False, "uri": MODELO_URI}


@app.post("/reload")
def recargar():
    global _modelo
    _modelo = None
    obtener_modelo()
    return {"mensaje": "Modelo recargado desde MLflow", "uri": MODELO_URI}


@app.post("/predict")
def predecir(penguin: Penguin):
    modelo = obtener_modelo()
    datos = pd.DataFrame([{
        "culmen_length_mm": penguin.culmen_length_mm,
        "culmen_depth_mm": penguin.culmen_depth_mm,
        "flipper_length_mm": penguin.flipper_length_mm,
        "body_mass_g": penguin.body_mass_g,
        "island": penguin.island,
        "sex": penguin.sex,
    }])
    especie = modelo.predict(datos)[0]
    return {"especie_predicha": str(especie), "modelo": MODELO_URI}
