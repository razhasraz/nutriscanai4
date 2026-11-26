from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CUSTOM_MODEL_PATH, MODELS_DIR, TRAINING_DIR


def train_model(
    data_yaml: Path,
    base_model: str,
    epochs: int,
    batch: int,
    imgsz: int,
    device: str,
) -> None:
    from ultralytics import YOLO

    if not data_yaml.exists():
        raise FileNotFoundError(f"Dataset YAML not found: {data_yaml}")

    model = YOLO(base_model)
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=str(TRAINING_DIR / "runs"),
        name="nutriscan_food_yolo",
        exist_ok=True,
        patience=15,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        fliplr=0.5,
    )

    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    if best_weights.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_weights, CUSTOM_MODEL_PATH)
        print(f"[SUCCESS] Deployed trained weights to: {CUSTOM_MODEL_PATH}")
    else:
        print(f"[WARN] Training finished, but best.pt not found at {best_weights}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train NutriScan AI 40-class YOLO food detector.")
    parser.add_argument("--data", type=Path, default=TRAINING_DIR / "dataset.yaml")
    parser.add_argument("--base-model", type=str, default="yolo11s.pt")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", type=str, default="0", help="'0' for GPU, 'cpu' for CPU")
    args = parser.parse_args()

    train_model(
        data_yaml=args.data,
        base_model=args.base_model,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
    )
