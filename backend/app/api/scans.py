"""Scan endpoints: upload, analyze, list, detail, compare."""
from __future__ import annotations

import logging
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.api.deps import scan_service
from app.models.database import get_db
from app.models.orm import Detection, Scan
from app.services.detection_service import DetectionService
from app.services.scan_service import ScanService, ScanValidationError
from sqlalchemy.orm import Session

from app.ml.inference import get_inference_engine
from app.ml.visualization import draw_detections, encode_original_data_uri
from app.utils.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scans", tags=["scans"])


def _scan_to_dict(scan: Scan, include_detections: bool = False) -> dict:
    location = None
    if scan.location is not None:
        location = {
            "latitude": scan.location.latitude,
            "longitude": scan.location.longitude,
            "depth_m": scan.location.depth_m,
            "region_label": scan.location.region_label,
            "is_demo": scan.location.is_demo,
        }
    detections = [
        {
            "id": d.id,
            "detection_uid": d.detection_uid,
            "scan_id": d.scan_id,
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
        for d in (scan.detections if include_detections else [])
    ]
    detection_count = len(scan.detections) if scan.detections is not None else 0
    anomaly_count = sum(1 for d in scan.detections if d.is_anomaly) if scan.detections else 0
    high_count = sum(1 for d in scan.detections if d.priority == "high") if scan.detections else 0
    return {
        "id": scan.id,
        "scan_uid": scan.scan_uid,
        "mission_id": scan.mission_id,
        "filename": scan.filename,
        "original_name": scan.original_name,
        "file_size": scan.file_size,
        "width": scan.width,
        "height": scan.height,
        "status": scan.status,
        "is_demo": scan.is_demo,
        "notes": scan.notes,
        "timestamp": scan.timestamp.isoformat() if scan.timestamp else None,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "location": location,
        "detection_count": detection_count,
        "anomaly_count": anomaly_count,
        "high_priority_count": high_count,
        "detections": detections if include_detections else [],
    }


@router.post("/upload")
async def upload_scan(
    file: UploadFile = File(...),
    mission_id: Optional[int] = Form(default=None),
    is_demo: bool = Form(default=False),
    notes: Optional[str] = Form(default=None),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
    depth_m: Optional[float] = Form(default=None),
    region_label: Optional[str] = Form(default=None),
    auto_analyze: bool = Form(default=True),
    service: ScanService = Depends(scan_service),
) -> dict:
    data = await file.read()
    try:
        scan = service.create_scan(
            original_name=file.filename or "upload.png",
            data=data,
            mission_id=mission_id,
            is_demo=is_demo,
            notes=notes,
            latitude=latitude,
            longitude=longitude,
            depth_m=depth_m,
            region_label=region_label,
        )
    except ScanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if auto_analyze:
        try:
            scan = service.analyze(scan.id)
        except ScanValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Auto-analysis failed: %s", exc)
            raise HTTPException(status_code=500, detail="Inference failed; scan saved for later analysis.")

    return _scan_to_dict(scan, include_detections=False)


@router.post("/{scan_id}/analyze")
def analyze_scan(scan_id: int, service: ScanService = Depends(scan_service)) -> dict:
    try:
        scan = service.analyze(scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ScanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _scan_to_dict(scan, include_detections=False)


@router.get("")
def list_scans(
    mission_id: Optional[int] = Query(default=None),
    is_demo: Optional[bool] = Query(default=None),
    service: ScanService = Depends(scan_service),
) -> list[dict]:
    scans = service.list_scans(mission_id=mission_id)
    if is_demo is not None:
        scans = [s for s in scans if s.is_demo == is_demo]
    return [_scan_to_dict(s, include_detections=False) for s in scans]
    


@router.get("/{scan_id}")
def get_scan(scan_id: int, service: ScanService = Depends(scan_service)) -> dict:
    scan = service.get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return _scan_to_dict(scan, include_detections=True)


@router.get("/{scan_id}/image")
def get_scan_image(scan_id: int, service: ScanService = Depends(scan_service)):
    scan = service.get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    settings = get_settings()
    path = settings.upload_path / scan.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored image missing.")
    return FileResponse(str(path), media_type="image/png", filename=scan.original_name)


@router.get("/{scan_id}/overlay")
def get_scan_overlay(scan_id: int, service: ScanService = Depends(scan_service)):
    """Return the original image annotated with detection boxes as PNG."""
    scan = service.get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    settings = get_settings()
    path = settings.upload_path / scan.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored image missing.")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Stored image could not be decoded.")
    boxes = [
        {
            "x1": d.x1, "y1": d.y1, "x2": d.x2, "y2": d.y2,
            "class_name": d.class_name, "confidence": d.confidence,
        }
        for d in scan.detections
    ]
    overlay = draw_detections(image, boxes)
    success, buf = cv2.imencode(".png", overlay)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode overlay.")
    from fastapi.responses import Response
    return Response(content=buf.tobytes(), media_type="image/png")


@router.get("/{scan_id}/enhanced")
def get_scan_enhanced(scan_id: int, service: ScanService = Depends(scan_service)):
    scan = service.get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    settings = get_settings()
    path = settings.upload_path / scan.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored image missing.")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Stored image could not be decoded.")
    engine = get_inference_engine()
    enhanced = engine.enhanced_image(image)
    success, buf = cv2.imencode(".png", enhanced)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode enhanced image.")
    from fastapi.responses import Response
    return Response(content=buf.tobytes(), media_type="image/png")


@router.post("/compare")
def compare_scans(payload: dict, db: Session = Depends(get_db)) -> dict:
    a = int(payload.get("scan_a_id", 0))
    b = int(payload.get("scan_b_id", 0))
    if a <= 0 or b <= 0:
        raise HTTPException(status_code=400, detail="scan_a_id and scan_b_id are required.")
    return DetectionService(db).compare(a, b)