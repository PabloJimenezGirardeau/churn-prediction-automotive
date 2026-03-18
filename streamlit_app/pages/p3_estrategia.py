"""Pagina 3 — Estrategia Comercial."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_estrategia, load_threshold
from utils.charts import (bar_acciones, bar_roi_accion, bar_cltv_modelo,
                          apply_theme, C_GREEN, C_RED, C_BLUE, C_ORANGE, C_PURPLE)
from utils.business_rules import ACCION_ORDER, ACCION_COLORS, RIESGO_COLORS


def kpi_card(icon, label, value, subtitle="", color="#3498db"):
    return (
        '<div style="background: linear-gradient(135deg, #1e2a3a 0%, #16213e 100%);'
        ' border: 1px solid rgba(52,152,219,0.12); border-radius: 14px;'
        ' padding: 1.2rem 1.5rem; text-align: center;'
        ' box-shadow: 0 4px 15px rgba(0,0,0,0.2);'
        ' border-top: 3px solid ' + color + ';">'
        '<div style="font-size: 1.5rem; margin-bottom: 0.3rem;">' + icon + '</div>'
        '<div style="font-size: 0.72rem; color: #6c8091; text-transform: uppercase;'
        ' letter-spacing: 1px; font-weight: 500;">' + label + '</div>'
        '<div style="font-size: 1.7rem; font-weight: 700; color: #ffffff;'
        ' margin: 0.3rem 0;">' + value + '</div>'
        '<div style="font-size: 0.78rem; color: #556677;">' + subtitle + '</div>'
        '</div>'
    )


def render():
    df = load_estrategia()
    t_opt = load_threshold()

    # --- KPIs ---
    inv_total = float(df["Inversion_accion"].sum())
    margen_total = float(df["Margen_neto"].sum())
    roi = float((df["Margen_neto"] * df["Conversion_rate"]).sum()) / inv_total if inv_total > 0 else 0
    margen_medio_pct = float(df["Margen_neto_pct"].mean())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("📤", "Inversion total",
                             "{:,.0f}€".format(inv_total), "en acciones comerciales", C_ORANGE),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("💰", "Margen neto total",
                             "{:,.0f}€".format(margen_total), "beneficio esperado", C_GREEN),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("📈", "ROI global",
                             "{:.1f}x".format(roi), "retorno sobre inversion", C_BLUE),
                    unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("🎯", "Margen neto medio",
                             "{:.1%}".format(margen_medio_pct), "por operacion", C_PURPLE),
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Distribucion de acciones + ROI ---
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(bar_acciones(df, ACCION_ORDER, ACCION_COLORS),
                        use_container_width=True, key="est_bar_acciones")

    with col2:
        st.plotly_chart(bar_roi_accion(df, ACCION_ORDER, ACCION_COLORS),
                        use_container_width=True, key="est_bar_roi")

    st.markdown("---")

    # --- CLTV + ROI por riesgo ---
    col3, col4 = st.columns(2)

    with col3:
        st.plotly_chart(bar_cltv_modelo(df), use_container_width=True, key="est_bar_cltv")

    with col4:
        # ROI por segmento
        rows = []
        for riesgo in ["Bajo", "Medio", "Alto"]:
            sub = df[df["Riesgo"] == riesgo]
            if len(sub) == 0:
                continue
            inv = float(sub["Inversion_accion"].sum())
            mar = float((sub["Margen_neto"] * sub["Conversion_rate"]).sum())
            rows.append({
                "Riesgo": riesgo,
                "ROI": mar / inv if inv > 0 else 0,
                "Margen_pct": float(sub["Margen_neto_pct"].mean()),
                "Clientes": len(sub),
            })
        roi_df = pd.DataFrame(rows)

        fig = go.Figure(go.Bar(
            x=roi_df["Riesgo"],
            y=roi_df["ROI"],
            marker_color=[RIESGO_COLORS[r] for r in roi_df["Riesgo"]],
            text=["{:.1f}x<br>({:.0%})".format(float(r), float(m)) for r, m in zip(roi_df["ROI"], roi_df["Margen_pct"])],
            textposition="outside",
            hovertemplate="%{x}<br>ROI: %{y:.1f}x<br>Clientes: %{customdata:,}<extra></extra>",
            customdata=roi_df["Clientes"],
        ))
        fig.update_layout(
            title_text="ROI por Segmento de Riesgo",
            title_x=0.5,
            yaxis_title="ROI",
            height=350,
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(apply_theme(fig), use_container_width=True, key="est_bar_roi_riesgo")

    # --- Comparador de escenarios ---
    st.markdown("---")
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <span style="font-size: 1.2rem; font-weight: 700; color: #e0e0e0;">⚡ Comparador de Escenarios</span>
        <span style="font-size: 0.85rem; color: #6c8091; margin-left: 1rem;">
            Compara dos thresholds diferentes y su impacto en la estrategia</span>
    </div>
    """, unsafe_allow_html=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        t1 = st.slider("Threshold Escenario A", 0.1, 0.9, 0.3, 0.05, key="t1_comp")
    with col_t2:
        t2 = st.slider("Threshold Escenario B", 0.1, 0.9, min(float(t_opt), 0.9), 0.05, key="t2_comp")

    def escenario_stats(threshold):
        alto = df[df["Prob_Churn"] >= threshold]
        n = len(alto)
        inv = float(alto["Inversion_accion"].sum())
        mar = float((alto["Margen_neto"] * alto["Conversion_rate"]).sum())
        rar = float(alto["Revenue_at_Risk"].sum())
        rar_pct = rar / float(df["Revenue_at_Risk"].sum()) if float(df["Revenue_at_Risk"].sum()) > 0 else 0
        roi = mar / inv if inv > 0 else 0
        return n, inv, mar, rar, rar_pct, roi

    n1, inv1, mar1, rar1, rar_pct1, roi1 = escenario_stats(t1)
    n2, inv2, mar2, rar2, rar_pct2, roi2 = escenario_stats(t2)

    def scenario_card(title, threshold, n, inv, mar, rar, rar_pct, roi, border_color):
        return (
            '<div style="background: linear-gradient(135deg, #1e2a3a, #16213e);'
            ' border: 1px solid rgba(52,152,219,0.12); border-radius: 14px;'
            ' padding: 1.5rem; border-left: 4px solid ' + border_color + ';">'
            '<div style="font-size: 1.1rem; font-weight: 700; color: ' + border_color + ';'
            ' margin-bottom: 1rem;">' + title + ' (t=' + "{:.2f}".format(threshold) + ')</div>'
            '<div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem;'
            ' padding-bottom: 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.05);">'
            '<span style="color: #8899aa;">Clientes alto riesgo</span>'
            '<span style="color: #e0e0e0; font-weight: 600;">'
            + "{:,}".format(n) + ' (' + "{:.1%}".format(n / len(df)) + ')</span></div>'
            '<div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem;'
            ' padding-bottom: 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.05);">'
            '<span style="color: #8899aa;">Inversion</span>'
            '<span style="color: #e0e0e0; font-weight: 600;">' + "{:,.0f}€".format(inv) + '</span></div>'
            '<div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem;'
            ' padding-bottom: 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.05);">'
            '<span style="color: #8899aa;">Revenue at Risk</span>'
            '<span style="color: #e0e0e0; font-weight: 600;">'
            + "{:,.0f}€".format(rar) + ' (' + "{:.1%}".format(rar_pct) + ')</span></div>'
            '<div style="display: flex; justify-content: space-between;">'
            '<span style="color: #8899aa;">ROI</span>'
            '<span style="color: ' + border_color + '; font-weight: 700; font-size: 1.2rem;">'
            + "{:.1f}x".format(roi) + '</span></div>'
            '</div>'
        )

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown(scenario_card("Escenario A", t1, n1, inv1, mar1, rar1, rar_pct1, roi1, C_BLUE),
                    unsafe_allow_html=True)
    with col_e2:
        st.markdown(scenario_card("Escenario B", t2, n2, inv2, mar2, rar2, rar_pct2, roi2, C_ORANGE),
                    unsafe_allow_html=True)
