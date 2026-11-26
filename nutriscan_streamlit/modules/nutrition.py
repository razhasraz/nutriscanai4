from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import FOOD_GROUP_MAP, FOOD_NUTRITION_CSV
from modules.portion import PortionManager

NUTRITION_COLUMNS: list[str] = [
    "food_name",
    "category",
    "calories_per_100g",
    "protein_per_100g",
    "carbs_per_100g",
    "fat_per_100g",
    "fibre_per_100g",
    "source",
    "notes",
]


class NutritionAnalyzer:
    """Computes food-level and meal-level nutrition from food_nutrition.csv."""

    def __init__(
        self,
        nutrition_csv: Path = FOOD_NUTRITION_CSV,
        portion_manager: PortionManager | None = None,
    ) -> None:
        self.nutrition_csv = nutrition_csv
        self.portion_manager = portion_manager or PortionManager()
        self.load_error: str | None = None
        self.df = self._load_nutrition_csv()

    def _load_nutrition_csv(self) -> pd.DataFrame:
        if not self.nutrition_csv.exists():
            self.load_error = f"Nutrition database CSV not found: {self.nutrition_csv}"
            return pd.DataFrame(columns=NUTRITION_COLUMNS)
        try:
            df = pd.read_csv(self.nutrition_csv)
            df["food_name"] = df["food_name"].astype(str).str.strip()
            df["category"] = df["category"].astype(str).str.strip()
            numeric_cols = [
                "calories_per_100g",
                "protein_per_100g",
                "carbs_per_100g",
                "fat_per_100g",
                "fibre_per_100g",
            ]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            self.load_error = None
            return df
        except Exception as exc:
            self.load_error = f"Failed to read nutrition database CSV: {exc}"
            return pd.DataFrame(columns=NUTRITION_COLUMNS)

    def list_foods(self) -> list[str]:
        if self.df.empty:
            return []
        return self.df["food_name"].tolist()

    def get_food_record(self, food_name: str) -> dict[str, Any] | None:
        if self.df.empty:
            return None
        match = self.df[self.df["food_name"].str.lower() == food_name.strip().lower()]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def calculate_item_nutrition(
        self,
        food_name: str,
        quantity: float,
        unit_display: str,
        portion_source: str = "User-confirmed",
        detection_confidence: float | None = None,
        verification_status: str = "Confirmed by user",
        original_ai_label: str | None = None,
        is_uncertain: bool = False,
    ) -> dict[str, Any]:
        """Calculates nutritional contribution for a single confirmed food item."""
        record = self.get_food_record(food_name)
        grams, conversion_note = self.portion_manager.convert_to_grams(
            food_name, quantity, unit_display
        )
        scale = grams / 100.0

        if record is None:
            return {
                "food_name": food_name,
                "category": "Unlisted",
                "food_group": "Unclassified",
                "in_database": False,
                "quantity": round(float(quantity), 2),
                "unit": unit_display,
                "grams": grams,
                "portion_source": portion_source,
                "conversion_note": conversion_note,
                "calories": None,
                "protein_g": None,
                "carbs_g": None,
                "fat_g": None,
                "fibre_g": None,
                "source": "Not found in database",
                "notes": "This item is not present in food_nutrition.csv; no values were fabricated.",
                "confidence": detection_confidence,
                "verification_status": verification_status,
                "original_ai_label": original_ai_label,
                "is_uncertain": is_uncertain,
            }

        canonical_name = str(record["food_name"])
        return {
            "food_name": canonical_name,
            "category": str(record["category"]),
            "food_group": FOOD_GROUP_MAP.get(canonical_name, "Other"),
            "in_database": True,
            "quantity": round(float(quantity), 2),
            "unit": unit_display,
            "grams": grams,
            "portion_source": portion_source,
            "conversion_note": conversion_note,
            "calories": round(float(record["calories_per_100g"]) * scale, 1),
            "protein_g": round(float(record["protein_per_100g"]) * scale, 1),
            "carbs_g": round(float(record["carbs_per_100g"]) * scale, 1),
            "fat_g": round(float(record["fat_per_100g"]) * scale, 1),
            "fibre_g": round(float(record["fibre_per_100g"]) * scale, 1),
            "source": str(record.get("source", "Reference Database")),
            "notes": str(record.get("notes", "")),
            "confidence": detection_confidence,
            "verification_status": verification_status,
            "original_ai_label": original_ai_label,
            "is_uncertain": is_uncertain,
        }

    def analyze_meal(self, confirmed_items: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Aggregates a list of confirmed meal entries into full nutritional analysis.
        Missing database items are flagged transparently and never fabricated.
        """
        analyzed_items: list[dict[str, Any]] = []
        missing_foods: list[str] = []

        for item in confirmed_items:
            result = self.calculate_item_nutrition(
                food_name=str(item["food_name"]),
                quantity=float(item.get("quantity", 1.0)),
                unit_display=str(item.get("unit", "Servings")),
                portion_source=str(item.get("portion_source", "User-confirmed")),
                detection_confidence=item.get("confidence"),
                verification_status=str(item.get("verification_status", "Confirmed by user")),
                original_ai_label=item.get("original_ai_label"),
                is_uncertain=bool(item.get("is_uncertain", False)),
            )
            analyzed_items.append(result)
            if not result["in_database"]:
                missing_foods.append(result["food_name"])

        matched_items = [i for i in analyzed_items if i["in_database"]]

        totals = {
            "total_grams": round(sum(i["grams"] for i in analyzed_items), 1),
            "total_calories": round(sum(float(i["calories"] or 0.0) for i in matched_items), 1),
            "total_protein_g": round(sum(float(i["protein_g"] or 0.0) for i in matched_items), 1),
            "total_carbs_g": round(sum(float(i["carbs_g"] or 0.0) for i in matched_items), 1),
            "total_fat_g": round(sum(float(i["fat_g"] or 0.0) for i in matched_items), 1),
            "total_fibre_g": round(sum(float(i["fibre_g"] or 0.0) for i in matched_items), 1),
            "item_count": len(analyzed_items),
            "matched_item_count": len(matched_items),
        }

        p_kcal = totals["total_protein_g"] * 4.0
        c_kcal = totals["total_carbs_g"] * 4.0
        f_kcal = totals["total_fat_g"] * 9.0
        macro_kcal = p_kcal + c_kcal + f_kcal

        if macro_kcal > 0:
            macro_pct = {
                "protein_pct": round((p_kcal / macro_kcal) * 100.0, 1),
                "carbs_pct": round((c_kcal / macro_kcal) * 100.0, 1),
                "fat_pct": round((f_kcal / macro_kcal) * 100.0, 1),
            }
        else:
            macro_pct = {"protein_pct": 0.0, "carbs_pct": 0.0, "fat_pct": 0.0}

        return {
            "items": analyzed_items,
            "totals": totals,
            "macro_energy_pct": macro_pct,
            "missing_foods": missing_foods,
        }
