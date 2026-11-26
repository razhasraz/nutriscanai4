from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CUSTOM_MODEL_PATH, TRAINING_DIR


def validate_model(weights: Path, data_yaml: Path, split: str = "val") -> None:
    from ultralytics import YOLO

    if not weights.exists():
        raise FileNotFoundError(f"Model weights not found: {weights}")
    if not data_yaml.exists():
        raise FileNotFoundError(f"Dataset YAML not found: {data_yaml}")

    model = YOLO(str(weights))
    metrics = model.val(data=str(data_yaml), split=split)

    print("\n=== NutriScan AI Model Evaluation Metrics ===")
    print(f"Weights   : {weights}")
    print(f"Split     : {split}")
    print(f"mAP@50    : {metrics.box.map50:.4f}")
    print(f"mAP@50-95 : {metrics.box.map:.4f}")
    print(f"Precision : {metrics.box.mp:.4f}")
    print(f"Recall    : {metrics.box.mr:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate NutriScan AI YOLO food detection model"
    )
    parser.add_argument("--weights", type=Path, default=CUSTOM_MODEL_PATH)
    parser.add_argument("--data", type=Path, default=TRAINING_DIR / "dataset.yaml")
    parser.add_argument("--split", type=str, default="val", choices=["val", "test"])
    args = parser.parse_args()

    validate_model(
        weights=args.weights,
        data_yaml=args.data,
        split=args.split,
    )