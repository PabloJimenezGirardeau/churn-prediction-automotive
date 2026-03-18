"""
Churn Prediction Dashboard — Sector Automocion
Entry point de la aplicacion Streamlit.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Churn Prediction — Automocion",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar branding
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0.5rem 1rem 0.5rem;">
        <div style="width: 60px; height: 60px; margin: 0 auto 0.8rem auto;
                    background: linear-gradient(135deg, #3498db, #2ecc71);
                    border-radius: 16px; display: flex; align-items: center;
                    justify-content: center; box-shadow: 0 4px 15px rgba(52,152,219,0.3);">
            <span style="font-size: 1.8rem; line-height: 1;">🚗</span>
        </div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff;
                    letter-spacing: 1.5px;">CHURN PREDICTOR</div>
        <div style="font-size: 0.72rem; color: #556677; margin-top: 0.3rem;
                    letter-spacing: 2px; text-transform: uppercase;">Sector Automocion</div>
    </div>
    <hr style="border-color: rgba(52,152,219,0.12); margin: 0.5rem 1rem;">
    """, unsafe_allow_html=True)

    # Info del modelo
    st.markdown("""
    <div style="background: rgba(52,152,219,0.06); border-radius: 10px;
                padding: 0.8rem 1rem; margin: 0.5rem 0;">
        <div style="font-size: 0.7rem; color: #3498db; text-transform: uppercase;
                    letter-spacing: 1px; font-weight: 600; margin-bottom: 0.5rem;">
            Modelo activo</div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span style="color: #6c8091; font-size: 0.78rem;">Algoritmo</span>
            <span style="color: #e0e0e0; font-size: 0.78rem; font-weight: 500;">Random Forest</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span style="color: #6c8091; font-size: 0.78rem;">Clientes</span>
            <span style="color: #e0e0e0; font-size: 0.78rem; font-weight: 500;">10,000</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #6c8091; font-size: 0.78rem;">Estado</span>
            <span style="color: #2ecc71; font-size: 0.78rem; font-weight: 500;">● Activo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Hero banner
st.markdown("""
<div class="hero-banner">
    <h1>Churn Prediction Dashboard</h1>
    <p>Predice el riesgo de abandono de tus clientes y diseña la estrategia optima de retencion.</p>
</div>
""", unsafe_allow_html=True)

# Navegacion por tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Resumen",
    "🔍 Explorador",
    "💼 Estrategia",
    "⚙️ Sensibilidad",
    "🚀 Piloto Auto",
    "🧠 Modelo",
])

# Importar paginas
from pages.p1_resumen import render as render_resumen
from pages.p2_explorador import render as render_explorador
from pages.p3_estrategia import render as render_estrategia
from pages.p4_sensibilidad import render as render_sensibilidad
from pages.p5_piloto import render as render_piloto
from pages.p6_modelo import render as render_modelo

with tab1:
    try:
        render_resumen()
    except Exception as e:
        st.error("Error en Resumen: " + str(e))
with tab2:
    try:
        render_explorador()
    except Exception as e:
        st.error("Error en Explorador: " + str(e))
with tab3:
    try:
        render_estrategia()
    except Exception as e:
        st.error("Error en Estrategia: " + str(e))
with tab4:
    try:
        render_sensibilidad()
    except Exception as e:
        st.error("Error en Sensibilidad: " + str(e))
with tab5:
    try:
        render_piloto()
    except Exception as e:
        st.error("Error en Piloto: " + str(e))
with tab6:
    try:
        render_modelo()
    except Exception as e:
        st.error("Error en Modelo: " + str(e))
