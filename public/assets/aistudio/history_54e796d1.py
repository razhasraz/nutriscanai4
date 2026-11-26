from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config import MEAL_HISTORY_CSV

HISTORY_COLUMNS: list[str] = [
    "meal_id",
    "timestamp",
    "meal_label",
    "foods_summary",
    "item_count",
    "total_grams",
    "total_calories",
    "total_protein_g",
    "total_carbs_g",
    "total_fat_g",
    "total_fibre_g",
]


class MealHistoryManager:
    """Manages reading, saving, clearing, and exporting meal history."""

    def __init__(self, history_csv: Path = MEAL_HISTORY_CSV) -> None:
        self.history_csv = history_csv
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        self.history_csv.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_csv.exists():
            pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(self.history_csv, index=False)

    def load_history(self) -> pd.DataFrame:
        self._ensure_file_exists()
        df = pd.read_csv(self.history_csv)
        if df.empty:
            return pd.DataFrame(columns=HISTORY_COLUMNS)
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)

    def save_meal(self, analysis: dict[str, Any], meal_label: str = "Scanned Meal") -> dict[str, Any]:
        items = analysis.get("items", [])
        totals = analysis.get("totals", {})
        if not items:
            raise ValueError("Cannot save an empty meal.")

        now = datetime.now()
        foods_summary = ", ".join(
            f"{item['food_name']} ({item['quantity']} {item['unit']})" for item in items
        )
        entry = {
            "meal_id": now.strftime("%Y%m%d%H%M%S%f")[:17],
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "meal_label": meal_label.strip() or "Scanned Meal",
            "foods_summary": foods_summary,
            "item_count": int(totals.get("item_count", len(items))),
            "total_grams": float(totals.get("total_grams", 0.0)),
            "total_calories": float(totals.get("total_calories", 0.0)),
            "total_protein_g": float(totals.get("total_protein_g", 0.0)),
            "total_carbs_g": float(totals.get("total_carbs_g", 0.0)),
            "total_fat_g": float(totals.get("total_fat_g", 0.0)),
            "total_fibre_g": float(totals.get("total_fibre_g", 0.0)),
        }

        df = self.load_history()
        updated = pd.concat([pd.DataFrame([entry]), df], ignore_index=True)
        updated.to_csv(self.history_csv, index=False)
        return entry

    def clear_history(self) -> None:
        pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(self.history_csv, index=False)

    def export_csv_bytes(self) -> bytes:
        df = self.load_history()
        return df.to_csv(index=False).encode("utf-8")
