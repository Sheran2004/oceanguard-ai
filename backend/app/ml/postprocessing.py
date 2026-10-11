"""Post-processing primitives used by the inference engine.

These are intentionally generic — they operate on simple dataclass-like
dicts so the same code can run on real model output or demo-mode
deterministic output.
"""
from __future__ import annotations

from typing import Iterable


def nms_iou(boxes: list[dict], iou_threshold: float = 0.45) -> list[dict]:
    """Class-agnostic Non-Maximum Suppression. Boxes are dicts with x1,y1,x2,y2,score."""
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: b.get("score", 0.0), reverse=True)
    keep: list[dict] = []
    while boxes:
        best = boxes.pop(0)
        keep.append(best)
        new_boxes = []
        for b in boxes:
            if iou(best, b) < iou_threshold:
                new_boxes.append(b)
        boxes = new_boxes
    return keep


def iou(a: dict, b: dict) -> float:
    ax1, ay1, ax2, ay2 = a["x1"], a["y1"], a["x2"], a["y2"]
    bx1, by1, bx2, by2 = b["x1"], b["y1"], b["x2"], b["y2"]
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def filter_by_confidence(boxes: Iterable[dict], threshold: float) -> list[dict]:
    return [b for b in boxes if float(b.get("score", 0.0)) >= threshold]


def decode_boxes(raw_predictions: list[list[float]], image_width: int, image_height: int) -> list[dict]:
    """Convert normalized [x_c, y_c, w, h, score, class_id] to pixel dicts."""
    decoded: list[dict] = []
    for pred in raw_predictions:
        if len(pred) < 6:
            continue
        x_c, y_c, w, h, score, cls = pred[:6]
        x1 = (x_c - w / 2.0) * image_width
        y1 = (y_c - h / 2.0) * image_height
        x2 = (x_c + w / 2.0) * image_width
        y2 = (y_c + h / 2.0) * image_height
        decoded.append({
            "x1": float(max(0.0, x1)),
            "y1": float(max(0.0, y1)),
            "x2": float(min(float(image_width), x2)),
            "y2": float(min(float(image_height), y2)),
            "score": float(score),
            "class_id": int(cls),
        })
    return decoded


def clamp_box(box: dict, width: int, height: int) -> dict:
    return {
        **box,
        "x1": float(max(0.0, min(width, box["x1"]))),
        "y1": float(max(0.0, min(height, box["y1"]))),
        "x2": float(max(0.0, min(width, box["x2"]))),
        "y2": float(max(0.0, min(height, box["y2"]))),
    }