from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CANONICAL_FOOD_CLASSES
from modules.nutrition import NutritionAnalyzer
from modules.portion import PortionManager
from modules.recommendations import generate_meal_insights


def test_all_40_canonical_foods_exist_in_databases() -> None:
    analyzer = NutritionAnalyzer()
    portion_mgr = PortionManager()

    db_foods = set(analyzer.list_foods())
    portion_foods = set(portion_mgr.df["food_name"].tolist())

    for food in CANONICAL_FOOD_CLASSES:
        assert food in db_foods, f"Missing '{food}' in food_nutrition.csv"
        assert food in portion_foods, f"Missing '{food}' in portion_reference.csv"


def test_portion_conversion_katori_and_pieces() -> None:
    portion_mgr = PortionManager()

    roti_grams, _ = portion_mgr.convert_to_grams("Roti / Chapati", 2, "Pieces")
    assert roti_grams == 80.0

    dal_grams, _ = portion_mgr.convert_to_grams("Dal", 1, "Katoris")
    assert dal_grams == 150.0


def test_meal_analysis_calculation() -> None:
    analyzer = NutritionAnalyzer()
    meal = [
        {"food_name": "Roti / Chapati", "quantity": 2, "unit": "Pieces", "portion_source": "User-confirmed"},
        {"food_name": "Dal", "quantity": 1, "unit": "Katoris", "portion_source": "User-confirmed"},
    ]
    result = analyzer.analyze_meal(meal)

    assert result["totals"]["item_count"] == 2
    assert result["totals"]["total_grams"] == 230.0
    # 80g Roti (297 kcal/100g = 237.6) + 150g Dal (116 kcal/100g = 174.0) = 411.6 kcal
    assert abs(result["totals"]["total_calories"] - 411.6) < 0.2
    assert result["macro_energy_pct"]["protein_pct"] > 0

    insights = generate_meal_insights(result)
    assert len(insights) > 0
