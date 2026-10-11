"""Pydantic schemas for API request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Globally allow fields whose names start with "model_" so we can use
# `model_type`, `model_name`, `model_version` etc. without namespace warnings.
_PYDANTIC_CONFIG = ConfigDict(protected_namespaces=(), from_attributes=True)


# ===== Mission =====

class MissionBase(BaseModel):
    model_config = _PYDANTIC_CONFIG
    mission_id: str
    name: str
    survey_area: Optional[str] = None
    operator: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    date: Optional[datetime] = None


class MissionCreate(MissionBase):
    model_config = _PYDANTIC_CONFIG
    pass


class MissionOut(MissionBase):
    model_config = _PYDANTIC_CONFIG
    id: int
    scan_count: int = 0
    detection_count: int = 0
    high_priority_count: int = 0
    created_at: datetime



# ===== Location =====

class LocationOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    depth_m: Optional[float] = None
    region_label: Optional[str] = None
    is_demo: bool = True



# ===== Scan =====

class ScanBase(BaseModel):
    model_config = _PYDANTIC_CONFIG
    original_name: str
    is_demo: bool = True
    notes: Optional[str] = None


class ScanOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    id: int
    scan_uid: str
    mission_id: int
    filename: str
    original_name: str
    file_size: int
    width: int
    height: int
    status: str
    is_demo: bool
    notes: Optional[str] = None
    timestamp: datetime
    created_at: datetime
    location: Optional[LocationOut] = None
    detection_count: int = 0
    anomaly_count: int = 0
    high_priority_count: int = 0



class ScanDetail(ScanOut):
    model_config = _PYDANTIC_CONFIG
    detections: list["DetectionOut"] = []


# ===== Detection =====

class DetectionBase(BaseModel):
    model_config = _PYDANTIC_CONFIG
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    id: int
    scan_id: int
    detection_uid: str
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float
    area_ratio: float
    is_anomaly: bool
    anomaly_score: float
    priority: str
    review_status: str
    reviewer_comment: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime



# ===== Reviews =====

class ReviewCreate(BaseModel):
    model_config = _PYDANTIC_CONFIG
    decision: str = Field(..., pattern="^(approved|rejected|review)$")
    reviewer: str = "operator"
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    id: int
    detection_id: int
    reviewer: str
    decision: str
    comment: Optional[str] = None
    created_at: datetime



# ===== Analytics =====

class AnalyticsSummary(BaseModel):
    model_config = _PYDANTIC_CONFIG
    total_scans: int
    total_detections: int
    total_missions: int
    debris_count: int
    anomaly_count: int
    high_priority_count: int
    avg_confidence: float
    class_distribution: dict
    priority_distribution: dict
    anomaly_trend: list
    confidence_buckets: list


# ===== Hotspot =====

class HotspotOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    region_label: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    detection_count: int
    anomaly_count: int
    avg_confidence: float
    risk_level: str


# ===== Compare =====

class CompareRequest(BaseModel):
    model_config = _PYDANTIC_CONFIG
    scan_a_id: int
    scan_b_id: int


class CompareResult(BaseModel):
    model_config = _PYDANTIC_CONFIG
    scan_a_id: int
    scan_b_id: int
    persistent: int
    new_detections: int
    removed: int
    changed_regions: int
    notes: list[str]


# ===== Report =====

class ReportOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    id: int
    mission_id: int
    filename: str
    file_path: str
    generated_by: str
    created_at: datetime



# ===== Models registry =====

class ModelVersionOut(BaseModel):
    model_config = _PYDANTIC_CONFIG
    id: int
    name: str
    version: str
    model_type: str
    path: str
    dataset: Optional[str] = None
    training_date: Optional[datetime] = None
    metrics_json: Optional[str] = None
    status: str
    description: Optional[str] = None
    created_at: datetime



# ===== Settings / Info =====

class SystemInfo(BaseModel):
    model_config = _PYDANTIC_CONFIG
    app_name: str
    app_env: str
    model_name: str
    model_version: str
    model_type: str
    confidence_threshold: float
    iou_threshold: float
    anomaly_threshold: float
    demo_mode: bool
    dataset_label: str
    classes: dict
    disclaimer: str


ScanDetail.model_rebuild()