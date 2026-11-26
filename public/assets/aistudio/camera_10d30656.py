from __future__ import annotations

import threading
import time
from typing import Any

import av
import cv2
import numpy as np
from streamlit_webrtc import VideoProcessorBase

from config import DEFAULT_CONFIDENCE_THRESHOLD
from modules.detector import DetectionResult, FoodDetector


class FoodVideoProcessor(VideoProcessorBase):
    """
    Processes live WebRTC video frames continuously using YOLO food detection.
    Maintains thread-safe state so the Streamlit UI can read latest detections
    without blocking the video stream.
    """

    def __init__(self, detector: FoodDetector) -> None:
        self.detector = detector
        self._lock = threading.Lock()
        self._conf_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
        self._latest_detections: list[dict[str, Any]] = []
        self._latest_frame_rgb: np.ndarray | None = None
        self._fps: float = 0.0
        self._last_timestamp: float = time.perf_counter()
        self._frame_count: int = 0

    def set_confidence_threshold(self, conf: float) -> None:
        with self._lock:
            self._conf_threshold = float(conf)

    def get_latest_detections(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._latest_detections]

    def get_latest_snapshot_rgb(self) -> np.ndarray | None:
        with self._lock:
            if self._latest_frame_rgb is None:
                return None
            return self._latest_frame_rgb.copy()

    def get_fps(self) -> float:
        with self._lock:
            return self._fps

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img_bgr = frame.to_ndarray(format="bgr24")

        with self._lock:
            conf = self._conf_threshold

        detections: list[DetectionResult] = []
        if self.detector is not None and self.detector.is_ready:
            detections = self.detector.detect(img_bgr, conf_threshold=conf)
            annotated_bgr = self.detector.draw_detections(
                img_bgr, detections, model_mode=self.detector.model_mode
            )
        else:
            annotated_bgr = img_bgr.copy()
            cv2.rectangle(annotated_bgr, (8, 8), (580, 42), (185, 28, 28), -1)
            cv2.putText(
                annotated_bgr,
                "Model weights missing. Run: python models/download_weights.py",
                (16, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        now = time.perf_counter()
        dt = max(now - self._last_timestamp, 1e-4)
        instant_fps = 1.0 / dt

        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        with self._lock:
            self._latest_detections = [d.to_dict() for d in detections]
            self._latest_frame_rgb = annotated_rgb
            self._fps = (0.8 * self._fps + 0.2 * instant_fps) if self._fps > 0 else instant_fps
            self._last_timestamp = now
            self._frame_count += 1

        return av.VideoFrame.from_ndarray(annotated_bgr, format="bgr24")

