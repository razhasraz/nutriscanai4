from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Soft-green botanical palette for Plotly charts
FOREST_GREEN = "#294C38"
PRIMARY_GREEN = "#527B60"
MUTED_SAGE = "#A8BCA6"
SOFT_MINT = "#DCEBDD"
WARM_OCHRE = "#C4955A"
DEEP_CLAY = "#8E7A66"
TEXT_PRIMARY = "#25352B"
TEXT_SECONDARY = "#758276"
GRID_LIGHT = "rgba(82, 123, 96, 0.12)"


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
        fig = go.Figure()
        fig.update_layout(
            title="Macronutrient Energy Split (%)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=330,
        )
        return fig

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(
                    colors=[FOREST_GREEN, PRIMARY_GREEN, WARM_OCHRE],
                    line=dict(color="#FFFFFF", width=2),
                ),
                textinfo="label+percent",
                hovertemplate="%{label}: %{value:.1f}% of energy<br>%{customdata:.1f} g<extra></extra>",
                customdata=grams,
            )
        ]
    )

    text_color = "#F3F7F0" if dark_mode else TEXT_PRIMARY
    fig.update_layout(
        title=dict(
            text="Macronutrient Energy Split (%)",
            font=dict(size=15, family="Manrope, DM Sans, sans-serif", color=text_color),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=text_color),
        margin=dict(t=48, b=24, l=12, r=12),
        height=330,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
    )
    return fig


def create_food_contribution_chart(analysis: dict[str, Any], dark_mode: bool = False) -> go.Figure:
    """Horizontal bar chart comparing calorie contributions of each confirmed food."""
    items = [i for i in analysis.get("items", []) if i.get("in_database", True)]
    text_color = "#F3F7F0" if dark_mode else TEXT_PRIMARY

    if not items:
        fig = go.Figure()
        fig.update_layout(
            title="Calorie Contribution by Food Item",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=330,
        )
        return fig

    df = pd.DataFrame(items).sort_values("calories", ascending=True)

    fig = px.bar(
        df,
        x="calories",
        y="food_name",
        orientation="h",
        color="category",
        color_discrete_map={"Indian": PRIMARY_GREEN, "International": MUTED_SAGE},
        text="calories",
        labels={"calories": "Calories (kcal)", "food_name": "Food Item", "category": "Cuisine"},
        hover_data=["grams", "protein_g", "carbs_g", "fat_g", "fibre_g"],
    )
    fig.update_traces(texttemplate="%{text:.0f} kcal", textposition="outside")
    fig.update_layout(
        title=dict(
            text="Calorie Contribution by Food Item",
            font=dict(size=15, family="Manrope, DM Sans, sans-serif", color=text_color),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=text_color),
        xaxis=dict(gridcolor=GRID_LIGHT, zeroline=False),
        yaxis=dict(title=""),
        margin=dict(t=48, b=24, l=12, r=52),
        height=330,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
    )
    return fig


def create_macro_grams_bar_chart(analysis: dict[str, Any], dark_mode: bool = False) -> go.Figure:
    """Grouped bar chart showing protein, carbs, fat, and fibre per item."""
    items = [i for i in analysis.get("items", []) if i.get("in_database", True)]
    text_color = "#F3F7F0" if dark_mode else TEXT_PRIMARY

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
            "Protein (g)": FOREST_GREEN,
            "Carbs (g)": PRIMARY_GREEN,
            "Fat (g)": WARM_OCHRE,
            "Fibre (g)": MUTED_SAGE,
        },
    )
    fig.update_layout(
        title=dict(
            text="Macronutrient Breakdown per Food (g)",
            font=dict(size=15, family="Manrope, DM Sans, sans-serif", color=text_color),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=text_color),
        xaxis=dict(title="", gridcolor=GRID_LIGHT),
        yaxis=dict(title="Grams (g)", gridcolor=GRID_LIGHT),
        margin=dict(t=48, b=24, l=12, r=12),
        height=330,
        legend=dict(orientation="h", yanchor="bottom", y=-0.24, xanchor="center", x=0.5),
    )
    return fig


def create_history_trend_chart(timeline_df: pd.DataFrame) -> go.Figure:
    """Line chart tracking recorded nutrient totals over meal history."""
    fig = go.Figure()
    x_labels = timeline_df["timestamp"].astype(str).str.slice(0, 16)

    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=timeline_df["total_protein_g"],
            mode="lines+markers",
            name="Protein (g)",
            line=dict(color=FOREST_GREEN, width=2.5),
            marker=dict(size=7),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=timeline_df["total_carbs_g"],
            mode="lines+markers",
            name="Carbs (g)",
            line=dict(color=PRIMARY_GREEN, width=2.5),
            marker=dict(size=7),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=timeline_df["total_fat_g"],
            mode="lines+markers",
            name="Fat (g)",
            line=dict(color=WARM_OCHRE, width=2.2),
            marker=dict(size=6),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=timeline_df["total_fibre_g"],
            mode="lines+markers",
            name="Fibre (g)",
            line=dict(color=MUTED_SAGE, width=2.2, dash="dot"),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title=dict(
            text="Recorded Nutrient Contributions Over Time",
            font=dict(size=15, family="Manrope, DM Sans, sans-serif", color=TEXT_PRIMARY),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=TEXT_PRIMARY),
        xaxis=dict(title="", gridcolor=GRID_LIGHT),
        yaxis=dict(title="Grams (g)", gridcolor=GRID_LIGHT),
        margin=dict(t=48, b=24, l=12, r=12),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.24, xanchor="center", x=0.5),
    )
    return fig


def create_top_foods_chart(top_foods: list[dict[str, Any]]) -> go.Figure:
    """Horizontal bar chart of most frequently analysed food items in history."""
    df = pd.DataFrame(top_foods).sort_values("count", ascending=True)
    fig = px.bar(
        df,
        x="count",
        y="food_name",
        orientation="h",
        text="count",
        color_discrete_sequence=[PRIMARY_GREEN],
        labels={"count": "Meals Recorded", "food_name": "Food Item"},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title=dict(
            text="Most Frequently Analysed Foods",
            font=dict(size=15, family="Manrope, DM Sans, sans-serif", color=TEXT_PRIMARY),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=TEXT_PRIMARY),
        xaxis=dict(gridcolor=GRID_LIGHT, dtick=1),
        yaxis=dict(title=""),
        margin=dict(t=48, b=24, l=12, r=36),
        height=320,
    )
    return fig
