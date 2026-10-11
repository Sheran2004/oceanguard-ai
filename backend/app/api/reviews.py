"""Review endpoints: approve / reject / review detections, export feedback."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import anomaly_service, detection_service
from app.models.schemas import ReviewCreate
from app.services.detection_service import DetectionService


router = APIRouter(prefix="/api", tags=["reviews"])


@router.post("/detections/{detection_id}/review")
def review_detection(
    detection_id: int,
    payload: ReviewCreate,
    service: DetectionService = Depends(detection_service),
) -> dict:
    try:
        det = service.review(
            detection_id=detection_id,
            decision=payload.decision,
            reviewer=payload.reviewer,
            comment=payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "id": det.id,
        "detection_uid": det.detection_uid,
        "review_status": det.review_status,
        "reviewer_comment": det.reviewer_comment,
    }


@router.get("/reviews/export")
def export_reviews(service: DetectionService = Depends(detection_service)) -> Response:
    csv_data = service.export_reviews()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=oceanguard_review_dataset.csv"},
    )


@router.get("/anomalies")
def list_anomalies(
    mission_id: int | None = Query(default=None),
    anomaly=Depends(anomaly_service),
) -> list[dict]:
    return anomaly.list_anomalies(mission_id=mission_id)