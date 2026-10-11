"""Detection-related operations: reviews, exports, comparisons."""
from __future__ import annotations

import csv
import io
import json
import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import Detection, Review, Scan


class DetectionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------------- queries ----------------

    def list_detections(
        self,
        *,
        scan_id: Optional[int] = None,
        mission_id: Optional[int] = None,
        class_name: Optional[str] = None,
        priority: Optional[str] = None,
        is_anomaly: Optional[bool] = None,
        review_status: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> list[Detection]:
        q = self.db.query(Detection).join(Scan, Detection.scan_id == Scan.id)
        if scan_id is not None:
            q = q.filter(Detection.scan_id == scan_id)
        if mission_id is not None:
            q = q.filter(Scan.mission_id == mission_id)
        if class_name:
            q = q.filter(Detection.class_name == class_name)
        if priority:
            q = q.filter(Detection.priority == priority)
        if is_anomaly is not None:
            q = q.filter(Detection.is_anomaly == is_anomaly)
        if review_status:
            q = q.filter(Detection.review_status == review_status)
        if min_confidence is not None:
            q = q.filter(Detection.confidence >= min_confidence)
        return q.order_by(Detection.created_at.desc()).all()

    def get_detection(self, detection_id: int) -> Optional[Detection]:
        return self.db.query(Detection).filter(Detection.id == detection_id).first()

    # ---------------- review ----------------

    def review(self, detection_id: int, *, decision: str, reviewer: str, comment: Optional[str]) -> Detection:
        if decision not in {"approved", "rejected", "review"}:
            raise ValueError("decision must be one of approved | rejected | review")
        det = self.get_detection(detection_id)
        if det is None:
            raise ValueError(f"Detection {detection_id} not found.")
        det.review_status = decision
        det.reviewer_comment = comment
        review = Review(
            detection_id=det.id,
            reviewer=reviewer or "operator",
            decision=decision,
            comment=comment,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(det)
        return det

    # ---------------- export ----------------

    def export_reviews(self) -> bytes:
        """Return a CSV file of all reviewed detections for retraining."""
        q = (
            self.db.query(Detection, Scan)
            .join(Scan, Detection.scan_id == Scan.id)
            .filter(Detection.review_status.in_(["approved", "rejected", "review"]))
            .order_by(Detection.created_at.desc())
        )
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "image_id", "detection_id", "scan_uid", "predicted_class", "class_id",
            "confidence", "x1", "y1", "x2", "y2", "priority", "is_anomaly",
            "anomaly_score", "review_status", "reviewer_comment", "is_demo_scan",
            "timestamp",
        ])
        for det, scan in q.all():
            writer.writerow([
                scan.scan_uid, det.detection_uid, scan.scan_uid,
                det.class_name, det.class_id, round(det.confidence, 4),
                round(det.x1, 2), round(det.y1, 2), round(det.x2, 2), round(det.y2, 2),
                det.priority, det.is_anomaly, round(det.anomaly_score, 4),
                det.review_status, det.reviewer_comment or "", scan.is_demo,
                det.created_at.isoformat() if det.created_at else "",
            ])
        return buf.getvalue().encode("utf-8")

    # ---------------- comparison ----------------

    def compare(self, scan_a_id: int, scan_b_id: int) -> dict:
        a = self.db.query(Detection).filter(Detection.scan_id == scan_a_id).all()
        b = self.db.query(Detection).filter(Detection.scan_id == scan_b_id).all()

        def _key(d: Detection) -> tuple:
            return (d.class_name, round(d.x1 / 20), round(d.y1 / 20))

        keys_a = {_key(d): d for d in a}
        keys_b = {_key(d): d for d in b}

        persistent_keys = set(keys_a.keys()) & set(keys_b.keys())
        new_keys = set(keys_b.keys()) - set(keys_a.keys())
        removed_keys = set(keys_a.keys()) - set(keys_b.keys())

        notes = []
        if persistent_keys:
            notes.append(f"{len(persistent_keys)} detections appear in both scans.")
        if new_keys:
            notes.append(f"{len(new_keys)} new anomalous regions detected in the latest scan.")
        if removed_keys:
            notes.append(f"{len(removed_keys)} detections from the earlier scan are not present in the latest one.")
        if not notes:
            notes.append("No overlapping regions detected between scans.")

        return {
            "scan_a_id": scan_a_id,
            "scan_b_id": scan_b_id,
            "persistent": len(persistent_keys),
            "new_detections": len(new_keys),
            "removed": len(removed_keys),
            "changed_regions": len(new_keys) + len(removed_keys),
            "notes": notes,
        }