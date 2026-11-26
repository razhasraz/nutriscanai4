from __future__ import annotations

from typing import Any


def generate_meal_insights(analysis: dict[str, Any]) -> list[dict[str, str]]:
    """
    Returns general educational observations about macronutrient balance and fibre.
    """
    totals = analysis.get("totals", {})
    macro_pct = analysis.get("macro_energy_pct", {})
    items = analysis.get("items", [])

    if not items or totals.get("total_calories", 0) <= 0:
        return [
            {
                "type": "info",
                "title": "No Meal Data Yet",
                "message": "Scan and confirm at least one food item to view meal balance insights.",
            }
        ]

    insights: list[dict[str, str]] = []
    calories = totals["total_calories"]
    protein_g = totals["total_protein_g"]
    fibre_g = totals["total_fibre_g"]
    protein_pct = macro_pct.get("protein_pct", 0.0)
    carbs_pct = macro_pct.get("carbs_pct", 0.0)
    fat_pct = macro_pct.get("fat_pct", 0.0)

    # Protein balance
    if protein_pct < 15.0:
        insights.append(
            {
                "type": "tip",
                "title": "Protein Contribution Is Modest",
                "message": (
                    f"Protein provides ~{protein_pct:.0f}% ({protein_g:.1f}g) of this meal's energy. "
                    "General dietary guidelines often suggest pairing carbohydrate-rich items with "
                    "protein sources such as dal, paneer, yogurt, eggs, grilled chicken, or fish."
                ),
            }
        )
    else:
        insights.append(
            {
                "type": "positive",
                "title": "Solid Protein Presence",
                "message": (
                    f"Protein accounts for ~{protein_pct:.0f}% ({protein_g:.1f}g) of this meal's energy, "
                    "supporting balanced satiety."
                ),
            }
        )

    # Fibre observation
    if fibre_g < 5.0:
        insights.append(
            {
                "type": "tip",
                "title": "Consider Adding Dietary Fibre",
                "message": (
                    f"Estimated fibre is {fibre_g:.1f}g. Adding a side of salad, sabzi, whole fruit, "
                    "or whole-grain flatbreads can increase meal fibre."
                ),
            }
        )
    else:
        insights.append(
            {
                "type": "positive",
                "title": "Good Dietary Fibre Content",
                "message": (
                    f"This meal provides an estimated {fibre_g:.1f}g of dietary fibre, "
                    "contributing meaningfully toward typical daily intake goals."
                ),
            }
        )

    # Carbohydrate & fat balance
    if carbs_pct > 65.0:
        insights.append(
            {
                "type": "info",
                "title": "Carbohydrate-Forward Meal",
                "message": (
                    f"Carbohydrates represent ~{carbs_pct:.0f}% of estimated calories. "
                    "Balancing portions with non-starchy vegetables or lean protein can help steady meal energy."
                ),
            }
        )

    if fat_pct > 38.0:
        insights.append(
            {
                "type": "info",
                "title": "Higher Fat Energy Share",
                "message": (
                    f"Fats contribute ~{fat_pct:.0f}% of estimated calories. Note that frying oil, "
                    "ghee, butter, and creamy dressings can raise actual values further."
                ),
            }
        )

    if calories > 850:
        insights.append(
            {
                "type": "info",
                "title": "Energy-Dense Meal",
                "message": (
                    f"Total estimated energy is {calories:.0f} kcal. Ensure portion quantities "
                    "match your actual serving sizes, as visual estimates can vary."
                ),
            }
        )

    return insights
