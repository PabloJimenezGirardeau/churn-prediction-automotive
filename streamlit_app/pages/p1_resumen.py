"""Pagina 1 — Resumen Ejecutivo."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_estrategia, load_threshold
from utils.charts import (donut_riesgo, bar_churn_modelo, hist_probabilidades,
                          apply_theme, C_GREEN, C_RED, C_BLUE, C_ORANGE, C_PURPLE,
                          RIESGO_COLORS)


def metric_html(icon, label, value, subtitle="", color="#3498db"):
    """Genera HTML para un KPI card con icono."""
    return f"""
    <div style="background: linear-gradient(135deg, #1e2a3a 0%, #16213e 100%);
                border: 1px solid rgba(52,152,219,0.12); border-radius: 14px;
                padding: 1.2rem 1.5rem; text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                border-top: 3px solid {color};">
        <div style="font-size: 1.6rem; margin-bottom: 0.3rem;">{icon}</div>
        <div style="font-size: 0.75rem; color: #6c8091; text-transform: uppercase;
                    letter-spacing: 1px; font-weight: 500;">{label}</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #ffffff;
                    margin: 0.3rem 0;">{value}</div>
        <div style="font-size: 0.8rem; color: #556677;">{subtitle}</div>
    </div>
    """


def render():
    df = load_estrategia()
    t_opt = load_threshold()

    # --- Sidebar filters ---
    with st.sidebar:
        st.markdown("""
        <div style="margin-top: 0.5rem;">
            <div style="font-size: 0.7rem; color: #3498db; text-transform: uppercase;
                        letter-spacing: 1.5px; font-weight: 600; margin-bottom: 0.8rem;">
                🎛️ Filtros de analisis</div>
        </div>
        """, unsafe_allow_html=True)

        all_modelos = sorted(df["Modelo"].unique())
        opciones_modelo = ["-- Todos --"] + all_modelos

        modelos_raw = st.multiselect(
            "Modelo de vehiculo",
            opciones_modelo,
            default=["-- Todos --"],
            key="res_modelo",
            placeholder="Selecciona modelos...",
        )
        if "-- Todos --" in modelos_raw:
            modelos_sel = all_modelos
        else:
            modelos_sel = modelos_raw

        opciones_riesgo = ["-- Todos --", "Bajo", "Medio", "Alto"]
        riesgo_raw = st.multiselect(
            "Nivel de riesgo",
            opciones_riesgo,
            default=["-- Todos --"],
            key="res_riesgo",
            placeholder="Selecciona riesgo...",
        )
        if "-- Todos --" in riesgo_raw:
            riesgo_sel = ["Bajo", "Medio", "Alto"]
        else:
            riesgo_sel = riesgo_raw

        prob_range = st.slider(
            "Rango de probabilidad (%)",
            min_value=0, max_value=100, value=(0, 100), step=1,
            key="res_prob",
            format="%d%%",
        )
        prob_range = (prob_range[0] / 100, prob_range[1] / 100)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="border-top: 1px solid rgba(52,152,219,0.1);
                    padding-top: 0.8rem; margin-top: 0.5rem;">
            <div style="font-size: 0.65rem; color: #3d4f5f; text-align: center;
                        line-height: 1.6;">
                Caso Practico IA<br>
                <span style="color: #556677;">Machine Learning &bull; 2025</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Apply filters
    mask = (
        df["Modelo"].isin(modelos_sel)
        & df["Riesgo"].isin(riesgo_sel)
        & df["Prob_Churn"].between(prob_range[0], prob_range[1])
    )
    dff = df[mask]

    if len(dff) == 0:
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <h3 style="color: #8899aa;">No hay clientes con los filtros seleccionados</h3>
            <p style="color: #556677;">Ajusta los filtros en el sidebar para ver resultados.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # --- KPIs ---
    n_total = len(dff)
    n_alto = int((dff["Riesgo"] == "Alto").sum())
    pct_alto = n_alto / n_total if n_total > 0 else 0
    rar_total = float(dff["Revenue_at_Risk"].sum())
    inv_total = float(dff["Inversion_accion"].sum())
    roi_global = float((dff["Margen_neto"] * dff["Conversion_rate"]).sum() / dff["Inversion_accion"].sum()) if inv_total > 0 else 0
    cltv_medio = float(dff["CLTV"].mean())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(metric_html("👥", "Clientes", f"{n_total:,}", "en cartera", C_BLUE), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_html("⚠️", "Alto Riesgo", f"{pct_alto:.1%}", f"{n_alto:,} clientes", C_RED), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_html("💰", "Revenue at Risk", f"{rar_total/1000:,.0f}K€", "ingreso en riesgo", C_ORANGE), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_html("📤", "Inversion", f"{inv_total/1000:,.0f}K€", "en acciones", C_PURPLE), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_html("📈", "ROI Global", f"{roi_global:.1f}x", "retorno", C_GREEN), unsafe_allow_html=True)
    with c6:
        st.markdown(metric_html("🏆", "CLTV Medio", f"{cltv_medio:,.0f}€", "por cliente", C_BLUE), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Charts ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.plotly_chart(donut_riesgo(dff), use_container_width=True, key="res_donut")

    with col2:
        st.plotly_chart(bar_churn_modelo(dff), use_container_width=True, key="res_bar_modelo")

    with col3:
        st.plotly_chart(hist_probabilidades(dff, t_opt), use_container_width=True, key="res_hist")

    # --- Resumen por segmento ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Desglose por Segmento de Riesgo")

    cols_seg = st.columns(3)
    for i, riesgo in enumerate(["Bajo", "Medio", "Alto"]):
        sub = dff[dff["Riesgo"] == riesgo]
        if len(sub) == 0:
            continue
        color = RIESGO_COLORS[riesgo]
        inv_s = float(sub["Inversion_accion"].sum())
        mar_s = float(sub["Margen_neto"].sum())
        conv_s = float(sub["Conversion_rate"].mean()) if "Conversion_rate" in sub.columns else 0.25
        roi_s = (mar_s * conv_s) / inv_s if inv_s > 0 else 0

        with cols_seg[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e2a3a, #16213e);
                        border-left: 4px solid {color}; border-radius: 10px;
                        padding: 1.2rem 1.5rem; margin-bottom: 1rem;">
                <div style="font-size: 1rem; font-weight: 700; color: {color};
                            margin-bottom: 0.8rem;">{riesgo.upper()}</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="color: #8899aa; font-size: 0.85rem;">Clientes</span>
                    <span style="color: #e0e0e0; font-weight: 600;">{len(sub):,}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="color: #8899aa; font-size: 0.85rem;">Prob. media</span>
                    <span style="color: #e0e0e0; font-weight: 600;">{float(sub['Prob_Churn'].mean()):.1%}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="color: #8899aa; font-size: 0.85rem;">Inversion</span>
                    <span style="color: #e0e0e0; font-weight: 600;">{inv_s:,.0f}€</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="color: #8899aa; font-size: 0.85rem;">Margen neto</span>
                    <span style="color: #e0e0e0; font-weight: 600;">{mar_s:,.0f}€</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8899aa; font-size: 0.85rem;">ROI</span>
                    <span style="color: {color}; font-weight: 700; font-size: 1.1rem;">{roi_s:.1f}x</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- Tabla expandible ---
    with st.expander("📋 Detalle por modelo"):
        resumen = dff.groupby("Modelo").agg(
            Clientes=("Modelo", "count"),
            Prob_media=("Prob_Churn", "mean"),
            CLTV_medio=("CLTV", "mean"),
            Inversion=("Inversion_accion", "sum"),
            Margen_neto=("Margen_neto", "sum"),
        ).round(2)
        conv_medio = dff.groupby("Modelo")["Conversion_rate"].mean()
        resumen["ROI"] = (resumen["Margen_neto"] * conv_medio / resumen["Inversion"].clip(lower=0.01)).round(1)
        resumen = resumen.sort_values("Prob_media", ascending=False)
        st.dataframe(resumen, use_container_width=True)
