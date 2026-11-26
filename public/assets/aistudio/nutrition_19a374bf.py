from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import FOOD_NUTRITION_CSV
from modules.portion import PortionManager


class NutritionAnalyzer:
    """Computes food-level and meal-level nutrition from food_nutrition.csv."""

    def __init__(
        self,
        nutrition_csv: Path = FOOD_NUTRITION_CSV,
        portion_manager: PortionManager | None = None,
    ) -> None:
        self.nutrition_csv = nutrition_csv
        self.portion_manager = portion_manager or PortionManager()
        self.df = self._load_nutrition_csv()

    def _load_nutrition_csv(self) -> pd.DataFrame:
        if not self.nutrition_csv.exists():
            raise FileNotFoundError(f"Nutrition database CSV not found: {self.nutrition_csv}")
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
        return df

    def list_foods(self) -> list[str]:
        return self.df["food_name"].tolist()

    def get_food_record(self, food_name: str) -> dict[str, Any] | None:
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
                "category": "Custom / Unlisted",
                "quantity": quantity,
                "unit": unit_display,
                "grams": grams,
                "portion_source": portion_source,
                "conversion_note": conversion_note,
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
                "fibre_g": 0.0,
                "source": "Not in database",
                "notes": "No nutritional match found",
                "confidence": detection_confidence,
            }

        return {
            "food_name": record["food_name"],
            "category": record["category"],
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
        }

    def analyze_meal(self, confirmed_items: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Aggregates a list of confirmed meal entries into full nutritional analysis.
        Each entry expects: food_name, quantity, unit, optional portion_source, confidence.
        """
        analyzed_items: list[dict[str, Any]] = []
        for item in confirmed_items:
            result = self.calculate_item_nutrition(
                food_name=str(item["food_name"]),
                quantity=float(item.get("quantity", 1.0)),
                unit_display=str(item.get("unit", "Servings")),
                portion_source=str(item.get("portion_source", "User-confirmed")),
                detection_confidence=item.get("confidence"),
            )
            analyzed_items.append(result)

        totals = {
            "total_grams": round(sum(i["grams"] for i in analyzed_items), 1),
            "total_calories": round(sum(i["calories"] for i in analyzed_items), 1),
            "total_protein_g": round(sum(i["protein_g"] for i in analyzed_items), 1),
            "total_carbs_g": round(sum(i["carbs_g"] for i in analyzed_items), 1),
            "total_fat_g": round(sum(i["fat_g"] for i in analyzed_items), 1),
            "total_fibre_g": round(sum(i["fibre_g"] for i in analyzed_items), 1),
            "item_count": len(analyzed_items),
        }

        # Energy macro share (4 kcal/g protein & carbs, 9 kcal/g fat)
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
        }

