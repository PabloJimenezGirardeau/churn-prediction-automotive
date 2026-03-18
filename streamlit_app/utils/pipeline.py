"""Pipeline de limpieza y Feature Engineering — replica exacta del notebook."""

import numpy as np
import pandas as pd


def limpiar_datos(df):
    """Pipeline de limpieza reproducible."""
    df = df.copy()
    df["QUEJA"] = df["QUEJA"].fillna("SIN_REGISTRO")
    df["STATUS_SOCIAL"] = df["STATUS_SOCIAL"].fillna("DESCONOCIDO")
    df["GENERO"] = df["GENERO"].fillna("DESCONOCIDO")
    df["EXTENSION_GARANTIA"] = df["EXTENSION_GARANTIA"].replace(
        "SI, Campa a Regalo", "SI, Campaña Regalo"
    )
    if "DAYS_LAST_SERVICE" in df.columns:
        df = df.drop(columns=["DAYS_LAST_SERVICE"])
    return df


def feature_engineering(df, costes_df):
    """Crea features derivadas y encoding — replica del notebook."""
    df = df.copy()

    # Merge con costes (temporal, para features derivadas)
    df = df.merge(costes_df[["Modelo", "Margen", "Costetransporte",
                              "Margendistribuidor", "GastosMarketing",
                              "Mantenimiento_medio", "Comisión_Marca", "alpha"]],
                  on="Modelo", how="left")

    # Parsear fechas
    for col in ["Sales_Date", "FIN_GARANTIA", "BASE_DATE"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Features temporales
    if "BASE_DATE" in df.columns and "Sales_Date" in df.columns:
        df["Antiguedad_dias"] = (df["BASE_DATE"] - df["Sales_Date"]).dt.days
    if "FIN_GARANTIA" in df.columns and "BASE_DATE" in df.columns:
        df["Dias_fin_garantia"] = (df["FIN_GARANTIA"] - df["BASE_DATE"]).dt.days

    # Features derivadas
    df["Margen_pct"] = np.where(df["PVP"] > 0, df["Margen_eur"] / df["PVP"], 0)
    df["Gasto_relativo"] = np.where(
        df["RENTA_MEDIA_ESTIMADA"] > 0,
        df["PVP"] / df["RENTA_MEDIA_ESTIMADA"],
        0,
    )
    ant = (df.get("Antiguedad_dias", pd.Series(dtype=float)) / 365.25).clip(lower=1/365.25)
    if "Revisiones" in df.columns:
        df["Revisiones_por_ano"] = df["Revisiones"] / ant
        df["perfil_cliente"] = (df["Revisiones"] == 0).astype(int)

    # Flags binarios
    df["tiene_datos_demo"] = (
        (df["RENTA_MEDIA_ESTIMADA"] > 0) | (df["ENCUESTA_CLIENTE_ZONA_TALLER"] > 0)
    ).astype(int)
    df["tiene_ext_garantia"] = (df["EXTENSION_GARANTIA"] != "NO").astype(int)
    df["en_garantia_bin"] = (df["EN_GARANTIA"] == "SI").astype(int)
    if "MANTENIMIENTO_GRATUITO" in df.columns and "Revisiones" in df.columns:
        df["mant_pendiente"] = (df["MANTENIMIENTO_GRATUITO"] > df["Revisiones"]).astype(int)
    df["seguro_bateria"] = (df["SEGURO_BATERIA_LARGO_PLAZO"] == "SI").astype(int)
    df["es_particular"] = (df["MOTIVO_VENTA"] == "Particular").astype(int)
    df["origen_tienda"] = (df["Origen"] == "Tienda").astype(int)
    df["fuel_electrico"] = (df["Fuel"] == "ELECTRICO").astype(int)
    df["tiene_descuento"] = (df["COSTE_VENTA_NO_IMPUESTOS"] > 0).astype(int)

    # Encoding
    df["Equipamiento_ord"] = df["Equipamiento"].map(
        {"Low": 0, "Mid": 1, "Mid-High": 2, "High": 3}
    )
    df = df.drop(columns=["Equipamiento"], errors="ignore")

    ohe_cols = ["GENERO", "QUEJA", "ZONA", "FORMA_PAGO", "Modelo",
                "TIENDA_DESC", "STATUS_SOCIAL"]
    ohe_cols = [c for c in ohe_cols if c in df.columns]
    df = pd.get_dummies(df, columns=ohe_cols, drop_first=True, dtype=int)

    # Eliminar columnas
    cols_drop = [
        "CODE", "Id_Producto", "Customer_ID",
        "Sales_Date", "FIN_GARANTIA", "BASE_DATE",
        "TRANSMISION_ID", "TIPO_CARROCERIA", "PROV_DESC", "Fuel",
        "MOTIVO_VENTA", "Origen", "EN_GARANTIA", "SEGURO_BATERIA_LARGO_PLAZO",
        "EXTENSION_GARANTIA", "CODIGO_POSTAL",
        "Costetransporte", "Margendistribuidor", "GastosMarketing",
        "Mantenimiento_medio", "Comisión_Marca", "Margen", "alpha",
        "Lead_compra_1", "Churn_400", "Churn",
        "Revisiones", "Revisiones_por_ano", "perfil_cliente",
        "Km_medio_por_revision", "km_ultima_revision",
        "Antiguedad_dias", "Dias_fin_garantia", "mant_pendiente",
    ]
    df = df.drop(columns=[c for c in cols_drop if c in df.columns])

    return df


def align_columns(df, model_columns):
    """Alinea columnas del DataFrame con las del modelo entrenado."""
    for c in set(model_columns) - set(df.columns):
        df[c] = 0
    extra = [c for c in df.columns if c not in model_columns]
    if extra:
        df = df.drop(columns=extra)
    return df[model_columns]


def full_pipeline(df_raw, costes_df, model, model_columns, threshold):
    """Pipeline completo: limpieza -> FE -> prediccion -> segmentacion."""
    # Guardar identificadores antes de transformar
    customer_ids = df_raw["Customer_ID"].values if "Customer_ID" in df_raw.columns else range(len(df_raw))
    modelos = df_raw["Modelo"].values if "Modelo" in df_raw.columns else ["?"] * len(df_raw)
    revisiones = df_raw["Revisiones"].values if "Revisiones" in df_raw.columns else [0] * len(df_raw)
    pvp = df_raw["PVP"].values if "PVP" in df_raw.columns else [0] * len(df_raw)

    # Pipeline
    df_clean = limpiar_datos(df_raw)
    df_fe = feature_engineering(df_clean, costes_df)
    X = align_columns(df_fe, model_columns)

    # Prediccion
    proba = model.predict_proba(X)[:, 1]

    # Resultado
    result = pd.DataFrame({
        "Customer_ID": customer_ids,
        "Modelo": modelos,
        "Revisiones": revisiones,
        "PVP": pvp,
        "Prob_Churn": proba.round(4),
        "Riesgo": pd.cut(
            proba,
            bins=[0, 0.3, max(threshold, 0.301), 1.0],
            labels=["Bajo", "Medio", "Alto"],
            include_lowest=True,
        ),
    })

    return result
