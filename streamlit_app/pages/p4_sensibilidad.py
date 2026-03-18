"""Pagina 4 — Sensibilidad del Threshold y Descuentos."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_loader import load_estrategia, load_threshold, load_costes
from utils.charts import C_BLUE, C_RED, C_GREEN, C_ORANGE
from utils.business_rules import (
    ACCIONES, ACCION_ORDER, ACCION_COLORS, MARGEN_MIN, CONVERSION_RATES,
    build_business_df,
)


def render():
    df = load_estrategia()
    t_opt = load_threshold()

    # ========== SECCION 1: SENSIBILIDAD DEL THRESHOLD ==========
    st.markdown("### Sensibilidad del Threshold")
    st.caption("Observa como cambian los KPIs al mover el umbral de decision.")

    t_slider = st.slider(
        "Threshold", 0.10, 0.90, float(t_opt), 0.01,
        key="sens_threshold",
        help="Umbral para clasificar un cliente como alto riesgo.",
    )

    # Calcular metricas para varios thresholds
    thresholds = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    if t_slider not in thresholds:
        thresholds.append(t_slider)
        thresholds.sort()

    rar_total = float(df["Revenue_at_Risk"].sum())
    rows = []
    for t in thresholds:
        alto = df[df["Prob_Churn"] >= t]
        n = len(alto)
        inv = float(alto["Inversion_accion"].sum())
        rar = float(alto["Revenue_at_Risk"].sum())
        mar = float(alto["Margen_neto"].sum())
        rows.append({
            "Threshold": t,
            "n_alto": n,
            "pct_cartera": n / len(df),
            "Inversion": inv,
            "RAR_capturado": rar,
            "pct_rar": rar / rar_total if rar_total > 0 else 0,
            "ROI": float((alto["Margen_neto"] * alto["Conversion_rate"]).sum()) / inv if inv > 0 else 0,
        })
    sens_df = pd.DataFrame(rows)

    # KPIs del threshold seleccionado
    current = sens_df[sens_df["Threshold"] == t_slider].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes alto riesgo", f"{int(current['n_alto']):,}",
              f"{current['pct_cartera']:.1%} de la cartera")
    c2.metric("Inversion necesaria", f"{current['Inversion']:,.0f}€")
    c3.metric("Revenue at Risk capturado", f"{current['pct_rar']:.1%}",
              f"{current['RAR_capturado']:,.0f}€")
    c4.metric("ROI estimado", f"{current['ROI']:.1f}x")

    # Grafico
    fig = go.Figure()

    # Barras de clientes
    bar_colors = [C_ORANGE if t == t_slider else C_BLUE for t in sens_df["Threshold"]]
    fig.add_trace(go.Bar(
        x=sens_df["Threshold"].astype(str),
        y=sens_df["n_alto"],
        name="Clientes alto riesgo",
        marker_color=bar_colors,
        opacity=0.8,
    ))

    # Linea de % RAR
    fig.add_trace(go.Scatter(
        x=sens_df["Threshold"].astype(str),
        y=sens_df["pct_rar"],
        name="% Revenue at Risk capturado",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=C_RED, width=3),
        marker=dict(size=10),
    ))

    fig.update_layout(
        title_text="Cobertura vs Inversion segun Threshold",
        title_x=0.5,
        xaxis_title="Threshold",
        yaxis=dict(title="Clientes alto riesgo", color=C_BLUE),
        yaxis2=dict(title="% RAR capturado", side="right", overlaying="y",
                    color=C_RED, tickformat=".0%"),
        height=400,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=80, b=40),
    )
    st.plotly_chart(fig, use_container_width=True, key="sens_threshold_chart")

    # Tabla detallada
    with st.expander("Tabla detallada"):
        display = sens_df.copy()
        display.columns = ["Threshold", "Clientes alto", "% cartera", "Inversion",
                           "RAR capturado", "% RAR", "ROI"]
        st.dataframe(display.style.format({
            "Threshold": "{:.2f}",
            "Clientes alto": "{:,.0f}",
            "% cartera": "{:.1%}",
            "Inversion": "{:,.0f}€",
            "RAR capturado": "{:,.0f}€",
            "% RAR": "{:.1%}",
            "ROI": "{:.1f}x",
        }).highlight_max(subset=["ROI"], color="#d4edda")
         .highlight_max(subset=["% RAR"], color="#fff3cd"),
         use_container_width=True)

    # ========== SECCION 2: AJUSTAR DESCUENTOS ==========
    st.markdown("---")
    st.markdown("### Ajustar Descuentos")
    st.caption("Modifica los porcentajes de descuento y observa el impacto en ROI y margen.")

    col1, col2 = st.columns(2)

    with col1:
        d_premium = st.slider("Ret. Premium (%)", 5, 50, 30, 1, key="d_prem")
        d_estandar = st.slider("Ret. Estandar (%)", 5, 40, 22, 1, key="d_est")

    with col2:
        d_fideliza = st.slider("Fidelizacion (%)", 3, 30, 15, 1, key="d_fid")
        d_prevent = st.slider("Mant. Preventivo (%)", 1, 20, 8, 1, key="d_prev")

    # Recalcular con nuevos descuentos
    custom_acciones = {
        "Retencion Premium":        {"desc_pct": d_premium/100, "desc_fijo": 0, "contacto": 50},
        "Retencion Estandar":       {"desc_pct": d_estandar/100, "desc_fijo": 0, "contacto": 35},
        "Fidelizacion Activa":      {"desc_pct": d_fideliza/100, "desc_fijo": 0, "contacto": 20},
        "Mantenimiento Preventivo": {"desc_pct": d_prevent/100, "desc_fijo": 0, "contacto": 10},
    }

    # Mostrar impacto
    costes = load_costes()
    c1_medio = float((costes["Mantenimiento_medio"] * (1 + costes["alpha"])).mean())
    mb_medio = c1_medio * 0.93  # ~93% margen bruto medio

    st.markdown("#### Impacto estimado")

    rows_impact = []
    for acc in ACCION_ORDER:
        params = custom_acciones[acc]
        desc = c1_medio * params["desc_pct"]
        inv = desc + params["contacto"]
        mn = mb_medio - inv
        mn_pct = mn / c1_medio
        conv = CONVERSION_RATES.get(acc, 0.25)
        roi = mn * conv / inv if inv > 0 else 0
        cumple = "✅" if mn_pct >= MARGEN_MIN else "❌"
        rows_impact.append({
            "Accion": acc,
            "Descuento": f"{params['desc_pct']:.0%}",
            "Inversion": f"{inv:.0f}€",
            "Margen neto": f"{mn:.0f}€ ({mn_pct:.0%})",
            "ROI": f"{roi:.1f}x",
            "Cumple 37%": cumple,
        })

    impact_df = pd.DataFrame(rows_impact)

    # Valores numericos para graficos
    inv_vals = [float(r.replace("€", "")) for r in impact_df["Inversion"]]
    roi_vals = [float(r.replace("x", "")) for r in impact_df["ROI"]]
    margen_vals = []
    for m in impact_df["Margen neto"]:
        pct = m.split("(")[1].replace(")", "").replace("%", "")
        margen_vals.append(int(pct) / 100)

    # Nombres cortos para las barras
    short_names = ["Premium", "Estandar", "Fidelizacion", "Preventivo"]
    bar_color = "#3498db"

    col_g1, col_g2 = st.columns(2)

    # --- Grafico 1: Inversion por accion ---
    with col_g1:
        fig_inv = go.Figure(go.Bar(
            x=short_names,
            y=inv_vals,
            marker_color=bar_color,
            text=["{:.0f}€".format(v) for v in inv_vals],
            textposition="outside",
            textfont=dict(color="#e0e0e0", size=12),
        ))
        fig_inv.update_layout(
            title_text="Inversion por accion",
            title_x=0.5,
            height=320,
            yaxis=dict(title="€", gridcolor="rgba(255,255,255,0.05)"),
            margin=dict(t=50, b=40, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#c0c0c0"),
        )
        st.plotly_chart(fig_inv, use_container_width=True, key="sens_inv_chart")

    # --- Grafico 2: ROI por accion ---
    with col_g2:
        roi_colors = [C_GREEN if m >= MARGEN_MIN else C_RED for m in margen_vals]
        fig_roi = go.Figure(go.Bar(
            x=short_names,
            y=roi_vals,
            marker_color=roi_colors,
            text=["{:.1f}x {}".format(r, "✅" if m >= MARGEN_MIN else "❌")
                  for r, m in zip(roi_vals, margen_vals)],
            textposition="outside",
            textfont=dict(color="#e0e0e0", size=12),
        ))
        fig_roi.update_layout(
            title_text="ROI por accion",
            title_x=0.5,
            height=320,
            yaxis=dict(title="ROI (x)", gridcolor="rgba(255,255,255,0.05)"),
            margin=dict(t=50, b=40, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#c0c0c0"),
        )
        st.plotly_chart(fig_roi, use_container_width=True, key="sens_roi_chart")

    # Tabla detallada
    with st.expander("Tabla detallada"):
        st.dataframe(impact_df, use_container_width=True, hide_index=True)
