"""Pagina 2 — Explorador de Clientes + What-if."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_loader import (load_estrategia, load_model, load_columns,
                                load_shap, load_threshold, load_staging_features)
from utils.business_rules import RIESGO_COLORS, ACCION_COLORS
from utils.charts import apply_theme, C_GREEN, C_RED, C_BLUE, C_ORANGE


def shap_waterfall_plotly(shap_vals_row, feature_names, feature_values, base_value, prediction, top_n=10):
    """Crea un waterfall chart de SHAP con Plotly."""
    abs_vals = np.abs(shap_vals_row)
    top_idx = np.argsort(abs_vals)[-top_n:][::-1]

    feats = []
    for i in top_idx:
        val = feature_values[i]
        if isinstance(val, (int, float, np.floating, np.integer)):
            feats.append(feature_names[i] + " = " + "{:.3g}".format(val))
        else:
            feats.append(feature_names[i] + " = " + str(val))

    vals = [shap_vals_row[i] for i in top_idx]
    rest = float(np.sum(shap_vals_row)) - sum(vals)
    feats.append("Resto (" + str(len(feature_names) - top_n) + " feat.)")
    vals.append(rest)

    cumulative = base_value
    x_starts = []
    for v in vals:
        x_starts.append(cumulative)
        cumulative += v

    colors = ["#e74c3c" if v > 0 else "#2ecc71" for v in vals]

    fig = go.Figure()
    for i, (feat, val, start) in enumerate(zip(feats, vals, x_starts)):
        fig.add_trace(go.Bar(
            y=[feat], x=[val], base=[start],
            orientation="h",
            marker_color=colors[i],
            showlegend=False,
            hovertemplate=feat + "<br>SHAP: " + "{:+.4f}".format(val) + "<extra></extra>",
        ))
        fig.add_annotation(
            x=start + val, y=feat,
            text="{:+.4f}".format(val), showarrow=False,
            font=dict(size=9, color="#c0c0c0"),
            xanchor="left" if val > 0 else "right",
        )

    fig.add_vline(x=base_value, line_dash="dash", line_color="#556677",
                  annotation_text="Base: {:.3f}".format(base_value),
                  annotation_font_color="#8899aa")
    fig.add_vline(x=prediction, line_dash="dot", line_color="#e0e0e0",
                  annotation_text="Pred: {:.1%}".format(prediction),
                  annotation_font_color="#e0e0e0")

    fig.update_layout(
        title="SHAP Waterfall",
        xaxis_title="SHAP value",
        height=380,
        yaxis=dict(autorange="reversed"),
    )
    return apply_theme(fig)


def gauge_chart(prob, threshold):
    """Gauge de probabilidad de churn."""
    if prob >= threshold:
        color = C_RED
    elif prob >= 0.3:
        color = C_ORANGE
    else:
        color = C_GREEN

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob * 100,
        number=dict(suffix="%", font=dict(size=36, color="#e0e0e0")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#556677",
                      tickfont=dict(color="#8899aa")),
            bar=dict(color=color),
            bgcolor="#1a1a2e",
            borderwidth=0,
            steps=[
                dict(range=[0, 30], color="rgba(46, 204, 113, 0.1)"),
                dict(range=[30, threshold * 100], color="rgba(243, 156, 18, 0.1)"),
                dict(range=[threshold * 100, 100], color="rgba(231, 76, 60, 0.1)"),
            ],
            threshold=dict(
                line=dict(color="#e0e0e0", width=2),
                thickness=0.75,
                value=threshold * 100,
            ),
        ),
    ))
    fig.update_layout(
        height=200,
        margin=dict(t=30, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c0c0c0"),
    )
    return fig


def render():
    df = load_estrategia()
    model = load_model()
    model_cols = load_columns()
    shap_data = load_shap()
    t_opt = load_threshold()
    staging = load_staging_features()

    # Busqueda
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_id = st.text_input(
            "🔍 Buscar por Customer ID",
            placeholder="Ej: 103388",
            key="search_id",
        )
    with col_filter:
        riesgo_filter = st.selectbox(
            "Filtrar por riesgo",
            ["Todos", "Alto", "Medio", "Bajo"],
            key="exp_riesgo",
        )

    dff = df.copy()
    if riesgo_filter != "Todos":
        dff = dff[dff["Riesgo"] == riesgo_filter]
    if search_id:
        try:
            search_val = int(search_id)
            dff = dff[dff["Customer_ID"] == search_val]
        except ValueError:
            st.error("Introduce un ID numerico valido.")
            return

    # Tabla
    display_cols = ["Customer_ID", "Modelo", "Prob_Churn", "Riesgo", "CLTV",
                    "Accion", "Inversion_accion", "Margen_neto", "ROI"]
    st.dataframe(
        dff[display_cols].head(100).style.format({
            "Prob_Churn": "{:.1%}",
            "CLTV": "{:,.0f}",
            "Inversion_accion": "{:,.0f}",
            "Margen_neto": "{:,.0f}",
            "ROI": "{:.1f}",
        }),
        use_container_width=True,
        height=280,
    )

    if len(dff) == 0:
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <div style="font-size: 2.5rem;">🔍</div>
            <p style="color: #8899aa;">No se encontro el cliente. Verifica el ID.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("---")

    # Seleccionar cliente
    cliente_ids = dff["Customer_ID"].tolist()
    selected_id = st.selectbox(
        "Selecciona un cliente para ver su ficha completa",
        cliente_ids, index=0, key="selected_client",
    )

    cliente = dff[dff["Customer_ID"] == selected_id].iloc[0]

    # --- FICHA DEL CLIENTE ---
    riesgo_val = str(cliente["Riesgo"])
    riesgo_color = RIESGO_COLORS.get(riesgo_val, "#666")
    accion_val = str(cliente["Accion"])
    accion_color = ACCION_COLORS.get(accion_val, "#666")

    # Header de ficha
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e2a3a, #16213e);
                border: 1px solid rgba(52,152,219,0.12); border-radius: 14px;
                padding: 1rem 1.5rem; margin-bottom: 1rem;
                display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 0.8rem; color: #6c8091; text-transform: uppercase;
                         letter-spacing: 1px;">Cliente</span>
            <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff;">"""
    + str(selected_id) + """</div>
        </div>
        <div style="text-align: center;">
            <span style="font-size: 0.8rem; color: #6c8091;">Modelo</span>
            <div style="font-size: 1.3rem; font-weight: 600; color: #3498db;">"""
    + str(cliente["Modelo"]) + """</div>
        </div>
        <div style="text-align: center;">
            <span style="background: """ + riesgo_color + """;
                         color: white; padding: 0.4rem 1.2rem; border-radius: 20px;
                         font-weight: 600; font-size: 0.9rem;">"""
    + riesgo_val + """</span>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 0.8rem; color: #6c8091;">Accion</span>
            <div style="font-size: 0.95rem; font-weight: 600; color: """ + accion_color + """;">"""
    + accion_val + """</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Gauge + metricas + SHAP
    col_gauge, col_metrics, col_shap = st.columns([1, 1, 2])

    with col_gauge:
        st.plotly_chart(gauge_chart(float(cliente["Prob_Churn"]), t_opt),
                        use_container_width=True, key="exp_gauge")
        st.markdown(
            "<p style='text-align: center; color: #8899aa; font-size: 0.85rem; margin-top: -10px;'>"
            "Probabilidad de Churn</p>",
            unsafe_allow_html=True,
        )

    with col_metrics:
        metrics = [
            ("CLTV", "{:,.0f}€".format(float(cliente["CLTV"])), "💰"),
            ("Inversion", "{:,.0f}€".format(float(cliente["Inversion_accion"])), "📤"),
            ("Margen neto", "{:,.0f}€".format(float(cliente["Margen_neto"])), "📊"),
            ("ROI", "{:.1f}x".format(float(cliente["ROI"])), "📈"),
        ]
        for label, value, icon in metrics:
            st.markdown(
                "<div style='background: #1a1a2e; border-radius: 8px; padding: 0.6rem 1rem;"
                " margin-bottom: 0.5rem; display: flex; justify-content: space-between;"
                " align-items: center;'>"
                "<span style='color: #8899aa; font-size: 0.85rem;'>"
                + icon + " " + label + "</span>"
                "<span style='color: #e0e0e0; font-weight: 600;'>"
                + value + "</span></div>",
                unsafe_allow_html=True,
            )

    with col_shap:
        feature_names = shap_data["feature_names"]
        pred = float(cliente["Prob_Churn"])

        # Buscar features reales del cliente en staging
        cid_mask = staging["customer_ids"] == selected_id
        if np.any(cid_mask):
            import shap as shap_lib
            row_idx = int(np.where(cid_mask)[0][0])
            x_row = staging["X"].iloc[[row_idx]]
            explainer = shap_lib.TreeExplainer(model)
            sv = explainer.shap_values(x_row)
            if isinstance(sv, list):
                sv = sv[1]  # clase positiva
            elif hasattr(sv, 'ndim') and sv.ndim == 3:
                sv = sv[:, :, 1]  # (n, features, classes) -> clase 1
            shap_row = sv[0]
            base_val = explainer.expected_value
            if isinstance(base_val, (list, np.ndarray)):
                base_val = float(base_val[1])
            feat_vals = x_row.iloc[0].values
        else:
            # Fallback: usar SHAP pre-computados
            shap_vals = shap_data["shap_values"]
            shap_sample = shap_data["sample_data"]
            idx = min(selected_id % len(shap_vals), len(shap_vals) - 1)
            shap_row = shap_vals[idx]
            base_val = 0.5
            feat_vals = shap_sample.iloc[idx].values

        fig = shap_waterfall_plotly(
            shap_row, feature_names, feat_vals,
            float(base_val), pred, top_n=8,
        )
        st.plotly_chart(fig, use_container_width=True, key="exp_shap")

    # --- WHAT-IF SIMULATOR ---
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2332 0%, #16213e 100%);
                border: 1px solid rgba(52,152,219,0.12); border-radius: 14px;
                padding: 1.5rem; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; margin-bottom: 1.2rem;">
            <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #9b59b6, #8e44ad);
                        border-radius: 10px; display: flex; align-items: center; justify-content: center;
                        margin-right: 0.8rem; font-size: 1.1rem;">🧪</div>
            <div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #e0e0e0;">Simulador What-if</div>
                <div style="font-size: 0.78rem; color: #6c8091;">
                    Modifica variables del cliente y observa como cambia la prediccion</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Obtener valores actuales del cliente para defaults
    cid_wif_mask = staging["customer_ids"] == selected_id
    if np.any(cid_wif_mask):
        wif_row_idx = int(np.where(cid_wif_mask)[0][0])
        wif_current = staging["X"].iloc[wif_row_idx]
        def_garantia = bool(wif_current.get("en_garantia_bin", 0))
        def_seguro = bool(wif_current.get("seguro_bateria", 0))
        def_ext = bool(wif_current.get("tiene_ext_garantia", 0))
        def_equip = int(wif_current.get("Equipamiento_ord", 0))
        def_edad = int(wif_current.get("Edad", 40))
        def_queja = bool(wif_current.get("QUEJA_SI", 0))
        def_mant_gratis = int(wif_current.get("MANTENIMIENTO_GRATUITO", 0))
        def_fuel_elec = bool(wif_current.get("fuel_electrico", 0))
        # Detectar modelo actual del cliente
        modelo_dummies = [c for c in staging["X"].columns if c.startswith("Modelo_")]
        def_modelo = "A"  # default (drop_first)
        for md in modelo_dummies:
            if wif_current.get(md, 0) == 1:
                def_modelo = md.replace("Modelo_", "")
                break
        # Detectar forma de pago actual
        fp_dummies = [c for c in staging["X"].columns if c.startswith("FORMA_PAGO_")]
        def_forma_pago = "Contado"  # default (drop_first)
        for fp in fp_dummies:
            if wif_current.get(fp, 0) == 1:
                def_forma_pago = fp.replace("FORMA_PAGO_", "")
                break
    else:
        def_garantia, def_seguro, def_ext = False, False, False
        def_equip, def_edad, def_queja = 0, 40, False
        def_modelo, def_mant_gratis = "A", 0
        def_fuel_elec, def_forma_pago = False, "Contado"

    col_w1, col_w2, col_w3, col_w4 = st.columns(4)

    with col_w1:
        st.markdown("**Servicios**")
        wif_garantia = st.toggle("En garantia", value=def_garantia, key="wif_gar")
        wif_seguro = st.toggle("Seguro bateria", value=def_seguro, key="wif_seg")
        wif_ext = st.toggle("Extension garantia", value=def_ext, key="wif_ext")
        wif_queja = st.toggle("Tiene queja", value=def_queja, key="wif_queja")

    with col_w2:
        st.markdown("**Perfil**")
        wif_edad = st.slider("Edad", 18, 80, def_edad, 1, key="wif_edad")
        wif_mant = st.number_input("Mant. gratuito", 0, 10, def_mant_gratis, 1, key="wif_mant")
        formas_pago = ["Contado", "Financiera Marca", "Prestamo Bancario", "Otros"]
        wif_fp = st.selectbox("Forma de pago", formas_pago,
                              index=formas_pago.index(def_forma_pago) if def_forma_pago in formas_pago else 0,
                              key="wif_fp")

    with col_w3:
        st.markdown("**Vehiculo**")
        modelos_list = sorted(df["Modelo"].unique())
        wif_modelo = st.selectbox("Modelo", modelos_list,
                                  index=modelos_list.index(def_modelo) if def_modelo in modelos_list else 0,
                                  key="wif_modelo")
        wif_equip = st.selectbox("Equipamiento", ["Low", "Mid", "Mid-High", "High"],
                                 index=def_equip, key="wif_equip")
        equip_num = {"Low": 0, "Mid": 1, "Mid-High": 2, "High": 3}[wif_equip]
        wif_fuel_elec = st.toggle("Fuel electrico", value=def_fuel_elec, key="wif_fuel")

    with col_w4:
        st.markdown("&nbsp;")
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
        run_sim = st.button("⚡ Recalcular", type="primary", key="btn_whatif",
                            use_container_width=True)

    if run_sim:
        try:
            # Usar features reales del cliente
            cid_mask_wif = staging["customer_ids"] == selected_id
            if np.any(cid_mask_wif):
                row_idx_wif = int(np.where(cid_mask_wif)[0][0])
                x_original = staging["X"].iloc[[row_idx_wif]].copy().reset_index(drop=True)
            else:
                x_original = pd.DataFrame([{col: 0 for col in model_cols}])

            # Aplicar variables modificadas
            if "en_garantia_bin" in x_original.columns:
                x_original["en_garantia_bin"] = int(wif_garantia)
            if "seguro_bateria" in x_original.columns:
                x_original["seguro_bateria"] = int(wif_seguro)
            if "Equipamiento_ord" in x_original.columns:
                x_original["Equipamiento_ord"] = equip_num
            if "tiene_ext_garantia" in x_original.columns:
                x_original["tiene_ext_garantia"] = int(wif_ext)
            if "Edad" in x_original.columns:
                x_original["Edad"] = wif_edad
            if "QUEJA_SI" in x_original.columns:
                x_original["QUEJA_SI"] = int(wif_queja)
            if "QUEJA_SIN_REGISTRO" in x_original.columns:
                x_original["QUEJA_SIN_REGISTRO"] = 0 if wif_queja else 1

            if "MANTENIMIENTO_GRATUITO" in x_original.columns:
                x_original["MANTENIMIENTO_GRATUITO"] = wif_mant
            if "fuel_electrico" in x_original.columns:
                x_original["fuel_electrico"] = int(wif_fuel_elec)

            # Forma de pago: resetear dummies y activar la correcta
            fp_dummy_cols = [c for c in x_original.columns if c.startswith("FORMA_PAGO_")]
            for fc in fp_dummy_cols:
                x_original[fc] = 0
            fp_col = "FORMA_PAGO_" + wif_fp
            if fp_col in x_original.columns:
                x_original[fp_col] = 1

            # Modelo: resetear todas las dummies y activar la correcta
            modelo_dummy_cols = [c for c in x_original.columns if c.startswith("Modelo_")]
            for mc in modelo_dummy_cols:
                x_original[mc] = 0
            modelo_col = "Modelo_" + wif_modelo
            if modelo_col in x_original.columns:
                x_original[modelo_col] = 1

            new_prob = model.predict_proba(x_original[model_cols])[:, 1][0]
            old_prob = float(cliente["Prob_Churn"])
            delta = new_prob - old_prob

            if delta < -0.05:
                verdict_color = "#2ecc71"
                verdict_icon = "✅"
                verdict_text = "La accion reduce el riesgo significativamente"
            elif delta < 0:
                verdict_color = "#3498db"
                verdict_icon = "ℹ️"
                verdict_text = "Ligera mejora en el riesgo"
            else:
                verdict_color = "#e67e22"
                verdict_icon = "⚠️"
                verdict_text = "La accion no mejora el riesgo"

            delta_color = "#2ecc71" if delta < 0 else "#e74c3c"
            delta_arrow = "↓" if delta < 0 else "↑"

            st.markdown("""
            <div style="background: linear-gradient(135deg, #1e2a3a, #16213e);
                        border: 1px solid rgba(52,152,219,0.12); border-radius: 12px;
                        padding: 1.2rem 1.5rem; margin-top: 0.8rem;
                        display: flex; align-items: center; justify-content: space-around; gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: #6c8091; text-transform: uppercase;
                                letter-spacing: 1px; margin-bottom: 0.3rem;">Prob. Original</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #8899aa;">"""
            + "{:.1%}".format(old_prob) + """</div>
                </div>
                <div style="font-size: 1.5rem; color: """ + delta_color + """;">""" + delta_arrow + """</div>
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: #6c8091; text-transform: uppercase;
                                letter-spacing: 1px; margin-bottom: 0.3rem;">Prob. Simulada</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #ffffff;">"""
            + "{:.1%}".format(new_prob) + """</div>
                    <div style="font-size: 0.85rem; color: """ + delta_color + """; font-weight: 600;">"""
            + "{:+.1%}".format(delta) + """</div>
                </div>
                <div style="width: 1px; height: 50px; background: rgba(255,255,255,0.08);"></div>
                <div style="text-align: center; max-width: 200px;">
                    <div style="font-size: 1.2rem; margin-bottom: 0.3rem;">""" + verdict_icon + """</div>
                    <div style="font-size: 0.82rem; color: """ + verdict_color + """;
                                font-weight: 600; line-height: 1.4;">""" + verdict_text + """</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error("Error en simulacion: " + str(e))
