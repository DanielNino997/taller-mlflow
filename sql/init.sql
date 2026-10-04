-- Dos etapas de datos para el taller de MLflow
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;

-- ETAPA 1: datos crudos, tal como vienen del CSV (todo TEXT)
CREATE TABLE IF NOT EXISTS raw.penguins_raw (
    id                  SERIAL PRIMARY KEY,
    species             TEXT,
    island              TEXT,
    bill_length_mm      TEXT,
    bill_depth_mm       TEXT,
    flipper_length_mm   TEXT,
    body_mass_g         TEXT,
    sex                 TEXT,
    ingested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETAPA 2: datos procesados, listos para entrenamiento
CREATE TABLE IF NOT EXISTS clean.penguins_clean (
    id                  SERIAL PRIMARY KEY,
    species             VARCHAR(20),
    island              VARCHAR(20),
    culmen_length_mm    DOUBLE PRECISION,
    culmen_depth_mm     DOUBLE PRECISION,
    flipper_length_mm   DOUBLE PRECISION,
    body_mass_g         DOUBLE PRECISION,
    sex                 VARCHAR(10),
    processed_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
