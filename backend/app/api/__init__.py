"""API routers."""
from app.api.scans import router as scans_router
from app.api.detections import router as detections_router
from app.api.missions import router as missions_router
from app.api.analytics import router as analytics_router
from app.api.hotspots import router as hotspots_router
from app.api.reports import router as reports_router
from app.api.reviews import router as reviews_router
from app.api.system import router as system_router
from app.api.auth import router as auth_router

__all__ = [
    "scans_router",
    "detections_router",
    "missions_router",
    "analytics_router",
    "hotspots_router",
    "reports_router",
    "reviews_router",
    "system_router",
    "auth_router",
]