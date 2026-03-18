ya# CLAUDE.md — Contexto del Proyecto

## Proyecto
Predicción de Fuga de Clientes (Churn) en el sector de automoción + diseño de estrategia comercial rentable.

## Objetivo
Construir un modelo de Machine Learning que prediga la probabilidad de churn de cada cliente de un concesionario oficial, y diseñar una acción comercial rentable basada en esas predicciones.

## Definición de Churn
Variable binaria `Churn_400`: un cliente tiene Churn=Y si lleva más de 400 días sin registrar una revisión técnica en el taller oficial. La lógica SQL es:
```sql
CASE
  WHEN DIAS_DESDE_ULTIMA_REVISION > 400 THEN 'Y'
  WHEN DIAS_DESDE_ULTIMA_REVISION IS NULL
    AND DATE_DIFF(Sales_Date, BASE_DATE) > 400 THEN 'Y'
  ELSE 'N'
END
```

## Datasets

### bqresults.csv (58.049 filas × 40 columnas)
Dataset principal para el SANDBOX. Contiene la variable objetivo `Churn_400`.

### nuevos_clientes.csv (10.000 filas × 38 columnas)
Datos frescos para STAGING. **No contiene** `Churn_400`. Se usa para validar el modelo en producción.

### Costes.csv (11 filas × 7 columnas)
Tabla auxiliar con parámetros económicos por modelo:
- Modelos: A, B, C, D, E, F, G, H, I, J, K
- Columnas: Modelo, Margen, Costetransporte, Margendistribuidor, GastosMarketing, Mantenimiento_medio, Comisión_Marca
- Modelos premium (A, B): α = 7% en capitalización de mantenimiento
- Resto de modelos: α = 10%
- Modelos J y K: margen 5% (100% de operaciones con margen neto negativo)

### Diferencias entre datasets
- En bqresults pero no en nuevos_clientes: `DAYS_LAST_SERVICE`, `Churn_400`, `Fue_Lead`
- En nuevos_clientes pero no en bqresults: `Lead_compra_1`

## Metodología: Sandbox / Staging

### SANDBOX (Desarrollo)
```
DATOS → VALIDAR → EDA → FE → TRAIN/ITERAR → TEST → WINNER
```

### STAGING (Producción)
```
EXPORTAR → DATOS FRESH → VALID. VS TEST → (si pasa) → PROD → BUSINESS
```

## Estado actual del proyecto

### ✅ Completado

#### Fase 1a — Carga de Datos
- Dataset cargado y explorado
- 44.053 clientes únicos en 58.049 transacciones (clientes con compras múltiples)
- Variable objetivo desbalanceada: 91,2% No Churn vs 8,8% Churn (ratio ~10:1)

#### Fase 1b — Validación de Calidad
- **Nulos tratados:**
  - QUEJA (33.323 nulos → "SIN_REGISTRO")
  - STATUS_SOCIAL (12.816 nulos → "DESCONOCIDO")
  - GENERO (849 nulos → "DESCONOCIDO")
- **Typo corregido:** EXTENSION_GARANTIA "SI, Campa a Regalo" → "SI, Campaña Regalo" (53 registros)
- **Leakage identificado y excluido:** `DAYS_LAST_SERVICE` (correlación 0.55 con Churn, es la variable que define el target)
- **Consistencias verificadas:** EN_GARANTIA vs fechas, km vs revisiones, modelos vs Costes.csv — todo OK
- **Outliers:** No requieren tratamiento (valores extremos son coherentes con negocio)

#### Fase 2 — EDA
- 10 visualizaciones generadas
- **Variables más discriminantes identificadas:** Revisiones, Modelo, EN_GARANTIA, QUEJA, FORMA_PAGO, Fuel, Antigüedad
- **Hallazgos clave:**
  - Pico de churn en la 2ª revisión (22,1%)
  - Modelo H ≈ 0% churn; modelos C y A > 13%
  - EN_GARANTIA=NO → ~15% churn
  - QUEJA=SI → mayor churn
  - Contado > Financiación en churn
  - 27.070 registros con 0 revisiones y 0% churn (anomalía)
  - Multicolinealidad: PVP ↔ Kw ↔ Margen_eur_bruto
  - Relación no lineal antigüedad-churn → favorece modelos de árboles

### 🔲 Pendiente

#### Fase 3 — Feature Engineering
Decisiones a tomar:
1. **Nivel de análisis:** ¿Transacción (CODE) o Cliente (Customer_ID)?
2. **Registros con 0 revisiones (27.070):** ¿Incluir, excluir, o tratar aparte?
3. **Variables a excluir del modelo:** CODE, Id_Producto, Customer_ID, DAYS_LAST_SERVICE (ya excluida), Sales_Date (string), FIN_GARANTIA (string), BASE_DATE
4. **Variables redundantes:** TRANSMISION_ID ≈ Fuel, TIPO_CARROCERIA ≈ Modelo, PROV_DESC ≈ ZONA
5. **Features a crear:**
   - Antigüedad del vehículo (días desde Sales_Date hasta BASE_DATE)
   - Días hasta fin de garantía
   - Margen porcentual (Margen_eur / PVP)
   - Ratio revisiones / antigüedad
   - Indicador de mantenimiento gratuito pendiente
   - Variable binaria TIENE_DATOS_DEMO (renta=0 y encuesta=0)
6. **Codificación de categóricas:** One-hot, label encoding, o target encoding según variable
7. **Escalado** si el modelo lo requiere

#### Fase 4 — Train + Iterar
- Separación train/validation/test
- Algoritmos a probar: Logistic Regression, Random Forest, XGBoost/LightGBM
- Balanceo: SMOTE, class_weight, undersampling
- Métricas: AUC-ROC, Precision, Recall, F1, curva Precision-Recall
- Feature importance + SHAP values

#### Fase 5 — Test + Winner
- Evaluación final en test set
- Umbral óptimo de decisión (basado en costes de negocio)
- Documentación del modelo ganador

#### Fase 6 — Staging
- Aplicar pipeline a nuevos_clientes.csv
- Data drift check
- Generar predicciones

#### Fase 7 — Business (Estrategia Comercial)
- Fórmula de coste de mantenimiento: C(n) = BASE · (1 + α)^n
  - α = 7% para modelos A y B (premium)
  - α = 10% para el resto
- Costes de marketing: 1% del coste de mantenimiento
- Descuento fijo de 1.000€ para renovación si n ≥ 5 revisiones
- Margen neto del concesionario debe superar el 30%
- 7% del ingreso bruto va a la marca
- Cálculo de CLTV (opcional pero recomendado)

## Pipeline de limpieza (aplicar siempre al cargar datos)
```python
def limpiar_datos(df):
    """Pipeline de limpieza reproducible."""
    df = df.copy()
    df['QUEJA'] = df['QUEJA'].fillna('SIN_REGISTRO')
    df['STATUS_SOCIAL'] = df['STATUS_SOCIAL'].fillna('DESCONOCIDO')
    df['GENERO'] = df['GENERO'].fillna('DESCONOCIDO')
    df['EXTENSION_GARANTIA'] = df['EXTENSION_GARANTIA'].replace(
        'SI, Campa a Regalo', 'SI, Campaña Regalo')
    if 'DAYS_LAST_SERVICE' in df.columns:
        df = df.drop(columns=['DAYS_LAST_SERVICE'])
    if 'Churn_400' in df.columns:
        df['Churn'] = (df['Churn_400'] == 'Y').astype(int)
    return df
```

## Archivos del proyecto
```
├── CLAUDE.md                              ← Este archivo
├── metadada.md                            ← Enunciado y metadata del caso práctico
├── bqresults.csv                          ← Dataset principal (Sandbox)
├── nuevos_clientes.csv                    ← Dataset staging
├── Costes.csv                             ← Costes por modelo
├── Sandbox_Staging.pdf                    ← Diagrama de metodología
├── Churn_Prediction_Automocion.ipynb      ← Notebook principal (en progreso)
├── 01_Carga_y_Validacion_Datos.pdf        ← Informe Fase 1a
├── 02_Validacion_Calidad_Datos.pdf        ← Informe Fase 1b
└── 03_Analisis_Exploratorio_EDA.pdf       ← Informe Fase 2
```

## Notas técnicas
- Python 3.11+, pandas, numpy, matplotlib, seaborn, scikit-learn, xgboost/lightgbm
- El notebook debe ser autocontenido y presentable (con gráficas y celdas markdown explicativas)
- Los PDFs son informes complementarios con estilo LaTeX (Times, booktabs)
- El proyecto se expondrá ante un tribunal
