from __future__ import annotations

import json
from collections import Counter
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
    "items_json",
]

MIN_MEALS_FOR_PATTERNS: int = 3


class MealHistoryManager:
    """Manages reading, saving, inspecting, clearing, exporting, and summarizing meal history."""

    def __init__(self, history_csv: Path = MEAL_HISTORY_CSV) -> None:
        self.history_csv = history_csv
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        self.history_csv.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_csv.exists():
            pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(self.history_csv, index=False)

    def load_history(self) -> pd.DataFrame:
        self._ensure_file_exists()
        try:
            df = pd.read_csv(self.history_csv)
        except Exception:
            return pd.DataFrame(columns=HISTORY_COLUMNS)

        if df.empty:
            return pd.DataFrame(columns=HISTORY_COLUMNS)

        # Backfill missing columns for legacy meal_history.csv files
        for col in HISTORY_COLUMNS:
            if col not in df.columns:
                df[col] = "" if col == "items_json" else 0

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
            "items_json": json.dumps(items, ensure_ascii=False),
        }

        df = self.load_history()
        updated = pd.concat([pd.DataFrame([entry]), df], ignore_index=True)
        updated.to_csv(self.history_csv, index=False)
        return entry

    @staticmethod
    def parse_meal_items(row: pd.Series | dict[str, Any]) -> list[dict[str, Any]]:
        raw = row.get("items_json", "")
        if not raw or pd.isna(raw):
            return []
        try:
            parsed = json.loads(str(raw))
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def compute_meal_pattern_insights(self) -> dict[str, Any]:
        """
        Analyses historical trends strictly from recorded meal history.
        Never fabricates records or draws conclusions from insufficient data.
        """
        df = self.load_history()
        meal_count = len(df)
        if meal_count < MIN_MEALS_FOR_PATTERNS:
            return {
                "sufficient_data": False,
                "meal_count": meal_count,
                "required_meals": MIN_MEALS_FOR_PATTERNS,
                "message": (
                    f"Meal Pattern Insights require at least {MIN_MEALS_FOR_PATTERNS} recorded meals. "
                    f"You currently have {meal_count} saved meal(s)."
                ),
            }

        ordered = df.sort_values("timestamp", ascending=True).reset_index(drop=True)
        for col in [
            "total_calories",
            "total_protein_g",
            "total_carbs_g",
            "total_fat_g",
            "total_fibre_g",
        ]:
            ordered[col] = pd.to_numeric(ordered[col], errors="coerce").fillna(0.0)

        # Count frequently analysed foods from structured items_json or foods_summary
        food_counter: Counter[str] = Counter()
        for _, row in ordered.iterrows():
            parsed_items = self.parse_meal_items(row)
            if parsed_items:
                for item in parsed_items:
                    name = str(item.get("food_name", "")).strip()
                    if name:
                        food_counter[name] += 1
            else:
                summary = str(row.get("foods_summary", ""))
                for chunk in summary.split(","):
                    name = chunk.split("(")[0].strip()
                    if name:
                        food_counter[name] += 1

        top_foods = [{"food_name": k, "count": v} for k, v in food_counter.most_common(8)]

        # Compare recent half vs earlier half for nutrient shifts
        mid = max(1, len(ordered) // 2)
        early = ordered.iloc[:mid]
        recent = ordered.iloc[mid:]

        avg_cal = float(ordered["total_calories"].mean())
        avg_protein = float(ordered["total_protein_g"].mean())
        avg_carbs = float(ordered["total_carbs_g"].mean())
        avg_fat = float(ordered["total_fat_g"].mean())
        avg_fibre = float(ordered["total_fibre_g"].mean())

        protein_delta = round(
            float(recent["total_protein_g"].mean() - early["total_protein_g"].mean()), 1
        )
        fibre_delta = round(
            float(recent["total_fibre_g"].mean() - early["total_fibre_g"].mean()), 1
        )

        return {
            "sufficient_data": True,
            "meal_count": meal_count,
            "required_meals": MIN_MEALS_FOR_PATTERNS,
            "averages": {
                "calories": round(avg_cal, 1),
                "protein_g": round(avg_protein, 1),
                "carbs_g": round(avg_carbs, 1),
                "fat_g": round(avg_fat, 1),
                "fibre_g": round(avg_fibre, 1),
            },
            "recent_shifts": {
                "protein_delta_g": protein_delta,
                "fibre_delta_g": fibre_delta,
            },
            "top_foods": top_foods,
            "timeline_df": ordered,
        }

    def clear_history(self) -> None:
        pd.DataFrame(columns=HISTORY_COLUMNS).to_csv(self.history_csv, index=False)

    def export_csv_bytes(self) -> bytes:
        df = self.load_history()
        export_cols = [c for c in df.columns if c != "items_json"]
        return df[export_cols].to_csv(index=False).encode("utf-8")
