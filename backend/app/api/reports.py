"""Report generation endpoints."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import report_service
from app.services.report_service import ReportService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/missions/{mission_id}")
def generate_mission_report(mission_id: int, service: ReportService = Depends(report_service)) -> dict:
    try:
        record = service.generate_mission_report(mission_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "id": record.id,
        "mission_id": record.mission_id,
        "filename": record.filename,
        "file_path": record.file_path,
        "generated_by": record.generated_by,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.get("")
def list_reports(mission_id: int | None = None, service: ReportService = Depends(report_service)) -> list[dict]:
    records = service.list_reports(mission_id=mission_id)
    return [
        {
            "id": r.id,
            "mission_id": r.mission_id,
            "filename": r.filename,
            "file_path": r.file_path,
            "generated_by": r.generated_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/{report_id}/download")
def download_report(report_id: int, service: ReportService = Depends(report_service)):
    records = service.list_reports()
    target = next((r for r in records if r.id == report_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    path = Path(target.file_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Report file no longer available on disk.")
    return FileResponse(str(path), media_type="application/pdf", filename=target.filename)