"""Scan ingestion, validation, and analysis orchestration."""
from __future__ import annotations

import io
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.ml.inference import InferenceEngine, Prediction, get_inference_engine
from app.models.orm import Detection, Location, Mission, Scan
from app.services.detection_service import DetectionService
from app.services.geo_service import GeoService
from app.services.priority_engine import compute_priority
from app.utils.config import get_settings


logger = logging.getLogger(__name__)


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
SUPPORTED_MIME = {"image/png", "image/jpeg", "image/bmp", "image/tiff", "image/webp"}


class ScanValidationError(Exception):
    pass


class ScanService:
    def __init__(self, db: Session, engine: Optional[InferenceEngine] = None) -> None:
        self.db = db
        self.engine = engine or get_inference_engine()

    # ---------------- validation ----------------

    @staticmethod
    def validate_upload(filename: str, content_type: str, size: int) -> None:
        ext = Path(filename).suffix.lower()
        settings = get_settings()
        if ext not in SUPPORTED_EXTS and content_type not in SUPPORTED_MIME:
            raise ScanValidationError(
                f"Unsupported file type '{ext or content_type}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}."
            )
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size > max_bytes:
            raise ScanValidationError(
                f"File is too large ({size / (1024 * 1024):.1f} MB). "
                f"Maximum allowed is {settings.max_upload_size_mb} MB."
            )

    @staticmethod
    def read_image_bytes(data: bytes) -> np.ndarray:
        arr = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ScanValidationError("Corrupted or unreadable image data.")
        return image

    # ---------------- ingestion ----------------

    def create_scan(
        self,
        *,
        original_name: str,
        data: bytes,
        mission_id: Optional[int] = None,
        is_demo: bool = False,
        notes: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        depth_m: Optional[float] = None,
        region_label: Optional[str] = None,
    ) -> Scan:
        self.validate_upload(original_name, "", len(data))
        settings = get_settings()

        image = self.read_image_bytes(data)
        h, w = image.shape[:2]
        suffix = Path(original_name).suffix.lower() or ".png"
        stored_name = f"{secrets.token_hex(8)}_{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"
        stored_path = settings.upload_path / stored_name
        cv2.imwrite(str(stored_path), image)

        if mission_id is None:
            mission = self._default_mission()
        else:
            mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
            if mission is None:
                mission = self._default_mission()

        scan = Scan(
            scan_uid=f"SCN-{secrets.token_hex(5).upper()}",
            mission_id=mission.id,
            filename=stored_name,
            original_name=original_name,
            file_size=len(data),
            width=int(w),
            height=int(h),
            status="pending",
            is_demo=is_demo,
            notes=notes,
        )
        self.db.add(scan)
        self.db.flush()

        if latitude is not None and longitude is not None:
            loc = Location(
                scan_id=scan.id,
                latitude=latitude,
                longitude=longitude,
                depth_m=depth_m,
                region_label=region_label or GeoService.region_label_for(latitude, longitude),
                is_demo=is_demo,
            )
            self.db.add(loc)

        self.db.commit()
        self.db.refresh(scan)
        return scan

    def _default_mission(self) -> Mission:
        mission = self.db.query(Mission).order_by(Mission.id.asc()).first()
        if mission is None:
            mission = Mission(
                mission_id="DEMO-MISSION-001",
                name="Demo Coastal Survey",
                survey_area="Demo Region",
                operator="Demo Operator",
                description="Auto-created default mission for uploads without explicit mission selection.",
                status="active",
            )
            self.db.add(mission)
            self.db.flush()
        return mission

    # ---------------- analysis ----------------

    def analyze(self, scan_id: int) -> Scan:
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()
        if scan is None:
            raise ValueError(f"Scan {scan_id} not found.")

        scan.status = "processing"
        self.db.commit()

        try:
            settings = get_settings()
            stored_path = settings.upload_path / scan.filename
            image = cv2.imread(str(stored_path), cv2.IMREAD_COLOR)
            if image is None:
                raise ScanValidationError("Stored image could not be re-loaded.")
            predictions = self.engine.predict(image)

            detections = []
            all_dicts = []
            for p in predictions:
                all_dicts.append({
                    "x1": p.x1, "y1": p.y1, "x2": p.x2, "y2": p.y2,
                    "confidence": p.confidence, "area_ratio": p.area_ratio,
                    "is_anomaly": p.is_anomaly, "class_id": p.class_id,
                })

            for p in predictions:
                priority, reasons = compute_priority(
                    {
                        "x1": p.x1, "y1": p.y1, "x2": p.x2, "y2": p.y2,
                        "confidence": p.confidence, "area_ratio": p.area_ratio,
                        "is_anomaly": p.is_anomaly, "class_id": p.class_id,
                    },
                    all_dicts,
                    scan.width,
                    scan.height,
                )
                explanation = (p.explanation or "") + " " + " ".join(reasons)
                det = Detection(
                    scan_id=scan.id,
                    detection_uid=f"DET-{secrets.token_hex(5).upper()}",
                    class_id=p.class_id,
                    class_name=p.class_name,
                    confidence=p.confidence,
                    x1=p.x1, y1=p.y1, x2=p.x2, y2=p.y2,
                    width=(p.x2 - p.x1), height=(p.y2 - p.y1),
                    area_ratio=p.area_ratio,
                    is_anomaly=p.is_anomaly,
                    anomaly_score=p.anomaly_score,
                    priority=priority,
                    review_status="review" if p.is_anomaly else "pending",
                    explanation=explanation[:1200],
                )
                detections.append(det)

            # Remove any prior detections for this scan (re-analysis support).
            self.db.query(Detection).filter(Detection.scan_id == scan.id).delete()
            self.db.add_all(detections)
            if self.engine.is_demo:
                scan.status = "complete"
                if not detections:
                    logger.info(
                        "Scan %s processed without detections: "
                        "no trained model is configured.",
                        scan_id,
                    )
            else:
                scan.status = "complete"
            scan.status = "complete"
            self.db.commit()
            self.db.refresh(scan)
            return scan
        except Exception as exc:  # noqa: BLE001
            logger.exception("Analysis failed for scan %s: %s", scan_id, exc)
            scan.status = "failed"
            self.db.commit()
            raise

    # ---------------- queries ----------------

    def list_scans(self, mission_id: Optional[int] = None) -> list[Scan]:
        q = self.db.query(Scan)
        if mission_id is not None:
            q = q.filter(Scan.mission_id == mission_id)
        return q.order_by(Scan.created_at.desc()).all()

    def get_scan(self, scan_id: int) -> Optional[Scan]:
        return self.db.query(Scan).filter(Scan.id == scan_id).first()

    def get_scan_by_uid(self, scan_uid: str) -> Optional[Scan]:
        return self.db.query(Scan).filter(Scan.scan_uid == scan_uid).first()