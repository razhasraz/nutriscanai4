from __future__ import annotations

from typing import Any

from modules.meal_intelligence import analyze_meal_intelligence


def generate_meal_insights(analysis: dict[str, Any]) -> list[dict[str, str]]:
    """
    Preserved public API returning general educational observations about
    macronutrient balance and dietary variety without medical claims.
    """
    totals = analysis.get("totals", {})
    macro_pct = analysis.get("macro_energy_pct", {})
    items = [i for i in analysis.get("items", []) if i.get("in_database", True)]

    if not items or totals.get("total_calories", 0) <= 0:
        return [
            {
                "type": "info",
                "title": "No Meal Data Yet",
                "message": "Scan and confirm at least one food item to view meal balance insights.",
            }
        ]

    insights: list[dict[str, str]] = []
    protein_g = totals["total_protein_g"]
    fibre_g = totals["total_fibre_g"]
    protein_pct = macro_pct.get("protein_pct", 0.0)
    carbs_pct = macro_pct.get("carbs_pct", 0.0)
    fat_pct = macro_pct.get("fat_pct", 0.0)

    if protein_pct < 15.0:
        insights.append(
            {
                "type": "tip",
                "title": "Protein Variety Opportunity",
                "message": (
                    f"Protein provides ~{protein_pct:.0f}% ({protein_g:.1f} g) of this meal's estimated energy. "
                    "Pairing grain-based dishes with dal, rajma, chole, paneer, yogurt, eggs, or fish "
                    "can add plant or dairy protein diversity."
                ),
            }
        )
    else:
        insights.append(
            {
                "type": "positive",
                "title": "Notable Protein Contribution",
                "message": (
                    f"Protein accounts for ~{protein_pct:.0f}% ({protein_g:.1f} g) of this meal's estimated energy."
                ),
            }
        )

    if fibre_g < 5.0:
        insights.append(
            {
                "type": "tip",
                "title": "Dietary Fibre Awareness",
                "message": (
                    f"Estimated fibre is {fibre_g:.1f} g. Exploring vegetables, sabzi, salad, legumes, "
                    "whole fruit, or whole-wheat flatbreads can expand dietary fibre."
                ),
            }
        )
    else:
        insights.append(
            {
                "type": "positive",
                "title": "Meaningful Dietary Fibre",
                "message": (
                    f"This meal provides an estimated {fibre_g:.1f} g of dietary fibre across the confirmed items."
                ),
            }
        )

    if carbs_pct > 65.0:
        insights.append(
            {
                "type": "info",
                "title": "Carbohydrate-Forward Composition",
                "message": (
                    f"Carbohydrates supply ~{carbs_pct:.0f}% of estimated energy. "
                    "Including non-starchy vegetables or a protein side can diversify meal composition."
                ),
            }
        )

    if fat_pct > 38.0:
        insights.append(
            {
                "type": "info",
                "title": "Higher Fat Energy Share",
                "message": (
                    f"Fats contribute ~{fat_pct:.0f}% of estimated energy. Cooking oil, tadka, ghee, "
                    "and dressings can shift actual meal fat content."
                ),
            }
        )

    intelligence = analyze_meal_intelligence(analysis)
    missing_groups = intelligence["food_group_variety"]["unrepresented"]
    if missing_groups:
        insights.append(
            {
                "type": "info",
                "title": "Food-Group Variety",
                "message": (
                    f"Food groups not represented in this single plate include: "
                    f"{', '.join(missing_groups[:3])}."
                ),
            }
        )

    return insights
