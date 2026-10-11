"""Anomaly listing + statistics."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.orm import Anomaly, Detection, Scan


class AnomalyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_anomalies(self, mission_id: Optional[int] = None) -> list[dict]:
        q = (
            self.db.query(Anomaly, Detection, Scan)
            .join(Detection, Anomaly.detection_id == Detection.id)
            .join(Scan, Detection.scan_id == Scan.id)
        )
        if mission_id is not None:
            q = q.filter(Scan.mission_id == mission_id)
        rows = q.order_by(Anomaly.created_at.desc()).all()
        out = []
        for anomaly, det, scan in rows:
            out.append({
                "anomaly_id": anomaly.id,
                "detection_uid": det.detection_uid,
                "scan_uid": scan.scan_uid,
                "scan_id": scan.id,
                "detection_id": det.id,
                "score": anomaly.anomaly_score,
                "method": anomaly.method,
                "description": anomaly.description or det.explanation,
                "region_label": anomaly.region_label,
                "review_status": det.review_status,
                "priority": det.priority,
                "class_name": det.class_name,
                "created_at": anomaly.created_at.isoformat() if anomaly.created_at else None,
            })
        return out

    def statistics(self) -> dict:
        rows = self.db.query(Anomaly).all()
        if not rows:
            return {"count": 0, "avg_score": 0, "max_score": 0, "review_required": 0}
        scores = [r.anomaly_score for r in rows]
        review_required = sum(1 for r in rows if r.detection_id is not None)
        return {
            "count": len(rows),
            "avg_score": round(sum(scores) / len(scores), 4),
            "max_score": round(max(scores), 4),
            "review_required": review_required,
        }