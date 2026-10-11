"""Idempotent seeding routine used by the demo data script."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from app.models.database import init_db, session_scope
from app.models.orm import ModelVersion, Mission, User


logger = logging.getLogger(__name__)


def ensure_base_data() -> None:
    """Create base missions + the default model registry row if missing."""
    init_db()
    with session_scope() as db:
        # Default admin and operator users — passwords are intentionally trivial
        # for the demo. Production deployments must rotate them.
        if db.query(User).count() == 0:
            from app.utils.security import hash_password

            db.add(User(
                username="admin",
                email="admin@oceanguard.example",
                full_name="OceanGuard Admin",
                role="admin",
                hashed_password=hash_password("admin123"),
                is_active=True,
            ))
            db.add(User(
                username="demo-operator",
                email="demo@oceanguard.example",
                full_name="Demo Operator",
                role="operator",
                hashed_password=hash_password("demo123"),
                is_active=True,
            ))

        # Default mission.
        if db.query(Mission).count() == 0:
            db.add(Mission(
                mission_id="ARABIAN-SEA-DEMO-001",
                name="Demo Coastal Survey",
                survey_area="Demo Region (Synthetic Coordinates)",
                operator="Demo Operator",
                description=(
                    "Synthetic demonstration mission for the OceanGuard AI prototype. "
                    "Coordinates and detections are generated for demonstration only "
                    "and do not represent real survey data."
                ),
                status="active",
                date=datetime.now(),
            ))
            db.add(Mission(
                mission_id="INDIAN-OCEAN-DEMO-002",
                name="Demo Deep-water Survey",
                survey_area="Demo Region (Synthetic Coordinates)",
                operator="Demo Operator",
                description="Second demonstration mission used for multi-mission analytics.",
                status="active",
                date=datetime.now(),
            ))

        # Model registry entry (no fabricated metrics).
        if db.query(ModelVersion).count() == 0:
            db.add(ModelVersion(
                name="OceanGuard-YOLO-v1",
                version="1.0",
                model_type="yolov8-demo",
                path="./ml/models/sonar_debris.pt",
                dataset="Demo / Synthetic / Research Dataset",
                status="demo",
                description=(
                    "Demo entry. Replace with a real trained model to enable production "
                    "inference. Evaluation metrics are unavailable for this demo model "
                    "and have not been fabricated."
                ),
            ))
    logger.info("Base seed data ready.")