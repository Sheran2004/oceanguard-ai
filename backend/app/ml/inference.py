"""High-level inference engine used by the API layer.

This module glues together preprocessing, model loading, post-processing,
anomaly detection and visualization. It supports two operating modes:

* REAL: a real trained model is loaded (YOLO etc). Optional heavy deps are
  imported lazily so the package stays importable on CPU-only machines.
* DEMO: deterministic content-aware predictions are produced. The output is
  shaped exactly like a real model's output so downstream code is identical.

The architecture is intentionally easy to swap: replace `InferenceEngine`
with a class that implements `predict(image: np.ndarray) -> list[dict]`.
"""
from __future__ import annotations

import hashlib
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.ml.anomaly_detector import AnomalyDetector
from app.ml.confidence import calibrate_confidence
from app.ml.model_loader import ModelBundle, load_model
from app.ml.postprocessing import clamp_box, filter_by_confidence, nms_iou
from app.ml.preprocessing import enhance_image, to_grayscale
from app.utils.config import load_classes_config


logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """Single detection output by the inference engine."""
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    area_ratio: float
    is_anomaly: bool = False
    anomaly_score: float = 0.0
    explanation: str = ""


class InferenceEngine:
    """Orchestrates the full AI pipeline.

    Construction is cheap (no model weights are loaded eagerly). The first call
    to `predict` triggers the model loader, which gracefully falls back to
    demo mode when the requested model file does not exist.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        anomaly_threshold: float = 0.65,
    ) -> None:
        self.confidence_threshold = float(confidence_threshold)
        self.iou_threshold = float(iou_threshold)
        self.anomaly_threshold = float(anomaly_threshold)
        self._bundle: Optional[ModelBundle] = None
        self._anomaly: AnomalyDetector = AnomalyDetector(threshold=anomaly_threshold)
        self._classes: dict = load_classes_config()

    # ---------------- lifecycle ----------------

    def initialize(self) -> ModelBundle:
        if self._bundle is None:
            self._bundle = load_model()
            logger.info("Loaded model bundle: %s (real=%s)", self._bundle.summary(), self._bundle.is_real)
        return self._bundle

    @property
    def bundle(self) -> ModelBundle:
        if self._bundle is None:
            self._bundle = load_model()
        return self._bundle

    @property
    def is_demo(self) -> bool:
        return not self.bundle.is_real

    @property
    def classes(self) -> dict:
        return self._classes

    # ---------------- public API ----------------

    def predict(
        self,
        image: np.ndarray,
        *,
        run_anomaly: bool = True,
    ) -> list[Prediction]:
        """Run inference only when a trained model is available."""

        if image is None or image.size == 0:
            raise ValueError("Empty image passed to inference engine.")

        if not self.bundle.is_real:
            logger.warning(
                "Detection skipped: no trained model is configured. "
                "Demo-generated detections are disabled for uploaded images."
            )
            return []

        if image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        h, w = image.shape[:2]
        enhanced = enhance_image(
            to_grayscale(image) if image.ndim == 3 else image
        )

        raw_boxes = self._predict_real(image)

        clamped = [clamp_box(b, w, h) for b in raw_boxes]
        filtered = filter_by_confidence(clamped, self.confidence_threshold)
        nms_boxes = nms_iou(filtered, iou_threshold=self.iou_threshold)

        predictions: list[Prediction] = []
        classes = self._classes.get("classes", {})
        image_area = float(w * h)

        for box in nms_boxes:
            class_id = int(box.get("class_id", 0))
            class_meta = classes.get(class_id, {})
            class_name = class_meta.get("name", f"class_{class_id}")

            confidence = calibrate_confidence(float(box.get("score", 0.0)))
            box_width = max(0.0, box["x2"] - box["x1"])
            box_height = max(0.0, box["y2"] - box["y1"])
            area_ratio = (
                box_width * box_height / image_area if image_area > 0 else 0.0
            )

            is_anomaly = bool(class_meta.get("is_anomaly", False)) or class_id == 5
            anomaly_score = 0.0

            explanation = (
                f"Model prediction for {class_name}; "
                "independent human verification is required."
            )

            if run_anomaly:
                x1, y1 = int(box["x1"]), int(box["y1"])
                x2, y2 = int(box["x2"]), int(box["y2"])
                crop = enhanced[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]

                if crop.size:
                    result = self._anomaly.score(enhanced, crop)
                    anomaly_score = result.score

            predictions.append(
                Prediction(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    x1=box["x1"],
                    y1=box["y1"],
                    x2=box["x2"],
                    y2=box["y2"],
                    area_ratio=area_ratio,
                    is_anomaly=is_anomaly,
                    anomaly_score=anomaly_score,
                    explanation=explanation,
                )
            )

        return predictions

    def enhanced_image(self, image: np.ndarray) -> np.ndarray:
        return enhance_image(to_grayscale(image) if image.ndim == 3 else image)

    # ---------------- internal helpers ----------------

    def _seed_from_image(self, image: np.ndarray) -> int:
        digest = hashlib.md5(image.tobytes()).digest()
        return int.from_bytes(digest[:4], "big")

    def _predict_real(self, image: np.ndarray) -> list[dict]:
        """Run inference using the configured trained model."""
        try:
            from ultralytics import YOLO

            model = YOLO(str(self.bundle.path))
            results = model.predict(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False,
            )

            boxes: list[dict] = []

            for result in results:
                if not hasattr(result, "boxes") or result.boxes is None:
                    continue

                for box in result.boxes:
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    score = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())

                    boxes.append({
                        "x1": xyxy[0],
                        "y1": xyxy[1],
                        "x2": xyxy[2],
                        "y2": xyxy[3],
                        "score": score,
                        "class_id": class_id,
                    })

            return boxes

        except Exception as exc:
            logger.exception("Real model inference failed: %s", exc)
            raise RuntimeError(
                "Model inference failed. Check the trained weights and dependencies."
            ) from exc

    def _predict_demo(self, enhanced: np.ndarray, *, image_id_seed: int) -> list[dict]:
        """Produce deterministic, content-aware predictions for demo mode.

        The algorithm scans the image with a small grid and emits boxes around
        regions with high contrast / edge density. This keeps the output
        visually plausible without needing a real model.
        """
        h, w = enhanced.shape[:2]
        rng = random.Random(image_id_seed)

        # Build a saliency map via Sobel edges.
        gx = cv2.Sobel(enhanced, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(enhanced, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        if mag.max() > 0:
            mag = (mag / mag.max() * 255).astype(np.uint8)
        else:
            mag = enhanced.copy()

        # Threshold + dilate to find candidate blobs.
        _, th = cv2.threshold(mag, 90, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        th = cv2.dilate(th, kernel, iterations=1)

        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw * bh < 0.001 * (w * h):
                continue
            # Reject very thin slivers (often acoustic shadow lines).
            if max(bw, bh) > 8 * min(bw, bh) and min(bw, bh) > 0:
                continue
            candidates.append((x, y, bw, bh))

        # If we found too few, inject a few synthetic ones so demo screens
        # are interesting.
        if len(candidates) < 3:
            for _ in range(3 - len(candidates)):
                bw = rng.randint(int(w * 0.05), int(w * 0.18))
                bh = rng.randint(int(h * 0.05), int(h * 0.18))
                x = rng.randint(int(w * 0.05), max(int(w * 0.05), w - bw - 1))
                y = rng.randint(int(h * 0.05), max(int(h * 0.05), h - bh - 1))
                candidates.append((x, y, bw, bh))

        # Sort by area, keep top-N.
        candidates.sort(key=lambda c: c[2] * c[3], reverse=True)
        max_dets = min(len(candidates), 6)
        candidates = candidates[:max_dets]

        # Class assignment: deterministic per region so the same image
        # always produces the same predictions.
        class_pool = [0, 1, 2, 3, 4, 5]
        rng2 = random.Random(image_id_seed ^ 0xA5A5)
        rng2.shuffle(class_pool)

        boxes: list[dict] = []
        for idx, (x, y, bw, bh) in enumerate(candidates):
            cls_id = class_pool[idx % len(class_pool)]
            # Confidence: inversely related to candidate rank.
            base_conf = 0.94 - idx * 0.07 + rng.uniform(-0.04, 0.04)
            base_conf = max(0.30, min(0.97, base_conf))
            boxes.append({
                "x1": float(x), "y1": float(y),
                "x2": float(x + bw), "y2": float(y + bh),
                "score": float(base_conf),
                "class_id": int(cls_id),
            })
        return boxes

    def _build_explanation(
        self,
        class_name: str,
        confidence: float,
        area_ratio: float,
        is_anomaly: bool,
        anomaly_score: float,
    ) -> str:
        if is_anomaly:
            return (
                f"Region appears consistent with an unknown underwater pattern "
                f"(anomaly score {anomaly_score:.2f}). Visual characteristics do not "
                f"match a known object class. Manual inspection recommended."
            )
        if confidence >= 0.85:
            certainty = "high"
        elif confidence >= 0.6:
            certainty = "moderate"
        else:
            certainty = "low"
        size = "large" if area_ratio > 0.10 else "medium" if area_ratio > 0.03 else "small"
        return (
            f"Detected object has visual characteristics consistent with '{class_name}' "
            f"(confidence {confidence:.0%}, {certainty}). Object footprint is {size} "
            f"relative to the scan area. AI-assisted review priority has been assigned. "
            f"This is a decision-support output and requires human verification."
        )


# ---------- module-level singleton ----------

_engine: Optional[InferenceEngine] = None


def get_inference_engine() -> InferenceEngine:
    global _engine
    if _engine is None:
        from app.utils.config import get_settings

        s = get_settings()
        _engine = InferenceEngine(
            confidence_threshold=s.confidence_threshold,
            iou_threshold=s.iou_threshold,
            anomaly_threshold=s.anomaly_threshold,
        )
        _engine.initialize()
    return _engine


def reset_inference_engine() -> None:
    global _engine
    _engine = None