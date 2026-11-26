from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def validate_yolo_label_file(label_path: Path, num_classes: int = 40) -> tuple[bool, str]:
    lines = label_path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return False, "Empty label file"
    for line_no, line in enumerate(lines, start=1):
        parts = line.strip().split()
        if len(parts) != 5:
            return False, f"Line {line_no}: expected 5 values, got {len(parts)}"
        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:]]
        except ValueError:
            return False, f"Line {line_no}: non-numeric values"
        if not (0 <= cls_id < num_classes):
            return False, f"Line {line_no}: class ID {cls_id} out of range [0, {num_classes - 1}]"
        if any(not (0.0 <= c <= 1.0) for c in coords):
            return False, f"Line {line_no}: normalized coordinates out of [0, 1]"
    return True, "OK"


def prepare_split(
    source_dir: Path,
    output_dir: Path,
    train_ratio: float = 0.75,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> None:
    images_dir = source_dir / "images"
    labels_dir = source_dir / "labels"

    if not images_dir.exists() or not labels_dir.exists():
        raise FileNotFoundError(
            f"Expected '{images_dir}' and '{labels_dir}' directories inside {source_dir}"
        )

    pairs: list[tuple[Path, Path]] = []
    skipped = 0

    for img_path in sorted(images_dir.iterdir()):
        if img_path.suffix.lower() not in IMAGE_EXTS:
            continue
        lbl_path = labels_dir / f"{img_path.stem}.txt"
        if not lbl_path.exists():
            skipped += 1
            continue
        valid, reason = validate_yolo_label_file(lbl_path)
        if not valid:
            print(f"[SKIP] {lbl_path.name}: {reason}")
            skipped += 1
            continue
        pairs.append((img_path, lbl_path))

    if not pairs:
        raise RuntimeError("No valid image/label pairs found to prepare.")

    random.seed(seed)
    random.shuffle(pairs)

    n = len(pairs)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    splits = {
        "train": pairs[:n_train],
        "val": pairs[n_train : n_train + n_val],
        "test": pairs[n_train + n_val :],
    }

    for split_name, split_pairs in splits.items():
        img_out = output_dir / "images" / split_name
        lbl_out = output_dir / "labels" / split_name
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for img_path, lbl_path in split_pairs:
            shutil.copy2(img_path, img_out / img_path.name)
            shutil.copy2(lbl_path, lbl_out / lbl_path.name)

    print(
        f"[SUCCESS] Prepared {n} samples (skipped {skipped}): "
        f"train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare YOLO food dataset splits.")
    parser.add_argument("--source", type=Path, default=Path("training/raw_dataset"))
    parser.add_argument("--output", type=Path, default=Path("training/prepared_dataset"))
    parser.add_argument("--train-ratio", type=float, default=0.75)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    args = parser.parse_args()

    prepare_split(args.source, args.output, args.train_ratio, args.val_ratio)
