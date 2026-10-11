"""Detection endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import detection_service
from app.models.orm import Detection
from app.services.detection_service import DetectionService


router = APIRouter(prefix="/api/detections", tags=["detections"])


def _det_to_dict(d: Detection) -> dict:
    return {
        "id": d.id,
        "scan_id": d.scan_id,
        "detection_uid": d.detection_uid,
        "class_id": d.class_id,
        "class_name": d.class_name,
        "confidence": round(d.confidence, 4),
        "x1": round(d.x1, 2), "y1": round(d.y1, 2),
        "x2": round(d.x2, 2), "y2": round(d.y2, 2),
        "width": round(d.width, 2), "height": round(d.height, 2),
        "area_ratio": round(d.area_ratio, 4),
        "is_anomaly": d.is_anomaly,
        "anomaly_score": round(d.anomaly_score, 4),
        "priority": d.priority,
        "review_status": d.review_status,
        "reviewer_comment": d.reviewer_comment,
        "explanation": d.explanation,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
def list_detections(
    scan_id: Optional[int] = Query(default=None),
    mission_id: Optional[int] = Query(default=None),
    class_name: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    is_anomaly: Optional[bool] = Query(default=None),
    review_status: Optional[str] = Query(default=None),
    min_confidence: Optional[float] = Query(default=None),
    service: DetectionService = Depends(detection_service),
) -> list[dict]:
    detections = service.list_detections(
        scan_id=scan_id,
        mission_id=mission_id,
        class_name=class_name,
        priority=priority,
        is_anomaly=is_anomaly,
        review_status=review_status,
        min_confidence=min_confidence,
    )
    return [_det_to_dict(d) for d in detections]


@router.get("/{detection_id}")
def get_detection(detection_id: int, service: DetectionService = Depends(detection_service)) -> dict:
    det = service.get_detection(detection_id)
    if det is None:
        raise HTTPException(status_code=404, detail="Detection not found.")
    return _det_to_dict(det)