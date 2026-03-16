# Churn Prediction — Sector Automocion

Modelo de Machine Learning para predecir la fuga de clientes en un concesionario oficial de automoviles, acompanado de una estrategia comercial rentable y un dashboard interactivo.

## Objetivo

Construir un sistema end-to-end que:
1. **Prediga** la probabilidad de abandono de cada cliente (churn = >400 dias sin revision en taller)
2. **Segmente** clientes por nivel de riesgo (Bajo / Medio / Alto)
3. **Disene** acciones comerciales de retencion con ROI positivo
4. **Visualice** los resultados en un dashboard interactivo

## Resultados del Modelo

| Metrica | Valor |
|---------|-------|
| AUC-ROC | 0.897 |
| Recall | 84.9% |
| Precision | 27.0% |
| F1-Score | 0.410 |
| Algoritmo | Random Forest (300 arboles, max_depth=15) |
| Features | 64 variables |
| Threshold | 0.498 (optimizado por valor de negocio) |

## Estructura del Proyecto

```
├── Churn_Prediction_Final.ipynb    # Notebook principal (EDA, modelado, estrategia)
├── bqresults.csv                   # Dataset de entrenamiento (58K registros)
├── nuevos_clientes.csv             # Dataset de staging (10K clientes)
├── Costes.csv                      # Parametros economicos por modelo
│
└── streamlit_app/                  # Dashboard interactivo
    ├── app.py                      # Entry point
    ├── assets/style.css            # Estilos CSS personalizados
    ├── .streamlit/config.toml      # Configuracion del tema
    ├── pages/
    │   ├── p1_resumen.py           # KPIs y vision general
    │   ├── p2_explorador.py        # Ficha de cliente + SHAP + What-if
    │   ├── p3_estrategia.py        # Estrategia comercial y escenarios
    │   ├── p4_sensibilidad.py      # Sensibilidad del threshold y descuentos
    │   ├── p5_piloto.py            # Pipeline automatico (upload CSV)
    │   └── p6_modelo.py            # Metricas y explicabilidad del modelo
    ├── utils/
    │   ├── business_rules.py       # Motor de reglas comerciales
    │   ├── charts.py               # Graficos Plotly reutilizables
    │   ├── data_loader.py          # Carga de datos con caching
    │   └── pipeline.py             # Pipeline de limpieza y FE
    └── data/                       # Modelo y datos serializados
        ├── modelo_churn.pkl
        ├── columnas_modelo.pkl
        ├── threshold.pkl
        ├── shap_values.pkl
        ├── model_metrics.pkl
        └── estrategia_comercial.csv
```

## Dashboard

El dashboard Streamlit incluye 6 pestanas:

- **Resumen** — KPIs globales, distribucion de riesgo, churn por modelo
- **Explorador** — Busqueda de clientes, ficha individual con gauge de probabilidad, SHAP waterfall y simulador What-if con 11 variables
- **Estrategia** — Distribucion de acciones comerciales, ROI por accion, CLTV por modelo, comparador de escenarios A/B
- **Sensibilidad** — Analisis de threshold y ajuste interactivo de descuentos con visualizacion de impacto
- **Piloto Auto** — Pipeline completo: subir CSV, predecir, aplicar reglas de negocio, exportar Excel
- **Modelo** — Curvas ROC y Precision-Recall, matriz de confusion, feature importance, configuracion tecnica

## Estrategia Comercial

Cuatro niveles de accion segun riesgo y valor del cliente:

| Accion | Descuento | Aplicacion |
|--------|-----------|------------|
| Retencion Premium | 20% | Alto riesgo + alto valor (CLTV) |
| Retencion Estandar | 15% | Alto riesgo + bajo valor |
| Fidelizacion Activa | 10% | Riesgo medio |
| Mantenimiento Preventivo | 5% | Riesgo bajo |

Restriccion: margen neto minimo del 37% (30% concesionario + 7% marca).

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/churn-prediction-automotive.git
cd churn-prediction-automotive

# Instalar dependencias
pip install pandas numpy scikit-learn plotly streamlit shap openpyxl

# Ejecutar el dashboard
cd streamlit_app
streamlit run app.py
```

## Metodologia

El proyecto sigue la metodologia **Sandbox / Staging**:

1. **Sandbox** — Desarrollo del modelo sobre datos historicos (`bqresults.csv`)
   - Limpieza y validacion de calidad
   - Analisis exploratorio (EDA)
   - Feature Engineering (64 features)
   - Entrenamiento e iteracion (Random Forest)
   - Evaluacion en test set

2. **Staging** — Validacion en produccion (`nuevos_clientes.csv`)
   - Aplicacion del pipeline completo
   - Generacion de predicciones
   - Asignacion de acciones comerciales
   - Calculo de ROI y CLTV

## Tecnologias

- **Python** — pandas, numpy, scikit-learn, SHAP
- **Streamlit** — Dashboard interactivo
- **Plotly** — Visualizaciones
- **Random Forest** — Modelo de clasificacion

## Contexto

Caso practico de Machine Learning para el grado en Ingeniería Matemática en la UAX,2026
