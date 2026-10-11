"""System info, model registry, settings."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ml.inference import get_inference_engine
from app.models.database import get_db
from app.models.orm import ModelVersion
from app.utils.config import get_settings, load_classes_config


router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system/info")
def system_info() -> dict:
    settings = get_settings()
    engine = get_inference_engine()
    classes_cfg = load_classes_config()
    classes = {}
    for cid, meta in classes_cfg.get("classes", {}).items():
        classes[int(cid)] = meta
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "model_name": engine.bundle.name,
        "model_version": engine.bundle.version,
        "model_type": engine.bundle.model_type,
        "model_path": str(engine.bundle.path),
        "is_real_model": engine.bundle.is_real,
        "confidence_threshold": settings.confidence_threshold,
        "iou_threshold": settings.iou_threshold,
        "anomaly_threshold": settings.anomaly_threshold,
        "demo_mode": settings.enable_demo_mode,
        "dataset_label": "Demo / Synthetic / Research Dataset" if engine.is_demo else "Configured Dataset",
        "classes": classes,
        "priority_rules": classes_cfg.get("priority_rules", {}),
        "disclaimer": (
            "DEMO INFERENCE — NOT A VALIDATED DEPLOYMENT MODEL unless a real trained "
            "model is configured. Predictions are decision-support outputs and should be "
            "independently verified by qualified personnel."
        ),
    }


@router.get("/models")
def list_models(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "version": r.version,
            "model_type": r.model_type,
            "path": r.path,
            "dataset": r.dataset,
            "training_date": r.training_date.isoformat() if r.training_date else None,
            "metrics_json": r.metrics_json,
            "status": r.status,
            "description": r.description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


class ModelRegisterIn(BaseModel):
    name: str
    version: str
    model_type: str
    path: str
    dataset: Optional[str] = None
    training_date: Optional[datetime] = None
    metrics_json: Optional[str] = None
    status: str = "demo"
    description: Optional[str] = None


@router.post("/models")
def register_model(payload: ModelRegisterIn, db: Session = Depends(get_db)) -> dict:
    row = ModelVersion(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "version": row.version, "status": row.status}