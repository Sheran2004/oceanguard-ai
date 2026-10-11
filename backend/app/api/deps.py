"""Common API dependencies."""
from __future__ import annotations

from typing import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.scan_service import ScanService
from app.services.detection_service import DetectionService
from app.services.geo_service import GeoService
from app.services.report_service import ReportService
from app.services.anomaly_service import AnomalyService


def scan_service(db: Session = Depends(get_db)) -> ScanService:
    return ScanService(db)


def detection_service(db: Session = Depends(get_db)) -> DetectionService:
    return DetectionService(db)


def geo_service(db: Session = Depends(get_db)) -> GeoService:
    return GeoService(db)


def report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


def anomaly_service(db: Session = Depends(get_db)) -> AnomalyService:
    return AnomalyService(db)