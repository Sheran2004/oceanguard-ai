"""Computer vision and ML inference package for OceanGuard AI."""
from app.ml.inference import InferenceEngine, get_inference_engine
from app.ml.preprocessing import (
    enhance_image,
    to_grayscale,
    normalize_image,
    apply_clahe,
    denoise_image,
    sharpen_image,
)
from app.ml.postprocessing import filter_by_confidence, nms_iou, decode_boxes
from app.ml.model_loader import load_model, ModelBundle
from app.ml.anomaly_detector import AnomalyDetector, score_anomaly
from app.ml.confidence import calibrate_confidence, confidence_bucket
from app.ml.visualization import draw_detections, encode_overlay_png

__all__ = [
    "InferenceEngine",
    "get_inference_engine",
    "enhance_image",
    "to_grayscale",
    "normalize_image",
    "apply_clahe",
    "denoise_image",
    "sharpen_image",
    "filter_by_confidence",
    "nms_iou",
    "decode_boxes",
    "load_model",
    "ModelBundle",
    "AnomalyDetector",
    "score_anomaly",
    "calibrate_confidence",
    "confidence_bucket",
    "draw_detections",
    "encode_overlay_png",
]