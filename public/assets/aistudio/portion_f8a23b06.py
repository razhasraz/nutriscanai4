from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import PORTION_REFERENCE_CSV, UNIT_KEY_MAP


class PortionManager:
    """Manages standard food portion references and unit conversions."""

    def __init__(self, csv_path: Path = PORTION_REFERENCE_CSV) -> None:
        self.csv_path = csv_path
        self.df = self._load_portion_csv()

    def _load_portion_csv(self) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Portion reference CSV not found: {self.csv_path}")
        df = pd.read_csv(self.csv_path)
        df["food_name"] = df["food_name"].astype(str).str.strip()
        df["default_unit"] = df["default_unit"].astype(str).str.strip()
        return df

    def get_reference_row(self, food_name: str) -> dict[str, Any] | None:
        match = self.df[self.df["food_name"].str.lower() == food_name.strip().lower()]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_default_portion(self, food_name: str) -> tuple[float, str]:
        row = self.get_reference_row(food_name)
        if row is None:
            return 100.0, "Grams (g)"

        default_qty = float(row.get("default_quantity", 1.0))
        raw_unit = str(row.get("default_unit", "Servings")).strip()
        unit_display_map = {
            "Grams": "Grams (g)",
            "Grams (g)": "Grams (g)",
            "Pieces": "Pieces",
            "Cups": "Cups",
            "Katoris": "Katoris",
            "Millilitres": "Millilitres (ml)",
            "Millilitres (ml)": "Millilitres (ml)",
            "Servings": "Servings",
        }
        return default_qty, unit_display_map.get(raw_unit, "Servings")

    def get_available_units(self, food_name: str) -> list[str]:
        row = self.get_reference_row(food_name)
        units = ["Grams (g)"]
        if row is None:
            units.extend(["Servings", "Cups", "Katoris", "Pieces", "Millilitres (ml)"])
            return units

        if float(row.get("grams_per_piece", 0)) > 0:
            units.append("Pieces")
        if float(row.get("grams_per_cup", 0)) > 0:
            units.append("Cups")
        if float(row.get("grams_per_katori", 0)) > 0:
            units.append("Katoris")
        if float(row.get("grams_per_ml", 0)) > 0:
            units.append("Millilitres (ml)")
        if float(row.get("grams_per_serving", 0)) > 0:
            units.append("Servings")
        return units

    def convert_to_grams(self, food_name: str, quantity: float, unit_display: str) -> tuple[float, str]:
        """
        Converts user quantity + unit into grams.
        Returns (grams, conversion_note).
        """
        qty = max(float(quantity), 0.0)
        unit_key = UNIT_KEY_MAP.get(unit_display, "serving")

        if unit_key == "grams":
            return round(qty, 1), "Direct gram entry"

        row = self.get_reference_row(food_name)
        if row is None:
            fallback_grams = qty * 100.0
            return round(fallback_grams, 1), "Fallback 100g/unit reference"

        col_map = {
            "piece": "grams_per_piece",
            "cup": "grams_per_cup",
            "katori": "grams_per_katori",
            "ml": "grams_per_ml",
            "serving": "grams_per_serving",
        }
        col_name = col_map.get(unit_key, "grams_per_serving")
        factor = float(row.get(col_name, 0.0))

        # Fallback if selected unit doesn't apply natively (e.g., 'Pieces' for Dal)
        if factor <= 0:
            fallback_serving = float(row.get("grams_per_serving", 150.0))
            factor = fallback_serving if fallback_serving > 0 else 150.0
            return (
                round(qty * factor, 1),
                f"Unit '{unit_display}' approximated via standard serving ({factor:.0f}g)",
            )

        return round(qty * factor, 1), f"1 {unit_display.rstrip('(g)ml ').rstrip('s')} ≈ {factor:.1f}g"

    @staticmethod
    def experimental_visual_estimate_grams(bbox_area_ratio: float) -> float:
        """
        EXPERIMENTAL ONLY: Rough heuristic estimating portion grams from 2D bounding-box
        frame occupancy. An RGB camera cannot measure true food mass, depth, or density.
        Always require user confirmation before nutritional calculation.
        """
        ratio = max(min(float(bbox_area_ratio), 0.85), 0.02)
        # Heuristic mapping assuming typical handheld meal framing (~80g to ~400g)
        estimated = 60.0 + (ratio * 550.0)
        return round(min(max(estimated, 40.0), 450.0), 0)
