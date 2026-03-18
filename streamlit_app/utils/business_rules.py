"""Business Rules Engine — asignacion de acciones y calculos economicos."""

import numpy as np
import pandas as pd


ACCIONES = {
    "Retencion Premium":        {"desc_pct": 0.30, "desc_fijo": 0, "contacto": 50},
    "Retencion Estandar":       {"desc_pct": 0.22, "desc_fijo": 0, "contacto": 35},
    "Fidelizacion Activa":      {"desc_pct": 0.15, "desc_fijo": 0, "contacto": 20},
    "Mantenimiento Preventivo": {"desc_pct": 0.08, "desc_fijo": 0, "contacto": 10},
}

# Tasa de conversion estimada por accion (% de clientes que responden positivamente)
CONVERSION_RATES = {
    "Retencion Premium":        0.42,
    "Retencion Estandar":       0.40,
    "Fidelizacion Activa":      0.38,
    "Mantenimiento Preventivo": 0.50,
}

ACCION_ORDER = [
    "Retencion Premium",
    "Retencion Estandar",
    "Fidelizacion Activa",
    "Mantenimiento Preventivo",
]

MARGEN_MIN = 0.37  # 30% concesionario + 7% marca

ACCION_COLORS = {
    "Retencion Premium": "#e74c3c",
    "Retencion Estandar": "#f39c12",
    "Fidelizacion Activa": "#3498db",
    "Mantenimiento Preventivo": "#27ae60",
}

RIESGO_COLORS = {
    "Bajo": "#27ae60",
    "Medio": "#f39c12",
    "Alto": "#e74c3c",
}


def asignar_accion(row):
    """Asigna accion comercial segun riesgo y valor."""
    if row["Riesgo"] == "Alto" and row["Valor"] == "Alto":
        return "Retencion Premium"
    if row["Riesgo"] == "Alto":
        return "Retencion Estandar"
    if row["Riesgo"] == "Medio":
        return "Fidelizacion Activa"
    return "Mantenimiento Preventivo"


def calcular_economics(row, acciones_config=None):
    """Calcula ingreso, costes y margen neto."""
    if acciones_config is None:
        acciones_config = ACCIONES

    accion = row["Accion"]
    params = acciones_config[accion]
    cn = row["C_n"]
    margen_bruto = row["Margen_bruto"]

    descuento = params["desc_fijo"] + cn * params["desc_pct"]
    coste_contacto = params["contacto"]
    inversion = descuento + coste_contacto

    margen_neto = margen_bruto - inversion
    margen_neto_pct = margen_neto / cn if cn > 0 else 0

    # Ajuste automatico si no cumple margen minimo
    ajustado = False
    if margen_neto_pct < MARGEN_MIN and descuento > 0:
        desc_max = margen_bruto - cn * MARGEN_MIN - coste_contacto
        if desc_max > 0:
            descuento = desc_max
            ajustado = True
        else:
            descuento = 0
        inversion = descuento + coste_contacto
        margen_neto = margen_bruto - inversion
        margen_neto_pct = margen_neto / cn if cn > 0 else 0

    return pd.Series({
        "Descuento": round(descuento, 2),
        "Coste_contacto": coste_contacto,
        "Inversion_accion": round(inversion, 2),
        "Margen_neto": round(margen_neto, 2),
        "Margen_neto_pct": round(margen_neto_pct, 4),
        "Ajustado": ajustado,
    })


def calcular_cltv(row, horizonte=5):
    """CLTV: margen bruto acumulado en las proximas `horizonte` revisiones."""
    base = row["Mantenimiento_medio"]
    alpha = row["alpha"]
    com_marca = row["Comision_Marca_pct"]
    n0 = row["Revisiones"]
    total = 0
    for i in range(n0 + 1, n0 + horizonte + 1):
        cn = base * (1 + alpha) ** i
        ops = cn * 0.01 + cn * com_marca
        total += cn - ops
    return round(total, 2)


def build_business_df(result_df, costes_df, threshold=None, acciones_config=None):
    """Construye el DataFrame completo de negocio a partir de predicciones."""
    if acciones_config is None:
        acciones_config = ACCIONES

    df = result_df.copy()

    # Merge con costes
    costes_merge = costes_df.copy()
    costes_merge["alpha"] = costes_merge["Modelo"].apply(
        lambda m: 0.07 if m in ["A", "B"] else 0.10
    )
    df = df.merge(costes_merge, on="Modelo", how="left")

    # C(n)
    df["n_prox"] = df["Revisiones"] + 1
    df["C_n"] = df["Mantenimiento_medio"] * (1 + df["alpha"]) ** df["n_prox"]

    # Costes operativos
    df["Comision_Marca_pct"] = df["Comisión_Marca"] / 100
    df["Coste_mkt_var"] = df["C_n"] * 0.01
    df["Coste_marca"] = df["C_n"] * df["Comision_Marca_pct"]
    df["Costes_op"] = df["Coste_mkt_var"] + df["Coste_marca"]

    # Margen bruto
    df["Margen_bruto"] = df["C_n"] - df["Costes_op"]

    # CLTV
    df["CLTV"] = df.apply(calcular_cltv, axis=1)
    cltv_mediana = df["CLTV"].median()
    df["Valor"] = np.where(df["CLTV"] >= cltv_mediana, "Alto", "Bajo")

    # Asignar acciones
    df["Accion"] = df.apply(asignar_accion, axis=1)

    # Calcular economics
    econ = df.apply(lambda row: calcular_economics(row, acciones_config), axis=1)
    df = pd.concat([df, econ], axis=1)

    # ROI ajustado por tasa de conversion
    df["Conversion_rate"] = df["Accion"].map(CONVERSION_RATES)
    df["ROI"] = (df["Margen_neto"] * df["Conversion_rate"]) / df["Inversion_accion"].clip(lower=0.01)
    df["Revenue_at_Risk"] = df["CLTV"] * df["Prob_Churn"]

    return df
