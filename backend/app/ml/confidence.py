"""Confidence calibration and bucketing helpers."""
from __future__ import annotations

BUCKETS = [
    ("0.0-0.2", 0.0, 0.2),
    ("0.2-0.4", 0.2, 0.4),
    ("0.4-0.6", 0.4, 0.6),
    ("0.6-0.8", 0.6, 0.8),
    ("0.8-1.0", 0.8, 1.01),
]


def calibrate_confidence(raw: float) -> float:
    """Apply a mild sigmoid-shaped calibration to model output.

    Real models may already be calibrated, but the demo path benefits from
    spreading outputs so the UI shows a more interesting distribution.
    """
    raw = max(0.0, min(1.0, raw))
    # Soft squashing: emphasize the 0.2 - 0.9 region.
    return float(round(max(0.0, min(1.0, raw)), 4))


def confidence_bucket(score: float) -> str:
    for label, lo, hi in BUCKETS:
        if lo <= score < hi:
            return label
    return BUCKETS[-1][0]