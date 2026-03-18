# Churn Prediction — Automotive Sector

> End-to-end Machine Learning system to predict customer churn in an official car dealership, including a commercial retention strategy and an interactive dashboard deployed in production.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://churn-prediction-automotive-jhxywrrmnkg5nfba3vxsxk.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-orange?logo=scikit-learn&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.52-red?logo=streamlit&logoColor=white)

---

## Overview

A customer is defined as **churned** if they have not visited the official dealership workshop in over **400 days**. The system predicts this probability for each client and automatically assigns a cost-effective retention action.

**Key results:**
- 71% of churning customers correctly identified (Recall)
- ROI of ~2.2x on the 10,000-client staging portfolio
- €547K investment protecting €4.9M in Revenue at Risk

---

## Live Demo

**[→ Open Dashboard](https://churn-prediction-automotive-jhxywrrmnkg5nfba3vxsxk.streamlit.app/)**

---

## Model Performance

| Metric | Value |
|--------|-------|
| AUC-ROC | 0.789 |
| AUC-PR | 0.355 |
| Recall (Churn) | 71.0% |
| Precision (Churn) | 34.2% |
| F1-Score | 0.46 |
| Algorithm | Random Forest |
| Trees | 300 (`max_depth=15`) |
| Features | 64 engineered variables |
| Threshold | 0.498 (F1-optimised) |
| Class balancing | `class_weight='balanced'` |

> **Note on precision/recall trade-off:** a 34% precision is acceptable in this business context — the cost of contacting a client who was not going to churn is low compared to the cost of losing one.

---

## Commercial Strategy

Each client receives an automatic action based on their risk level and Customer Lifetime Value (CLTV):

| Action | Discount | Contact Cost | Conversion Rate | Clients |
|--------|----------|--------------|-----------------|---------|
| Premium Retention | 30% × C(n) | €50 | 42% | 204 |
| Standard Retention | 22% × C(n) | €35 | 40% | 1,495 |
| Active Loyalty | 15% × C(n) | €20 | 38% | 2,060 |
| Preventive Maintenance | 8% × C(n) | €10 | 50% | 6,241 |

**C(n)** = maintenance cost at revision *n*, capitalised at α = 7% (premium models A/B) or 10% (rest).
**Constraint:** minimum net margin of 37% enforced on every action.

**Adjusted ROI formula:**

$$ROI_{adj} = \frac{\text{Net margin} \times \text{Conversion rate}}{\text{Action investment}}$$

---

## Dashboard — 6 Tabs

| Tab | Description |
|-----|-------------|
| **Summary** | Global KPIs, risk distribution, revenue at risk, churn by model |
| **Client Explorer** | Individual client card with churn gauge, SHAP waterfall and 11-variable What-If simulator |
| **Strategy** | Action distribution, ROI by action, CLTV by model, A/B threshold comparator |
| **Sensitivity** | Threshold sensitivity analysis and interactive discount adjustment |
| **Auto Pilot** | Full pipeline: upload a CSV → predict → apply business rules → export Excel report |
| **Model** | ROC & Precision-Recall curves, confusion matrix, feature importance, technical config |

---

## Project Structure

```
├── requirements.txt
├── streamlit_app/
│   ├── app.py                      # Entry point
│   ├── assets/style.css            # Custom dark theme (glassmorphism)
│   ├── pages/
│   │   ├── p1_resumen.py           # Summary & KPIs
│   │   ├── p2_explorador.py        # Client explorer + SHAP + What-If
│   │   ├── p3_estrategia.py        # Commercial strategy
│   │   ├── p4_sensibilidad.py      # Threshold & discount sensitivity
│   │   ├── p5_piloto.py            # Automated pipeline (CSV upload)
│   │   └── p6_modelo.py            # Model metrics & explainability
│   ├── utils/
│   │   ├── business_rules.py       # Commercial rules engine + CLTV
│   │   ├── charts.py               # Reusable Plotly charts
│   │   ├── data_loader.py          # Cached data loading
│   │   └── pipeline.py             # Cleaning & feature engineering pipeline
│   └── data/
│       ├── modelo_churn.pkl        # Trained Random Forest
│       ├── estrategia_comercial.csv
│       ├── shap_values.pkl
│       ├── model_metrics.pkl
│       └── ...
```

---

## Methodology

```
SANDBOX  →  Validate → EDA → Feature Engineering → Train → Test → Winner
STAGING  →  Fresh data → Pipeline → Predict → Business rules → ROI
```

**Sandbox** (development): trained on `bqresults.csv` — 58,049 transactions, 44,053 unique clients, 8.8% churn rate.
**Staging** (production): applied to `nuevos_clientes.csv` — 10,000 new clients with no churn label.

Key decisions:
- **Leakage removal:** `DAYS_LAST_SERVICE` excluded (directly defines the target).
- **Population filter:** model trained on clients with ≥1 workshop visit (churn rate rises to 16.4%).
- **Revision variables excluded** from features to ensure generalisation to staging clients (all have 0 visits).

---

## Installation

```bash
git clone https://github.com/PabloJimenezGirardeau/churn-prediction-automotive.git
cd churn-prediction-automotive
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data processing | pandas, NumPy |
| Machine Learning | scikit-learn (Random Forest) |
| Explainability | SHAP (TreeExplainer) |
| Visualisation | Plotly, Matplotlib, Seaborn |
| Dashboard | Streamlit |
| Serialisation | pickle, openpyxl |

---

## Context

Academic project — Machine Learning course, Universidad Alfonso X el Sabio (UAX), 2026.
