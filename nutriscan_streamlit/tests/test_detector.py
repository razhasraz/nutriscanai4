from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import UNCERTAIN_LABEL
from modules.detector import DetectionResult, FoodDetector


def test_missing_weights_graceful_handling(tmp_path: Path) -> None:
    nonexistent = tmp_path / "does_not_exist.pt"
    detector = FoodDetector(weights_path=nonexistent)
    status = detector.get_status_summary()
    assert "ready" in status
    assert "mode" in status
    assert "supported_classes" in status


def test_honest_label_mapping() -> None:
    detector = FoodDetector.__new__(FoodDetector)
    detector.model_mode = "base_coco"
    detector._canonical_lookup = {}

    apple_label, apple_uncertain = detector._map_label("apple")
    assert apple_label == "Apple"
    assert apple_uncertain is False

    bowl_label, bowl_uncertain = detector._map_label("bowl")
    assert UNCERTAIN_LABEL in bowl_label
    assert bowl_uncertain is True


def test_draw_detections_on_blank_frame() -> None:
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    det = DetectionResult(
        detection_id=1,
        label="Apple",
        raw_label="apple",
        confidence=0.92,
        bbox=[100, 100, 220, 220],
        is_uncertain=False,
        bbox_area_ratio=0.05,
    )
    out = FoodDetector.draw_detections(blank, [det], model_mode="base_coco")
    assert out.shape == blank.shape
    assert out.sum() > 0
