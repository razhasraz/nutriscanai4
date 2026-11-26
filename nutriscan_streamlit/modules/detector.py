from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from config import (
    BASE_MODEL_PATH,
    CANONICAL_FOOD_CLASSES,
    COCO_DIRECT_FOOD_MAP,
    COCO_UNCERTAIN_FOOD_HINTS,
    CUSTOM_MODEL_PATH,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_IOU_THRESHOLD,
    INFERENCE_IMAGE_SIZE,
    UNCERTAIN_LABEL,
)

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Represents a single food detection within a camera frame."""

    detection_id: int
    label: str
    raw_label: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]
    is_uncertain: bool
    bbox_area_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "label": self.label,
            "raw_label": self.raw_label,
            "confidence": round(float(self.confidence), 4),
            "bbox": self.bbox,
            "is_uncertain": self.is_uncertain,
            "bbox_area_ratio": round(float(self.bbox_area_ratio), 4),
        }


class FoodDetector:
    """Wrapper around Ultralytics YOLO for multi-food live detection."""

    def __init__(self, weights_path: Path | None = None) -> None:
        self.model: Any = None
        self.model_mode: str = "uninitialized"
        self.weights_path: Path | None = None
        self.load_error: str | None = None
        self._canonical_lookup = {name.lower(): name for name in CANONICAL_FOOD_CLASSES}
        self._load_model(weights_path)

    def _resolve_weights_path(self, explicit_path: Path | None) -> tuple[Path | None, str]:
        if explicit_path is not None and explicit_path.exists():
            mode = "custom" if explicit_path.name == CUSTOM_MODEL_PATH.name else "base_coco"
            return explicit_path, mode
        if CUSTOM_MODEL_PATH.exists():
            return CUSTOM_MODEL_PATH, "custom"
        if BASE_MODEL_PATH.exists():
            return BASE_MODEL_PATH, "base_coco"
        return None, "missing"

    def _load_model(self, explicit_path: Path | None = None) -> None:
        resolved_path, mode = self._resolve_weights_path(explicit_path)
        if resolved_path is None:
            self.model_mode = "missing_weights"
            self.load_error = (
                f"No YOLO weights found at '{CUSTOM_MODEL_PATH}' or '{BASE_MODEL_PATH}'. "
                "Run 'python models/download_weights.py' to download base pretrained weights, "
                "or place your trained 40-class weights at 'models/nutriscan_food_yolo.pt'."
            )
            logger.warning(self.load_error)
            return

        try:
            from ultralytics import YOLO

            self.model = YOLO(str(resolved_path))
            self.weights_path = resolved_path
            self.model_mode = mode
            self.load_error = None
            logger.info("Loaded YOLO model (%s) from %s", mode, resolved_path)
        except Exception as exc:
            self.model = None
            self.model_mode = "load_error"
            self.load_error = f"Failed to initialize YOLO model: {exc}"
            logger.exception(self.load_error)

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def get_supported_classes(self) -> list[str]:
        """Returns only the food classes genuinely supported by the active loaded weights."""
        if not self.is_ready:
            return []
        if self.model_mode == "custom":
            names = getattr(self.model, "names", None)
            if isinstance(names, dict) and names:
                return [str(v) for v in names.values()]
            return list(CANONICAL_FOOD_CLASSES)
        return sorted(set(COCO_DIRECT_FOOD_MAP.values()))

    def get_status_summary(self) -> dict[str, Any]:
        return {
            "ready": self.is_ready,
            "mode": self.model_mode,
            "weights_path": str(self.weights_path) if self.weights_path else None,
            "error": self.load_error,
            "supported_classes": self.get_supported_classes(),
        }

    def _map_label(self, raw_name: str) -> tuple[str, bool]:
        """
        Maps model output class name to NutriScan canonical food label.
        Returns (mapped_label, is_uncertain).
        """
        normalized = raw_name.strip().lower()

        if self.model_mode == "custom":
            if normalized in self._canonical_lookup:
                return self._canonical_lookup[normalized], False
            return f"{UNCERTAIN_LABEL} ({raw_name})", True

        # Base COCO model mode: be strictly honest about capabilities
        if normalized in COCO_DIRECT_FOOD_MAP:
            return COCO_DIRECT_FOOD_MAP[normalized], False
        if normalized in COCO_UNCERTAIN_FOOD_HINTS:
            return f"{UNCERTAIN_LABEL} ({raw_name})", True
        return f"{UNCERTAIN_LABEL} ({raw_name})", True

    def detect(
        self,
        image_bgr: np.ndarray,
        conf_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        include_non_food_context: bool = False,
    ) -> list[DetectionResult]:
        """
        Runs YOLO inference on a BGR OpenCV image.
        Filters irrelevant COCO background detections unless relevant food/container.
        """
        if not self.is_ready or image_bgr is None or image_bgr.size == 0:
            return []

        height, width = image_bgr.shape[:2]
        frame_area = max(float(height * width), 1.0)

        results = self.model.predict(
            source=image_bgr,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=INFERENCE_IMAGE_SIZE,
            verbose=False,
        )

        detections: list[DetectionResult] = []
        if not results:
            return detections

        res = results[0]
        boxes = res.boxes
        names = res.names if hasattr(res, "names") else getattr(self.model, "names", {})

        if boxes is None or len(boxes) == 0:
            return detections

        det_idx = 1
        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            raw_name = str(names.get(cls_id, f"class_{cls_id}"))
            norm_raw = raw_name.strip().lower()

            if self.model_mode != "custom" and not include_non_food_context:
                is_food_or_container = (
                    norm_raw in COCO_DIRECT_FOOD_MAP or norm_raw in COCO_UNCERTAIN_FOOD_HINTS
                )
                if not is_food_or_container:
                    continue
                if norm_raw == "dining table":
                    continue

            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = [max(0, int(round(coord))) for coord in xyxy]
            x2 = min(width, x2)
            y2 = min(height, y2)

            bbox_area = max((x2 - x1) * (y2 - y1), 0)
            area_ratio = bbox_area / frame_area

            mapped_label, is_uncertain = self._map_label(raw_name)
            if conf < 0.45 and not is_uncertain:
                is_uncertain = True

            detections.append(
                DetectionResult(
                    detection_id=det_idx,
                    label=mapped_label,
                    raw_label=raw_name,
                    confidence=conf,
                    bbox=[x1, y1, x2, y2],
                    is_uncertain=is_uncertain,
                    bbox_area_ratio=area_ratio,
                )
            )
            det_idx += 1

        return detections

    @staticmethod
    def draw_detections(
        image_bgr: np.ndarray,
        detections: list[DetectionResult],
        model_mode: str = "base_coco",
    ) -> np.ndarray:
        """Draws clean botanical bounding boxes and actual confidence labels on frame."""
        annotated = image_bgr.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            # Botanical forest green (#527B60) for confident items, warm ochre (#B88446) for uncertain
            rgb_color = (82, 123, 96) if not det.is_uncertain else (184, 132, 70)
            bgr_color = (rgb_color[2], rgb_color[1], rgb_color[0])

            cv2.rectangle(annotated, (x1, y1), (x2, y2), bgr_color, 2)

            conf_pct = int(round(det.confidence * 100))
            short_label = det.label.replace(f"{UNCERTAIN_LABEL} ", "Uncertain ")
            tag = f"{short_label} {conf_pct}%"

            (text_w, text_h), baseline = cv2.getTextSize(
                tag, cv2.FONT_HERSHEY_SIMPLEX, 0.54, 2
            )
            pill_y1 = max(0, y1 - text_h - baseline - 8)
            pill_y2 = max(text_h + baseline + 8, y1)
            cv2.rectangle(
                annotated,
                (x1, pill_y1),
                (min(annotated.shape[1], x1 + text_w + 12), pill_y2),
                bgr_color,
                -1,
            )
            cv2.putText(
                annotated,
                tag,
                (x1 + 6, pill_y2 - baseline - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.54,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        mode_text = (
            "NutriScan AI | Custom 40-Class YOLO Model"
            if model_mode == "custom"
            else "NutriScan AI | Base Pretrained YOLO (Verify Unmapped Dishes)"
        )
        # Deep forest green HUD (#294C38 -> BGR 56, 76, 41)
        cv2.rectangle(annotated, (8, 8), (540, 34), (56, 76, 41), -1)
        cv2.putText(
            annotated,
            mode_text,
            (16, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (243, 247, 240),
            1,
            cv2.LINE_AA,
        )

        return annotated
