"""Anomaly detection layer.

Real implementations would use:
  * feature-embedding distance from a trained backbone
  * reconstruction error from an autoencoder
  * isolation forest on patch embeddings
  * one-class SVM

The demo mode uses a deterministic but content-aware heuristic:
  - Compute a coarse histogram on the cropped detection region.
  - Combine with edge density and contrast measures.
  - Produce a score in [0,1]; >= threshold => "anomaly".

This still demonstrates the API contract: any backend can replace this with
a real anomaly model without changing the rest of the system.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class AnomalyResult:
    score: float
    method: str
    is_anomaly: bool
    explanation: str


class AnomalyDetector:
    """Stateless anomaly scorer. Operates on the detection crop + image stats."""

    def __init__(self, threshold: float = 0.65, method: str = "content+edge+contrast") -> None:
        self.threshold = float(threshold)
        self.method = method

    def score(self, image: np.ndarray, crop: np.ndarray | None = None) -> AnomalyResult:
        if image is None or image.size == 0:
            return AnomalyResult(0.0, self.method, False, "Empty image.")

        h, w = image.shape[:2]
        if crop is None or crop.size == 0:
            region = image
        else:
            region = crop

        gray_full = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        gray_crop = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if region.ndim == 3 else region

        # Contrast-based component
        contrast = float(np.std(gray_crop)) / 128.0
        contrast = max(0.0, min(1.0, contrast))

        # Edge density
        edges = cv2.Canny(gray_crop, 60, 120)
        edge_density = float(edges.mean()) / 255.0

        # Histogram skew: how unusual is the crop intensity distribution?
        hist = cv2.calcHist([gray_crop], [0], None, [32], [0, 256]).flatten()
        hist = hist / max(hist.sum(), 1e-6)
        entropy = float(-np.sum(hist * np.log2(hist + 1e-9)) / np.log2(32))
        skew = 1.0 - entropy  # lower entropy => more skewed => more anomalous

        # Combined score. The mix keeps the value responsive but bounded.
        score = 0.45 * contrast + 0.30 * skew + 0.25 * edge_density
        score = float(max(0.0, min(1.0, score)))

        # Add a small deterministic jitter from the image hash so demo images
        # don't all share an identical score.
        digest = hashlib.md5(gray_full.tobytes()).digest()
        jitter = (digest[0] / 255.0 - 0.5) * 0.05
        score = float(max(0.0, min(1.0, score + jitter)))

        is_anomaly = score >= self.threshold
        if is_anomaly:
            explanation = (
                "Image region differs significantly from typical background patterns "
                "(edge density, contrast or intensity distribution). Manual review "
                "recommended. Unknown objects are NOT classified as dangerous."
            )
        else:
            explanation = (
                "Region statistics are within typical distribution; pattern matches known "
                "object characteristics. Verification by a human operator still recommended."
            )
        return AnomalyResult(
            score=round(score, 4),
            method=self.method,
            is_anomaly=is_anomaly,
            explanation=explanation,
        )


def score_anomaly(image: np.ndarray, crop: np.ndarray | None = None, threshold: float = 0.65) -> AnomalyResult:
    return AnomalyDetector(threshold=threshold).score(image, crop)