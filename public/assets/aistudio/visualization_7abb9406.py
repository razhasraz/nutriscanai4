from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_macro_donut_chart(analysis: dict[str, Any], dark_mode: bool = False) -> go.Figure:
    """Donut chart showing Protein, Carbohydrates, and Fat energy distribution."""
    macro_pct = analysis.get("macro_energy_pct", {})
    totals = analysis.get("totals", {})

    labels = ["Protein", "Carbohydrates", "Fat"]
    values = [
        macro_pct.get("protein_pct", 0.0),
        macro_pct.get("carbs_pct", 0.0),
        macro_pct.get("fat_pct", 0.0),
    ]
    grams = [
        totals.get("total_protein_g", 0.0),
        totals.get("total_carbs_g", 0.0),
        totals.get("total_fat_g", 0.0),
    ]

    if sum(values) == 0:
        values = [1, 1, 1]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=["#10B981", "#3B82F6", "#F59E0B"]),
                textinfo="label+percent",
                hovertemplate="%{label}: %{value:.1f}% of energy<br>%{customdata:.1f} g<extra></extra>",
                customdata=grams,
            )
        ]
    )

    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    fig.update_layout(
        title=dict(text="Macronutrient Energy Split (%)", font=dict(size=16, color=text_color)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color),
        margin=dict(t=48, b=16, l=16, r=16),
        height=340,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
    )
    return fig


def create_food_contribution_chart(analysis: dict[str, Any], dark_mode: bool = False) -> go.Figure:
    """Horizontal bar chart comparing calorie contributions of each detected food."""
    items = analysis.get("items", [])
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    grid_color = "rgba(148,163,184,0.2)"

    if not items:
        fig = go.Figure()
        fig.update_layout(
            title="Calorie Contribution by Food Item",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
        )
        return fig

    df = pd.DataFrame(items)
    df = df.sort_values("calories", ascending=True)

    fig = px.bar(
        df,
        x="calories",
        y="food_name",
        orientation="h",
        color="category",
        color_discrete_map={"Indian": "#10B981", "International": "#3B82F6"},
        text="calories",
        labels={"calories": "Calories (kcal)", "food_name": "Food Item", "category": "Cuisine"},
        hover_data=["grams", "protein_g", "carbs_g", "fat_g", "fibre_g"],
    )
    fig.update_traces(texttemplate="%{text:.0f} kcal", textposition="outside")
    fig.update_layout(
        title=dict(text="Individual Food Calorie Contributions", font=dict(size=16, color=text_color)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color),
        xaxis=dict(gridcolor=grid_color),
        yaxis=dict(title=""),
        margin=dict(t=48, b=24, l=16, r=48),
        height=340,
    )
    return fig


def create_macro_grams_bar_chart(analysis: dict[str, Any], dark_mode: bool = False) -> go.Figure:
    """Grouped bar chart showing protein, carbs, fat, and fibre per item."""
    items = analysis.get("items", [])
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    grid_color = "rgba(148,163,184,0.2)"

    if not items:
        return go.Figure()

    df = pd.DataFrame(items)
    melted = df.melt(
        id_vars=["food_name"],
        value_vars=["protein_g", "carbs_g", "fat_g", "fibre_g"],
        var_name="Nutrient",
        value_name="Grams",
    )
    label_map = {
        "protein_g": "Protein (g)",
        "carbs_g": "Carbs (g)",
        "fat_g": "Fat (g)",
        "fibre_g": "Fibre (g)",
    }
    melted["Nutrient"] = melted["Nutrient"].map(label_map)

    fig = px.bar(
        melted,
        x="food_name",
        y="Grams",
        color="Nutrient",
        barmode="group",
        color_discrete_map={
            "Protein (g)": "#10B981",
            "Carbs (g)": "#3B82F6",
            "Fat (g)": "#F59E0B",
            "Fibre (g)": "#8B5CF6",
        },
    )
    fig.update_layout(
        title=dict(text="Nutrient Breakdown per Food (g)", font=dict(size=16, color=text_color)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color),
        xaxis=dict(title="", gridcolor=grid_color),
        yaxis=dict(title="Grams (g)", gridcolor=grid_color),
        margin=dict(t=48, b=24, l=16, r=16),
        height=340,
    )
    return fig
