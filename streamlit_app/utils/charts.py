"""Funciones de graficos Plotly reutilizables."""

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Paleta global
C_GREEN = "#2ecc71"
C_RED = "#e74c3c"
C_BLUE = "#3498db"
C_ORANGE = "#f39c12"
C_PURPLE = "#9b59b6"

RIESGO_COLORS = {"Bajo": C_GREEN, "Medio": C_ORANGE, "Alto": C_RED}
RIESGO_ORDER = ["Bajo", "Medio", "Alto"]

# Layout base para todos los graficos (tema oscuro)
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#c0c0c0", size=12),
    title_font=dict(size=15, color="#e0e0e0"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
    hoverlabel=dict(bgcolor="#1e2a3a", font_size=12, font_color="#e0e0e0"),
    margin=dict(t=50, b=40, l=20, r=20),
)


def apply_theme(fig):
    """Aplica tema oscuro consistente a un grafico Plotly."""
    fig.update_layout(**LAYOUT_BASE)
    return fig


def donut_riesgo(df):
    """Donut chart de distribucion por segmento de riesgo."""
    counts = df["Riesgo"].value_counts()
    counts = counts.reindex(RIESGO_ORDER).dropna()

    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.6,
        marker=dict(
            colors=[RIESGO_COLORS[r] for r in counts.index],
            line=dict(color="#0e1117", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=13, color="#e0e0e0"),
        hovertemplate="%{label}: %{value:,} clientes (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title_text="Distribucion por Riesgo",
        title_x=0.5,
        showlegend=False,
        height=350,
    )
    return apply_theme(fig)


def bar_churn_modelo(df):
    """Barras horizontales de probabilidad media de churn por modelo."""
    churn_mod = df.groupby("Modelo")["Prob_Churn"].mean().sort_values()
    media = df["Prob_Churn"].mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=churn_mod.index,
        x=churn_mod.values * 100,
        orientation="h",
        marker=dict(
            color=[C_RED if v > media else C_BLUE for v in churn_mod.values],
            line=dict(width=0),
        ),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=media * 100, line_dash="dash", line_color="#556677",
                  annotation_text=f"Media: {media:.1%}",
                  annotation_font_color="#8899aa")
    fig.update_layout(
        title_text="Prob. Churn por Modelo",
        title_x=0.5,
        xaxis_title="Prob. Churn media (%)",
        height=350,
    )
    return apply_theme(fig)


def hist_probabilidades(df, threshold):
    """Histograma de distribucion de probabilidades con threshold."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["Prob_Churn"],
        nbinsx=40,
        marker=dict(color=C_BLUE, line=dict(color="#0e1117", width=1)),
        opacity=0.8,
        hovertemplate="Prob: %{x:.2f}<br>Clientes: %{y}<extra></extra>",
    ))
    fig.add_vline(x=threshold, line_dash="dot", line_color="#e0e0e0", line_width=2,
                  annotation_text=f"Threshold: {threshold:.3f}",
                  annotation_font_color="#e0e0e0")
    fig.update_layout(
        title_text="Distribucion de Probabilidades",
        title_x=0.5,
        xaxis_title="Probabilidad de Churn",
        yaxis_title="Frecuencia",
        height=350,
        xaxis=dict(range=[0, 1]),
    )
    return apply_theme(fig)


def bar_acciones(df, accion_order, accion_colors):
    """Barras horizontales de distribucion de acciones."""
    counts = df["Accion"].value_counts()
    acciones = [a for a in accion_order if a in counts.index]
    vals = [counts[a] for a in acciones]
    colors = [accion_colors[a] for a in acciones]

    fig = go.Figure(go.Bar(
        y=acciones,
        x=vals,
        orientation="h",
        marker=dict(color=colors, line=dict(color="#0e1117", width=1)),
        text=[f"{v:,} ({v/len(df):.1%})" for v in vals],
        textposition="outside",
        textfont=dict(color="#c0c0c0"),
        hovertemplate="%{y}: %{x:,} clientes<extra></extra>",
    ))
    fig.update_layout(
        title_text="Distribucion de Acciones",
        title_x=0.5,
        height=300,
        xaxis_title="Clientes",
        margin=dict(t=50, b=20, l=20, r=100),
    )
    return apply_theme(fig)


def bar_roi_accion(df, accion_order, accion_colors):
    """Barras de ROI medio por accion."""
    rows = []
    for acc in accion_order:
        sub = df[df["Accion"] == acc]
        if len(sub) == 0:
            continue
        rows.append({
            "Accion": acc,
            "ROI": float((sub["Margen_neto"] * sub["Conversion_rate"]).sum() / sub["Inversion_accion"].sum()),
            "Margen_neto_medio": float(sub["Margen_neto"].mean()),
            "Inversion_media": float(sub["Inversion_accion"].mean()),
        })
    roi_df = pd.DataFrame(rows)

    fig = go.Figure(go.Bar(
        y=roi_df["Accion"],
        x=roi_df["ROI"],
        orientation="h",
        marker=dict(
            color=[accion_colors[a] for a in roi_df["Accion"]],
            line=dict(color="#0e1117", width=1),
        ),
        text=[f"{r:.1f}x" for r in roi_df["ROI"]],
        textposition="outside",
        textfont=dict(color="#c0c0c0"),
        hovertemplate="%{y}<br>ROI: %{x:.1f}x<br>Margen: %{customdata[0]:,.0f}€<br>Inv: %{customdata[1]:,.0f}€<extra></extra>",
        customdata=roi_df[["Margen_neto_medio", "Inversion_media"]].values,
    ))
    fig.update_layout(
        title_text="ROI por Accion",
        title_x=0.5,
        xaxis_title="ROI ajustado por conversion",
        height=300,
        margin=dict(t=50, b=40, l=20, r=60),
    )
    return apply_theme(fig)


def bar_cltv_modelo(df):
    """Barras horizontales de CLTV medio por modelo."""
    cltv_mod = df.groupby("Modelo")["CLTV"].mean().sort_values()
    mediana = df["CLTV"].median()

    fig = go.Figure(go.Bar(
        y=cltv_mod.index,
        x=cltv_mod.values,
        orientation="h",
        marker=dict(color=C_GREEN, line=dict(color="#0e1117", width=1)),
        text=[f"{v:,.0f}€" for v in cltv_mod.values],
        textposition="outside",
        textfont=dict(color="#c0c0c0"),
        hovertemplate="%{y}: %{x:,.0f}€<extra></extra>",
    ))
    fig.add_vline(x=mediana, line_dash="dash", line_color="#556677",
                  annotation_text=f"Mediana: {mediana:,.0f}€",
                  annotation_font_color="#8899aa")
    fig.update_layout(
        title_text="CLTV por Modelo",
        title_x=0.5,
        xaxis_title="CLTV medio (EUR)",
        height=350,
        margin=dict(t=50, b=40, l=20, r=80),
    )
    return apply_theme(fig)


def sensitivity_chart(thresholds, data):
    """Grafico de sensibilidad: clientes alto riesgo + revenue capturado."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[str(t) for t in thresholds],
        y=data["n_alto"],
        name="Clientes alto riesgo",
        marker=dict(color=C_BLUE, opacity=0.8, line=dict(color="#0e1117", width=1)),
    ))

    fig.add_trace(go.Scatter(
        x=[str(t) for t in thresholds],
        y=data["pct_rar"],
        name="% Revenue at Risk capturado",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=C_RED, width=3),
        marker=dict(size=10, color=C_RED),
    ))

    fig.update_layout(
        title_text="Sensibilidad del Threshold",
        title_x=0.5,
        xaxis_title="Threshold",
        yaxis=dict(title="Clientes alto riesgo", side="left", color=C_BLUE),
        yaxis2=dict(title="% Revenue at Risk capturado", side="right",
                    overlaying="y", color=C_RED,
                    tickformat=".0%", gridcolor="rgba(0,0,0,0)"),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font_color="#c0c0c0"),
    )
    return apply_theme(fig)
