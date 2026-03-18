"""Pagina 5 — Piloto Automatico: sube un CSV y obtiene predicciones."""

import streamlit as st
import pandas as pd
import io
import time
from utils.data_loader import load_model, load_columns, load_threshold, load_costes
from utils.pipeline import full_pipeline
from utils.business_rules import build_business_df, ACCION_ORDER, ACCION_COLORS, RIESGO_COLORS
from utils.charts import donut_riesgo, bar_acciones, C_GREEN, C_RED, C_BLUE, C_ORANGE


REQUIRED_COLS = [
    "Customer_ID", "Modelo", "Revisiones", "PVP", "Margen_eur",
    "RENTA_MEDIA_ESTIMADA", "ENCUESTA_CLIENTE_ZONA_TALLER",
    "EN_GARANTIA", "EXTENSION_GARANTIA", "SEGURO_BATERIA_LARGO_PLAZO",
    "MOTIVO_VENTA", "Origen", "Fuel", "Equipamiento",
    "QUEJA", "GENERO", "STATUS_SOCIAL", "ZONA", "FORMA_PAGO",
    "TIENDA_DESC", "MANTENIMIENTO_GRATUITO", "Kw",
    "COSTE_VENTA_NO_IMPUESTOS", "Sales_Date", "FIN_GARANTIA", "BASE_DATE",
]


def step_indicator(current_step):
    """Indicador visual de pasos del wizard."""
    steps = [
        ("1", "Subir CSV"),
        ("2", "Validar"),
        ("3", "Procesar"),
        ("4", "Resultados"),
        ("5", "Exportar"),
    ]
    html = '<div style="display: flex; justify-content: center; gap: 0.5rem; margin-bottom: 1.5rem;">'
    for num, label in steps:
        step_num = int(num)
        if step_num < current_step:
            bg = C_GREEN
            border = C_GREEN
            text_color = "white"
        elif step_num == current_step:
            bg = C_BLUE
            border = C_BLUE
            text_color = "white"
        else:
            bg = "transparent"
            border = "#334455"
            text_color = "#556677"

        html += (
            '<div style="display: flex; align-items: center; gap: 0.4rem;">'
            '<div style="width: 32px; height: 32px; border-radius: 50%; '
            'background: ' + bg + '; border: 2px solid ' + border + '; '
            'display: flex; align-items: center; justify-content: center; '
            'font-weight: 700; font-size: 0.85rem; color: ' + text_color + ';">'
            + num + '</div>'
            '<span style="color: ' + text_color + '; font-size: 0.8rem; '
            'font-weight: 500;">' + label + '</span>'
        )
        if num != "5":
            html += '<div style="width: 40px; height: 2px; background: ' + border + '; margin: 0 0.3rem;"></div>'
        html += '</div>'
    html += '</div>'
    return html


def render():
    model = load_model()
    model_cols = load_columns()
    t_opt = load_threshold()
    costes = load_costes()

    # Step indicator
    step = st.session_state.get("piloto_step", 1)

    # --- STEP 1: Upload ---
    st.markdown(step_indicator(1), unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📁</div>
        <h3 style="color: #e0e0e0; margin-bottom: 0.3rem;">Sube tu cartera de clientes</h3>
        <p style="color: #6c8091; font-size: 0.9rem;">
            El sistema ejecutara automaticamente: limpieza, prediccion,
            estrategia comercial y calculo de ROI.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Selecciona un archivo CSV",
        type=["csv"],
        key="piloto_upload",
        label_visibility="collapsed",
    )

    if uploaded is None:
        with st.expander("📋 Columnas necesarias en el CSV"):
            cols_df = pd.DataFrame({"Columna": REQUIRED_COLS})
            st.dataframe(cols_df, hide_index=True, use_container_width=True)
        return

    # --- STEP 2: Validacion ---
    st.markdown(step_indicator(2), unsafe_allow_html=True)

    try:
        df_raw = pd.read_csv(uploaded)
    except Exception as e:
        st.error("Error al leer el CSV: " + str(e))
        return

    missing = [c for c in REQUIRED_COLS if c not in df_raw.columns]
    if missing:
        st.markdown("""
        <div style="background: rgba(231,76,60,0.1); border: 1px solid rgba(231,76,60,0.3);
                    border-radius: 10px; padding: 1.2rem;">
            <div style="color: #e74c3c; font-weight: 700; margin-bottom: 0.5rem;">
                ❌ Faltan """ + str(len(missing)) + """ columnas obligatorias</div>
            <div style="color: #c0c0c0; font-size: 0.85rem;">"""
        + ", ".join(missing) + """</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("""
    <div style="background: rgba(46,204,113,0.1); border: 1px solid rgba(46,204,113,0.3);
                border-radius: 10px; padding: 1rem; text-align: center;">
        <span style="color: #2ecc71; font-weight: 600;">✅ CSV validado:</span>
        <span style="color: #e0e0e0;">""" + "{:,}".format(len(df_raw))
    + """ registros x """ + str(df_raw.shape[1]) + """ columnas</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- STEP 3: Pipeline ---
    st.markdown(step_indicator(3), unsafe_allow_html=True)

    progress = st.progress(0, text="Iniciando pipeline...")
    time.sleep(0.3)

    progress.progress(15, text="🧹 Limpiando datos...")
    result_df = full_pipeline(df_raw, costes, model, model_cols, t_opt)

    progress.progress(55, text="💼 Calculando estrategia comercial...")
    df_biz = build_business_df(result_df, costes, t_opt)

    progress.progress(85, text="📊 Generando visualizaciones...")
    time.sleep(0.3)

    progress.progress(100, text="✅ Pipeline completado!")
    time.sleep(0.5)
    progress.empty()

    # --- STEP 4: Resultados ---
    st.markdown(step_indicator(4), unsafe_allow_html=True)

    n_total = len(df_biz)
    n_alto = int((df_biz["Riesgo"] == "Alto").sum())
    inv_total = float(df_biz["Inversion_accion"].sum())
    margen_total = float(df_biz["Margen_neto"].sum())
    conv_total = float((df_biz["Margen_neto"] * df_biz["Conversion_rate"]).sum()) if "Conversion_rate" in df_biz.columns else margen_total
    roi = conv_total / inv_total if inv_total > 0 else 0

    # Hero resultado
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0d1117, #161b22, #1a2332);
                border: 1px solid rgba(52,152,219,0.15); padding: 1.5rem 2rem;
                border-radius: 14px; margin-bottom: 1.5rem; text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #e0e0e0;
                    margin-bottom: 0.8rem;">Analisis Completado</div>
        <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap;">
            <div>
                <div style="font-size: 2rem; font-weight: 700; color: #3498db;">"""
    + "{:,}".format(n_total) + """</div>
                <div style="color: #6c8091; font-size: 0.8rem;">Clientes analizados</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: 700; color: #e74c3c;">"""
    + "{:,}".format(n_alto) + """</div>
                <div style="color: #6c8091; font-size: 0.8rem;">En riesgo de abandono</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: 700; color: #f39c12;">"""
    + "{:,.0f}€".format(inv_total) + """</div>
                <div style="color: #6c8091; font-size: 0.8rem;">Inversion recomendada</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: 700; color: #2ecc71;">"""
    + "{:.1f}x".format(roi) + """</div>
                <div style="color: #6c8091; font-size: 0.8rem;">ROI esperado</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Graficas
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(donut_riesgo(df_biz), use_container_width=True, key="piloto_donut")
    with col2:
        st.plotly_chart(bar_acciones(df_biz, ACCION_ORDER, ACCION_COLORS),
                        use_container_width=True, key="piloto_bar_acciones")

    with st.expander("📋 Ver datos completos"):
        display_cols = ["Customer_ID", "Modelo", "Prob_Churn", "Riesgo", "CLTV",
                        "Accion", "Inversion_accion", "Margen_neto", "ROI"]
        available_cols = [c for c in display_cols if c in df_biz.columns]
        st.dataframe(df_biz[available_cols].head(200), use_container_width=True)

    # --- STEP 5: Exportar ---
    st.markdown("---")
    st.markdown(step_indicator(5), unsafe_allow_html=True)

    export_cols = ["Customer_ID", "Modelo", "Revisiones", "Prob_Churn", "Riesgo",
                   "Valor", "C_n", "CLTV", "Accion", "Descuento",
                   "Inversion_accion", "Margen_neto", "Margen_neto_pct", "ROI"]
    available_export = [c for c in export_cols if c in df_biz.columns]
    df_export = df_biz[available_export]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, sheet_name="Estrategia", index=False)
        resumen = df_biz.groupby("Accion").agg(
            Clientes=("Accion", "count"),
            Inversion_total=("Inversion_accion", "sum"),
            Margen_total=("Margen_neto", "sum"),
        ).round(0)
        conv_map = df_biz.groupby("Accion")["Conversion_rate"].first()
        resumen["ROI"] = ((resumen["Margen_total"] * resumen.index.map(conv_map)) / resumen["Inversion_total"].clip(lower=0.01)).round(1)
        resumen.to_excel(writer, sheet_name="Resumen")

    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0;">
        <p style="color: #8899aa;">Descarga el informe completo con estrategia y resumen.</p>
    </div>
    """, unsafe_allow_html=True)

    col_dl = st.columns([1, 2, 1])
    with col_dl[1]:
        st.download_button(
            "📥 Descargar Informe Excel",
            data=buffer.getvalue(),
            file_name="estrategia_comercial.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )
