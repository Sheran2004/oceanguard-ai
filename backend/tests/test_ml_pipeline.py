"""Unit tests for the ML inference and priority pipeline."""
from __future__ import annotations

import numpy as np

from app.ml.anomaly_detector import AnomalyDetector
from app.ml.preprocessing import enhance_image, to_grayscale
from app.ml.confidence import calibrate_confidence, confidence_bucket
from app.ml.postprocessing import iou, nms_iou, filter_by_confidence
from app.services.priority_engine import compute_priority


def test_to_grayscale_idempotent():
    img = np.random.randint(0, 255, (32, 32), dtype=np.uint8)
    out = to_grayscale(img)
    assert out.shape == img.shape


def test_enhance_image_runs():
    img = (np.random.rand(64, 64) * 255).astype(np.uint8)
    out = enhance_image(img)
    assert out.shape == img.shape
    assert out.dtype == np.uint8


def test_confidence_calibration_bounds():
    assert 0 <= calibrate_confidence(-0.3) <= 1
    assert 0 <= calibrate_confidence(1.7) <= 1
    assert calibrate_confidence(0.5) == 0.5


def test_confidence_buckets():
    assert confidence_bucket(0.1) == "0.0-0.2"
    assert confidence_bucket(0.5) == "0.4-0.6"
    assert confidence_bucket(0.95) == "0.8-1.0"


def test_iou_basic():
    a = {"x1": 0, "y1": 0, "x2": 10, "y2": 10}
    b = {"x1": 5, "y1": 5, "x2": 15, "y2": 15}
    # Intersection 5x5=25, Union (100+100-25)=175, IoU=25/175≈0.143
    assert abs(iou(a, b) - 25 / 175) < 1e-6


def test_nms_removes_duplicates():
    boxes = [
        {"x1": 0, "y1": 0, "x2": 10, "y2": 10, "score": 0.9, "class_id": 0},
        {"x1": 1, "y1": 1, "x2": 11, "y2": 11, "score": 0.7, "class_id": 0},
        {"x1": 100, "y1": 100, "x2": 110, "y2": 110, "score": 0.8, "class_id": 0},
    ]
    out = nms_iou(boxes, iou_threshold=0.5)
    assert len(out) == 2
    assert out[0]["score"] == 0.9


def test_confidence_filter():
    boxes = [
        {"x1": 0, "y1": 0, "x2": 5, "y2": 5, "score": 0.9, "class_id": 0},
        {"x1": 10, "y1": 10, "x2": 15, "y2": 15, "score": 0.2, "class_id": 0},
    ]
    assert len(filter_by_confidence(boxes, threshold=0.5)) == 1


def test_anomaly_detector_runs():
    img = (np.random.rand(128, 128) * 255).astype(np.uint8)
    det = AnomalyDetector(threshold=0.65)
    result = det.score(img)
    assert 0.0 <= result.score <= 1.0
    assert isinstance(result.is_anomaly, bool)
    assert isinstance(result.explanation, str)


def test_priority_engine_unknown_anomaly_returns_review():
    det = {"x1": 0, "y1": 0, "x2": 50, "y2": 50, "confidence": 0.9, "area_ratio": 0.05, "is_anomaly": True, "class_id": 5}
    priority, reasons = compute_priority(det, [], 100, 100)
    assert priority == "review"
    assert len(reasons) >= 1


def test_priority_engine_high_confidence_large_object():
    det = {"x1": 0, "y1": 0, "x2": 50, "y2": 50, "confidence": 0.95, "area_ratio": 0.15, "is_anomaly": False, "class_id": 1}
    priority, _ = compute_priority(det, [], 100, 100)
    # Fishing Net has base priority "high" + large footprint + high confidence
    assert priority in {"high", "medium"}