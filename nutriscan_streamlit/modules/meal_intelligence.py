from __future__ import annotations

from typing import Any

from config import FOOD_GROUP_CATALOG, FOOD_GROUP_MAP

CORE_VARIETY_GROUPS: list[str] = [
    "Grains & Staples",
    "Lentils & Legumes",
    "Vegetables & Greens",
    "Dairy & Paneer",
    "Eggs & Lean Proteins",
    "Fruits",
]


def analyze_meal_intelligence(analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Signature NutriScan Meal Intelligence Engine.

    Transforms item-level confirmed nutritional calculations into a holistic
    educational summary covering:
      1. Meal Composition
      2. Nutritional Balance
      3. Food-Group Variety (represented & unrepresented categories)
      4. Contextual Suggestions (non-medical, non-restrictive, data-grounded)
    """
    items: list[dict[str, Any]] = analysis.get("items", [])
    totals: dict[str, Any] = analysis.get("totals", {})
    macro_pct: dict[str, float] = analysis.get("macro_energy_pct", {})

    matched_items = [i for i in items if i.get("in_database", True)]
    total_cal = float(totals.get("total_calories", 0.0))

    # 1. Meal Composition
    composition: list[dict[str, Any]] = []
    for item in matched_items:
        cal = float(item.get("calories") or 0.0)
        cal_share = round((cal / total_cal) * 100.0, 1) if total_cal > 0 else 0.0
        group = item.get("food_group") or FOOD_GROUP_MAP.get(item["food_name"], "Other")
        composition.append(
            {
                "food_name": item["food_name"],
                "food_group": group,
                "portion_label": f"{item['quantity']} {item['unit']}",
                "grams": float(item["grams"]),
                "calories": cal,
                "calorie_share_pct": cal_share,
                "protein_g": float(item.get("protein_g") or 0.0),
                "carbs_g": float(item.get("carbs_g") or 0.0),
                "fat_g": float(item.get("fat_g") or 0.0),
                "fibre_g": float(item.get("fibre_g") or 0.0),
            }
        )

    # 2. Nutritional Balance Summary
    protein_g = float(totals.get("total_protein_g", 0.0))
    carbs_g = float(totals.get("total_carbs_g", 0.0))
    fat_g = float(totals.get("total_fat_g", 0.0))
    fibre_g = float(totals.get("total_fibre_g", 0.0))

    p_pct = float(macro_pct.get("protein_pct", 0.0))
    c_pct = float(macro_pct.get("carbs_pct", 0.0))
    f_pct = float(macro_pct.get("fat_pct", 0.0))

    if total_cal <= 0:
        balance_summary = "Confirm at least one database-matched food item to view meal nutritional balance."
    else:
        dominant_macro = max(
            [("carbohydrates", c_pct), ("protein", p_pct), ("fat", f_pct)],
            key=lambda x: x[1],
        )[0]
        balance_summary = (
            f"Across {len(matched_items)} analysed item(s), this meal provides an estimated "
            f"{total_cal:.0f} kcal with {dominant_macro} supplying the largest share of energy "
            f"(Carbs {c_pct:.0f}% · Protein {p_pct:.0f}% · Fat {f_pct:.0f}%) and "
            f"{fibre_g:.1f} g of dietary fibre."
        )

    nutritional_balance = {
        "summary": balance_summary,
        "calories": total_cal,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "fibre_g": fibre_g,
        "protein_pct": p_pct,
        "carbs_pct": c_pct,
        "fat_pct": f_pct,
    }

    # 3. Food-Group Variety
    group_items: dict[str, list[str]] = {}
    for entry in composition:
        grp = entry["food_group"]
        group_items.setdefault(grp, []).append(entry["food_name"])

    represented_groups = [
        {"group": grp, "items": group_items[grp]}
        for grp in FOOD_GROUP_CATALOG
        if grp in group_items
    ]
    unrepresented_groups = [
        grp for grp in CORE_VARIETY_GROUPS if grp not in group_items
    ]

    # 4. Contextual Suggestions (educational, non-medical, non-restrictive)
    suggestions: list[str] = []

    if not matched_items:
        suggestions.append(
            "Add and confirm items from the reference database to generate contextual meal insights."
        )
    else:
        carb_items = [
            e["food_name"]
            for e in composition
            if e["food_group"] == "Grains & Staples" or e["carbs_g"] >= 20.0
        ]
        legume_items = group_items.get("Lentils & Legumes", [])
        veg_items = group_items.get("Vegetables & Greens", [])
        fruit_items = group_items.get("Fruits", [])
        protein_group_present = bool(
            legume_items
            or group_items.get("Dairy & Paneer")
            or group_items.get("Eggs & Lean Proteins")
        )

        # Multiple carbohydrate sources + legume/protein observation
        if len(carb_items) >= 2 and legume_items and not veg_items:
            suggestions.append(
                f"Your meal contains multiple carbohydrate sources ({', '.join(carb_items[:3])}) "
                f"alongside a legume-based protein source ({', '.join(legume_items)}). "
                "Consider exploring additional vegetable variety such as sabzi or fresh salad in your meals."
            )
        elif len(carb_items) >= 2 and not protein_group_present:
            suggestions.append(
                f"This plate centres on grain and carbohydrate staples ({', '.join(carb_items[:3])}). "
                "Exploring complementary protein options like dal, rajma, chole, paneer, curd, or eggs "
                "can broaden the meal's amino acid and macronutrient diversity."
            )
        elif legume_items and veg_items:
            suggestions.append(
                f"Your meal brings together legumes ({', '.join(legume_items)}) and vegetables "
                f"({', '.join(veg_items)}), offering a varied combination of plant protein and fibre."
            )

        # Vegetable & fruit variety note
        if not veg_items and not (len(carb_items) >= 2 and legume_items):
            suggestions.append(
                "No leafy or cooked vegetable dishes are represented in this plate. "
                "Including a katori of seasonal sabzi, aloo gobi, soup, or fresh salad is an easy way to expand plant variety."
            )

        if not fruit_items and fibre_g < 6.0:
            suggestions.append(
                f"Estimated dietary fibre for this meal is {fibre_g:.1f} g. "
                "Whole grains (such as whole-wheat roti or oats), legumes, vegetables, or whole fruit "
                "naturally contribute additional dietary fibre across the day."
            )
        elif fibre_g >= 6.0:
            suggestions.append(
                f"This plate contributes an estimated {fibre_g:.1f} g of dietary fibre from "
                f"{', '.join(e['food_name'] for e in composition if e['fibre_g'] >= 1.5) or 'the confirmed items'}."
            )

        # Protein presence observation
        if p_pct < 14.0 and protein_g < 12.0:
            suggestions.append(
                f"Protein currently supplies about {p_pct:.0f}% ({protein_g:.1f} g) of estimated meal energy. "
                "Pairing everyday grains with dal, paneer, yogurt, eggs, fish, or grilled chicken increases protein variety."
            )
        elif protein_g >= 18.0:
            suggestions.append(
                f"Protein makes up ~{p_pct:.0f}% ({protein_g:.1f} g) of estimated energy, "
                "led by "
                + ", ".join(
                    e["food_name"]
                    for e in sorted(composition, key=lambda x: x["protein_g"], reverse=True)[:2]
                )
                + "."
            )

        # Preparation awareness (cooking fat / oil)
        if f_pct > 36.0 or group_items.get("Fried & Indulgent Snacks"):
            suggestions.append(
                "Preparation methods such as tadka, ghee brushing, or deep-frying can shift fat and energy values "
                "noticeably relative to standard database averages."
            )

    return {
        "composition": composition,
        "nutritional_balance": nutritional_balance,
        "food_group_variety": {
            "represented": represented_groups,
            "unrepresented": unrepresented_groups,
            "represented_count": len(represented_groups),
        },
        "contextual_suggestions": suggestions[:4],
        "missing_foods": analysis.get("missing_foods", []),
    }
