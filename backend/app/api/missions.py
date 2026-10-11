"""Mission endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import scan_service
from app.models.database import get_db
from app.models.orm import Detection, Mission, Scan
from app.models.schemas import MissionOut
from app.services.scan_service import ScanService


router = APIRouter(prefix="/api/missions", tags=["missions"])


def _mission_to_dict(m: Mission, scans: list[Scan]) -> dict:
    detections: list[Detection] = []
    for s in scans:
        detections.extend(s.detections)
    return {
        "id": m.id,
        "mission_id": m.mission_id,
        "name": m.name,
        "survey_area": m.survey_area,
        "operator": m.operator,
        "description": m.description,
        "status": m.status,
        "date": m.date.isoformat() if m.date else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "scan_count": len(scans),
        "detection_count": len(detections),
        "high_priority_count": sum(1 for d in detections if d.priority == "high"),
    }


@router.get("")
def list_missions(db: Session = Depends(get_db)) -> list[dict]:
    missions = db.query(Mission).order_by(Mission.created_at.desc()).all()
    out = []
    for m in missions:
        scans = db.query(Scan).filter(Scan.mission_id == m.id).all()
        out.append(_mission_to_dict(m, scans))
    return out


@router.get("/{mission_id}")
def get_mission(mission_id: int, db: Session = Depends(get_db)) -> dict:
    m = db.query(Mission).filter(Mission.id == mission_id).first()
    if m is None:
        raise HTTPException(status_code=404, detail="Mission not found.")
    scans = db.query(Scan).filter(Scan.mission_id == m.id).all()
    return _mission_to_dict(m, scans)


@router.post("")
def create_mission(payload: dict, db: Session = Depends(get_db)) -> dict:
    required = {"mission_id", "name"}
    if not required.issubset(set(payload.keys())):
        raise HTTPException(status_code=400, detail="mission_id and name are required.")
    existing = db.query(Mission).filter(Mission.mission_id == payload["mission_id"]).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Mission with that mission_id already exists.")
    m = Mission(
        mission_id=str(payload["mission_id"]),
        name=str(payload["name"]),
        survey_area=payload.get("survey_area"),
        operator=payload.get("operator"),
        description=payload.get("description"),
        status=payload.get("status", "active"),
        date=datetime.now(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _mission_to_dict(m, [])