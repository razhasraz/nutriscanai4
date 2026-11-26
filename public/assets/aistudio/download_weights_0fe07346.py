from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import BASE_MODEL_PATH, FALLBACK_BASE_MODEL_NAME, MODELS_DIR


def download_base_weights() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if BASE_MODEL_PATH.exists():
        print(f"[OK] Base weights already exist at: {BASE_MODEL_PATH}")
        return BASE_MODEL_PATH

    print(f"[INFO] Downloading official Ultralytics '{FALLBACK_BASE_MODEL_NAME}' weights...")
    from ultralytics import YOLO

    # Ultralytics automatically fetches official weights over HTTPS
    model = YOLO(FALLBACK_BASE_MODEL_NAME)
    downloaded_path = Path(model.ckpt_path) if getattr(model, "ckpt_path", None) else Path(FALLBACK_BASE_MODEL_NAME)

    if downloaded_path.exists() and downloaded_path.resolve() != BASE_MODEL_PATH.resolve():
        shutil.move(str(downloaded_path), str(BASE_MODEL_PATH))

    if BASE_MODEL_PATH.exists():
        print(f"[SUCCESS] Weights saved to: {BASE_MODEL_PATH}")
        return BASE_MODEL_PATH

    raise FileNotFoundError("Weights download completed, but file was not found at target path.")


if __name__ == "__main__":
    download_base_weights()
