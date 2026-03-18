"""Pagina 6 — Acerca del Modelo."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_loader import load_model_metrics
from utils.charts import apply_theme, C_GREEN, C_RED, C_BLUE, C_ORANGE, C_PURPLE


def render():
    m = load_model_metrics()

    # --- Header ---
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2332, #16213e);
                border: 1px solid rgba(52,152,219,0.12); border-radius: 14px;
                padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.2rem; font-weight: 700; color: #e0e0e0; margin-bottom: 0.5rem;">
            Modelo de Prediccion de Churn</div>
        <div style="font-size: 0.85rem; color: #6c8091; line-height: 1.6;">
            Random Forest entrenado sobre datos historicos del concesionario.
            Predice la probabilidad de que un cliente abandone el taller oficial
            (>400 dias sin revision).</div>
    </div>
    """, unsafe_allow_html=True)

    # --- KPIs del modelo ---
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        ("AUC-ROC", f"{m['auc_roc']:.3f}", C_BLUE),
        ("Precision", f"{m['precision']:.1%}", C_ORANGE),
        ("Recall", f"{m['recall']:.1%}", C_GREEN),
        ("F1-Score", f"{m['f1']:.3f}", C_PURPLE),
        ("Accuracy", f"{m['accuracy']:.1%}", "#8899aa"),
    ]
    for col, (label, value, color) in zip([c1, c2, c3, c4, c5], kpis):
        col.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e2a3a, #16213e);
                    border-top: 3px solid {color}; border-radius: 10px;
                    padding: 1rem; text-align: center;">
            <div style="font-size: 0.7rem; color: #6c8091; text-transform: uppercase;
                        letter-spacing: 1px;">{label}</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff;
                        margin-top: 0.3rem;">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROC + PR + Confusion Matrix ---
    col_roc, col_pr, col_cm = st.columns(3)

    chart_layout = dict(
        height=350,
        margin=dict(t=50, b=50, l=50, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#c0c0c0", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )

    with col_roc:
        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(
            x=m["roc_fpr"], y=m["roc_tpr"],
            mode="lines", name="Modelo",
            line=dict(color=C_BLUE, width=3),
            fill="tozeroy", fillcolor="rgba(52,152,219,0.1)",
        ))
        fig_roc.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1],
            mode="lines", name="Aleatorio",
            line=dict(color="#556677", width=1, dash="dash"),
        ))
        fig_roc.update_layout(
            title=f"Curva ROC (AUC = {m['auc_roc']:.3f})",
            title_x=0.5,
            xaxis_title="FPR",
            yaxis_title="TPR",
            legend=dict(x=0.5, y=0.1, font=dict(size=10)),
            **chart_layout,
        )
        st.plotly_chart(fig_roc, use_container_width=True, key="mod_roc")

    with col_pr:
        fig_pr = go.Figure()
        fig_pr.add_trace(go.Scatter(
            x=m["pr_recall"], y=m["pr_precision"],
            mode="lines", name="Modelo",
            line=dict(color=C_ORANGE, width=3),
            fill="tozeroy", fillcolor="rgba(243,156,18,0.1)",
        ))
        # Linea base = prevalencia
        prevalence = m["n_churn"] / m["n_train"]
        fig_pr.add_hline(y=prevalence, line_dash="dash", line_color="#556677",
                         annotation_text=f"Base: {prevalence:.1%}",
                         annotation_font_color="#8899aa",
                         annotation_position="top right")
        fig_pr.update_layout(
            title="Curva Precision-Recall",
            title_x=0.5,
            xaxis_title="Recall",
            yaxis_title="Precision",
            yaxis_range=[0, 1],
            showlegend=False,
            **chart_layout,
        )
        st.plotly_chart(fig_pr, use_container_width=True, key="mod_pr")

    with col_cm:
        cm = np.array(m["confusion_matrix"])
        cm_pct = cm / cm.sum() * 100
        labels = [["VN", "FP"], ["FN", "VP"]]

        fig_cm = go.Figure(go.Heatmap(
            z=cm_pct,
            x=["Pred. No Churn", "Pred. Churn"],
            y=["Real No Churn", "Real Churn"],
            colorscale=[[0, "#0e1117"], [0.5, "#1a3a5c"], [1, "#3498db"]],
            showscale=False,
            text=[[f"{labels[i][j]}<br>{cm[i][j]:,}<br>({cm_pct[i][j]:.1f}%)"
                   for j in range(2)] for i in range(2)],
            texttemplate="%{text}",
            textfont=dict(size=14, color="#e0e0e0"),
        ))
        fig_cm.update_layout(
            title="Matriz de Confusion",
            title_x=0.5,
            height=350,
            margin=dict(t=50, b=50, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#c0c0c0", size=11),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_cm, use_container_width=True, key="mod_cm")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Feature Importance ---
    st.markdown("#### Top 20 Features mas importantes")

    feat_names = m["feature_names"]
    feat_imp = m["feature_importances"]
    top_idx = np.argsort(feat_imp)[-20:]
    top_names = [feat_names[i] for i in top_idx]
    top_vals = [feat_imp[i] for i in top_idx]

    # Nombres legibles
    name_map = {
        "en_garantia_bin": "En garantia",
        "seguro_bateria": "Seguro bateria",
        "Equipamiento_ord": "Equipamiento",
        "tiene_ext_garantia": "Extension garantia",
        "tiene_datos_demo": "Datos demograficos",
        "fuel_electrico": "Fuel electrico",
        "es_particular": "Es particular",
        "origen_tienda": "Origen tienda",
        "tiene_descuento": "Tiene descuento",
        "Margen_pct": "Margen %",
        "Margen_eur_bruto": "Margen bruto (€)",
        "Margen_eur": "Margen neto (€)",
        "Gasto_relativo": "Gasto relativo",
        "RENTA_MEDIA_ESTIMADA": "Renta estimada",
        "COSTE_VENTA_NO_IMPUESTOS": "Coste venta s/imp.",
        "ENCUESTA_CLIENTE_ZONA_TALLER": "Encuesta taller",
        "MANTENIMIENTO_GRATUITO": "Mant. gratuito",
        "Lead_compra": "Lead compra",
    }
    display_names = [name_map.get(n, n.replace("_", " ")) for n in top_names]

    # Color por importancia
    max_val = max(top_vals)
    colors = [f"rgba(52,152,219,{0.3 + 0.7 * (v / max_val)})" for v in top_vals]

    fig_fi = go.Figure(go.Bar(
        y=display_names,
        x=top_vals,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1%}" for v in top_vals],
        textposition="outside",
        textfont=dict(color="#c0c0c0", size=11),
    ))
    fig_fi.update_layout(
        height=550,
        margin=dict(t=20, b=30, l=180, r=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#c0c0c0"),
        xaxis=dict(title="Importancia relativa",
                   tickformat=".0%",
                   gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig_fi, use_container_width=True, key="mod_fi")

    # --- Detalles tecnicos ---
    st.markdown("<br>", unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e2a3a, #16213e);
                    border-radius: 10px; padding: 1.2rem 1.5rem;">
            <div style="font-size: 0.9rem; font-weight: 700; color: #3498db;
                        margin-bottom: 0.8rem;">Configuracion del modelo</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Algoritmo</span>
                <span style="color: #e0e0e0; font-weight: 600;">Random Forest</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Arboles</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + str(m["n_estimators"]) + """</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Profundidad max.</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + str(m["max_depth"]) + """</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Features</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + str(m["n_features"]) + """</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #8899aa; font-size: 0.85rem;">Threshold optimo</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + f"{m['threshold']:.4f}" + """</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_d2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e2a3a, #16213e);
                    border-radius: 10px; padding: 1.2rem 1.5rem;">
            <div style="font-size: 0.9rem; font-weight: 700; color: #3498db;
                        margin-bottom: 0.8rem;">Datos de entrenamiento</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Total registros</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + f"{m['n_train']:,}" + """</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Churn (Y)</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + f"{m['n_churn']:,} ({m['n_churn']/m['n_train']:.1%})" + """</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">No Churn (N)</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + f"{m['n_no_churn']:,} ({m['n_no_churn']/m['n_train']:.1%})" + """</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span style="color: #8899aa; font-size: 0.85rem;">Ratio desbalanceo</span>
                <span style="color: #e0e0e0; font-weight: 600;">""" + f"1:{m['n_no_churn']//m['n_churn']}" + """</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #8899aa; font-size: 0.85rem;">Definicion churn</span>
                <span style="color: #e0e0e0; font-weight: 600;">>400 dias sin revision</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Interpretacion ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(52,152,219,0.06); border-left: 3px solid #3498db;
                border-radius: 0 10px 10px 0; padding: 1rem 1.5rem;">
        <div style="font-size: 0.9rem; font-weight: 700; color: #3498db;
                    margin-bottom: 0.5rem;">Interpretacion de metricas</div>
        <div style="font-size: 0.85rem; color: #8899aa; line-height: 1.8;">
            <b style="color: #e0e0e0;">AUC-ROC = """ + f"{m['auc_roc']:.3f}" + """</b> —
            El modelo distingue bien entre clientes que abandonan y los que no.<br>
            <b style="color: #e0e0e0;">Recall = """ + f"{m['recall']:.1%}" + """</b> —
            Detecta la gran mayoria de los clientes que realmente abandonan.<br>
            <b style="color: #e0e0e0;">Precision = """ + f"{m['precision']:.1%}" + """</b> —
            De los que marca como churn, un """ + f"{m['precision']:.0%}" + """ realmente lo son.
            El resto son "falsas alarmas", pero el coste de contactar un cliente que no iba a
            abandonar es bajo frente al coste de perderlo.<br>
            <b style="color: #e0e0e0;">Threshold = """ + f"{m['threshold']:.2f}" + """</b> —
            Optimizado para maximizar el valor de negocio (balance entre inversión y retención).
        </div>
    </div>
    """, unsafe_allow_html=True)
