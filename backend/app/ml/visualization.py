"""Visualization helpers used by the inference engine.

We avoid heavy dependencies so it works on CPU-only demo machines.
"""
from __future__ import annotations

import base64
from io import BytesIO

import cv2
import numpy as np


CLASS_COLORS_BGR = {
    "marine_debris": (90, 200, 90),
    "fishing_net": (60, 90, 230),
    "plastic_debris": (200, 200, 60),
    "metal_object": (40, 40, 220),
    "man_made_object": (200, 90, 200),
    "unknown_anomaly": (40, 200, 230),
}


def _color_for(class_name: str) -> tuple:
    return CLASS_COLORS_BGR.get(class_name, (180, 180, 180))


def draw_detections(
    image: np.ndarray,
    detections: list[dict],
    *,
    show_labels: bool = True,
    show_confidence: bool = True,
    thickness: int = 2,
) -> np.ndarray:
    """Render bounding boxes onto a copy of the image. Returns BGR ndarray."""
    if image.ndim == 2:
        canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        canvas = image.copy()

    for idx, det in enumerate(detections, start=1):
        x1 = int(round(det["x1"]))
        y1 = int(round(det["y1"]))
        x2 = int(round(det["x2"]))
        y2 = int(round(det["y2"]))
        cls = det.get("class_name", "object")
        conf = det.get("confidence", det.get("score", 0.0))
        color = _color_for(cls)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)
        label = f"#{idx} {cls}" if show_labels else f"#{idx}"
        if show_confidence:
            label = f"{label} {conf:.0%}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        ty1 = max(0, y1 - th - 8)
        cv2.rectangle(canvas, (x1, ty1), (x1 + tw + 8, ty1 + th + 6), color, -1)
        cv2.putText(canvas, label, (x1 + 4, ty1 + th + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return canvas


def encode_overlay_png(image: np.ndarray) -> str:
    """Encode a numpy image as base64 PNG (data URI fragment, no prefix)."""
    success, buf = cv2.imencode(".png", image)
    if not success:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")


def save_overlay_png(image: np.ndarray, path: str) -> bool:
    return bool(cv2.imwrite(path, image))


def encode_original_data_uri(image: np.ndarray) -> str:
    """Encode the grayscale sonar image to PNG and return a data URI."""
    success, buf = cv2.imencode(".png", image)
    if not success:
        return ""
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def to_bytesio(image: np.ndarray, ext: str = ".png") -> BytesIO:
    success, buf = cv2.imencode(ext, image)
    bio = BytesIO(buf.tobytes())
    return bio