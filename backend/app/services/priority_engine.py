"""Transparent rule-based priority engine.

The output is explicitly labelled as "AI-Assisted Review Priority", not a
scientific risk score. Inputs:

  * detection confidence
  * object class
  * area ratio (relative footprint)
  * number of nearby detections on the same scan (cluster)
  * anomaly flag

Rules are configurable via config/classes.yaml -> priority_rules.
"""
from __future__ import annotations

import math
from typing import Iterable

from app.utils.config import load_classes_config


def _distance(a: dict, b: dict) -> float:
    ax, ay = (a["x1"] + a["x2"]) / 2.0, (a["y1"] + a["y2"]) / 2.0
    bx, by = (b["x1"] + b["x2"]) / 2.0, (b["y1"] + b["y2"]) / 2.0
    return math.hypot(ax - bx, ay - by)


def compute_priority(
    detection: dict,
    all_detections: Iterable[dict],
    image_width: int,
    image_height: int,
) -> tuple[str, list[str]]:
    """Return (priority, reasons)."""
    classes_cfg = load_classes_config().get("classes", {})
    rules = load_classes_config().get("priority_rules", {})

    cls_meta = classes_cfg.get(detection.get("class_id", -1), {})
    base = cls_meta.get("base_priority", "medium")
    reasons: list[str] = []
    score = 0

    conf = float(detection.get("confidence", 0.0))
    if conf >= float(rules.get("high_confidence_threshold", 0.85)):
        score += 2
        reasons.append(f"High confidence ({conf:.0%}).")
    elif conf < float(rules.get("review_confidence_threshold", 0.40)):
        score -= 1
        reasons.append(f"Low confidence ({conf:.0%}) — verification required.")

    area_ratio = detection.get("area_ratio", 0.0)
    if area_ratio >= float(rules.get("size_high_area_ratio", 0.10)):
        score += 1
        reasons.append("Large object footprint relative to scan.")
    elif area_ratio >= float(rules.get("size_medium_area_ratio", 0.03)):
        score += 0
        reasons.append("Medium object footprint.")

    if detection.get("is_anomaly"):
        score -= 1
        reasons.append("Unknown anomaly pattern — manual review required.")

    cluster_d = float(rules.get("cluster_nearby_distance_px", 80))
    cluster_n = int(rules.get("cluster_nearby_count", 3))
    nearby = 0
    for other in all_detections:
        if other is detection:
            continue
        if _distance(detection, other) <= cluster_d:
            nearby += 1
    if nearby >= cluster_n:
        score += 1
        reasons.append(f"Clustered with {nearby} nearby detections.")

    # Translate score to priority level.
    if detection.get("is_anomaly"):
        return "review", reasons + ["Flagged as unknown anomaly — review required."]
    if base == "high":
        score += 1
    if base == "low":
        score -= 1
    if score >= 3:
        return "high", reasons + ["Elevated AI-assisted review priority."]
    if score >= 1:
        return "medium", reasons + ["Moderate AI-assisted review priority."]
    if score >= -1:
        return "low", reasons + ["Low AI-assisted review priority."]
    return "review", reasons + ["Insufficient confidence — review required."]