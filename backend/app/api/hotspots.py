"""Hotspots endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import geo_service
from app.services.geo_service import GeoService


router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])


@router.get("")
def get_hotspots(geo: GeoService = Depends(geo_service)) -> list[dict]:
    return geo.hotspots()