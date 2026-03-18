"""Carga de datos y modelo con caching de Streamlit."""

import pickle
import os
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@st.cache_resource
def load_model():
    """Carga el modelo entrenado (se ejecuta una sola vez)."""
    with open(os.path.join(DATA_DIR, "modelo_churn.pkl"), "rb") as f:
        return pickle.load(f)


@st.cache_resource
def load_columns():
    """Carga la lista de features del modelo."""
    with open(os.path.join(DATA_DIR, "columnas_modelo.pkl"), "rb") as f:
        return pickle.load(f)


@st.cache_resource
def load_threshold():
    """Carga el threshold optimo."""
    with open(os.path.join(DATA_DIR, "threshold.pkl"), "rb") as f:
        return pickle.load(f)


@st.cache_resource
def load_shap():
    """Carga SHAP values pre-computados."""
    with open(os.path.join(DATA_DIR, "shap_values.pkl"), "rb") as f:
        return pickle.load(f)


@st.cache_resource
def load_model_metrics():
    """Carga metricas del modelo pre-computadas."""
    with open(os.path.join(DATA_DIR, "model_metrics.pkl"), "rb") as f:
        return pickle.load(f)


@st.cache_resource
def load_staging_features():
    """Carga features preprocesadas de staging con Customer_ID."""
    with open(os.path.join(DATA_DIR, "staging_features.pkl"), "rb") as f:
        return pickle.load(f)


@st.cache_data
def load_costes():
    """Carga tabla de costes por modelo."""
    df = pd.read_csv(os.path.join(DATA_DIR, "Costes.csv"))
    df["alpha"] = df["Modelo"].apply(lambda m: 0.07 if m in ["A", "B"] else 0.10)
    return df


@st.cache_data
def load_estrategia():
    """Carga las predicciones + estrategia comercial de staging."""
    from utils.business_rules import CONVERSION_RATES
    df = pd.read_csv(os.path.join(DATA_DIR, "estrategia_comercial.csv"))
    # Forzar tipos numericos para evitar errores de formato
    num_cols = ["Prob_Churn", "CLTV", "Inversion_accion", "Margen_neto",
                "Margen_neto_pct", "ROI", "Revenue_at_Risk", "PVP"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # Añadir Conversion_rate si no existe (CSV generado antes de este campo)
    if "Conversion_rate" not in df.columns and "Accion" in df.columns:
        df["Conversion_rate"] = df["Accion"].map(CONVERSION_RATES).fillna(0.20)
        df["ROI"] = (df["Margen_neto"] * df["Conversion_rate"]) / df["Inversion_accion"].clip(lower=0.01)
    return df
