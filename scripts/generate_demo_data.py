"""Demo data generator.

Creates synthetic side-scan sonar-like images and seeds the database with
missions, scans, locations, detections and reviews. Generated content is
explicitly labelled as DEMO DATA in the UI.

Usage:
    python scripts/generate_demo_data.py            # regenerate
    python scripts/generate_demo_data.py --clear    # reset DB first
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np

# Make backend imports work when running this script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database.seed import ensure_base_data  # noqa: E402
from app.models.database import init_db, session_scope  # noqa: E402
from app.models.orm import (  # noqa: E402
    Anomaly,
    Detection,
    Location,
    Mission,
    Review,
    Scan,
)
from app.services.priority_engine import compute_priority  # noqa: E402
from app.utils.config import get_settings  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seed")


CLASS_PALETTE = [
    ("Marine Debris", (90, 200, 90)),
    ("Fishing Net", (60, 90, 230)),
    ("Plastic Debris", (200, 200, 60)),
    ("Metal Object", (40, 40, 220)),
    ("Man-made Object", (200, 90, 200)),
    ("Unknown Anomaly", (40, 200, 230)),
]


def _generate_sonar_image(width: int = 960, height: int = 540, *, seed: int) -> tuple[np.ndarray, list[dict]]:
    """Generate a synthetic side-scan sonar-like image with embedded 'objects'."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    # Background: noise + water-column gradient + seafloor return.
    noise = np_rng.normal(loc=8, scale=14, size=(height, width)).astype(np.float32)
    gradient = np.linspace(0, 30, height, dtype=np.float32).reshape(-1, 1)
    seafloor = np.zeros_like(noise)
    seafloor[int(height * 0.85):, :] = np_rng.normal(30, 6, size=(height - int(height * 0.85), width))

    img = noise + gradient + seafloor
    img = np.clip(img, 0, 255).astype(np.uint8)

    # Light horizontal scan lines (typical of side-scan water column).
    line = (np.sin(np.linspace(0, 4 * np.pi, width)) * 4 + 6).astype(np.uint8)
    for y in range(0, height, 5):
        img[y, :] = np.clip(img[y, :].astype(np.int16) + line, 0, 255).astype(np.uint8)

    # Vertical acoustic shadow band (nadir).
    nadir_w = max(4, width // 80)
    img[:, width // 2 - nadir_w // 2:width // 2 + nadir_w // 2] = np.clip(
        img[:, width // 2 - nadir_w // 2:width // 2 + nadir_w // 2].astype(np.int16) - 12, 0, 255
    ).astype(np.uint8)

    objects = []
    obj_count = rng.randint(3, 6)
    classes = list(range(len(CLASS_PALETTE)))
    rng.shuffle(classes)
    for idx in range(obj_count):
        cls_id = classes[idx % len(classes)]
        cls_name, color_bgr = CLASS_PALETTE[cls_id]
        # Object footprint.
        bw = rng.randint(int(width * 0.05), int(width * 0.16))
        bh = rng.randint(int(height * 0.04), int(height * 0.10))
        x = rng.randint(int(width * 0.08), max(int(width * 0.08), width - bw - 1))
        y = rng.randint(int(height * 0.30), max(int(height * 0.30), height - int(height * 0.18) - bh))

        # Draw a soft elliptical highlight + acoustic shadow (the side-scan signature).
        overlay = img.copy()
        center = (x + bw // 2, y + bh // 2)
        axes = (bw // 2, bh // 2)
        cv2.ellipse(overlay, center, axes, rng.uniform(-25, 25), 0, 360, color_bgr, -1)
        alpha = rng.uniform(0.55, 0.85)
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        # Shadow trail to the right (or left) of the highlight.
        sx = x + bw + rng.randint(2, 6)
        sy = y + rng.randint(0, max(1, bh // 4))
        sh_w = rng.randint(int(bw * 0.7), int(bw * 1.4))
        sh_h = max(2, bh // rng.randint(2, 4))
        cv2.rectangle(img, (sx, sy), (sx + sh_w, sy + sh_h), (10, 10, 10), -1)

        objects.append({
            "class_id": cls_id,
            "class_name": cls_name,
            "x1": float(x), "y1": float(y),
            "x2": float(x + bw), "y2": float(y + bh),
            "width": float(bw), "height": float(bh),
            "confidence": round(rng.uniform(0.65, 0.96), 4),
            "is_anomaly": cls_name == "Unknown Anomaly",
            "anomaly_score": round(rng.uniform(0.70, 0.92), 4) if cls_name == "Unknown Anomaly" else round(rng.uniform(0.05, 0.35), 4),
        })

    return img, objects


def _save_image(img: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)


def clear_database() -> None:
    with session_scope() as db:
        for cls in [Review, Anomaly, Detection, Location, Scan, Mission]:
            db.query(cls).delete()
    logger.info("Existing data cleared.")


def seed_database(image_dir: Path, scan_count: int = 8) -> None:
    settings = get_settings()
    image_dir.mkdir(parents=True, exist_ok=True)

    # Files are written to image_dir, but the scan DB stores `filename` so the
    # FastAPI image endpoints can serve them via `settings.upload_path / filename`.
    # Therefore the stored filename must be RELATIVE to settings.upload_path.
    upload_root = settings.upload_path
    try:
        relative_subdir = image_dir.relative_to(upload_root)
    except ValueError:
        # image_dir is outside upload_path (e.g. ./data/demo in legacy runs);
        # in that case fall back to storing just the basename, which won't be
        # served correctly — caller should re-run with --out uploads/demo.
        relative_subdir = None
    if relative_subdir and str(relative_subdir) not in (".", ""):
        prefix = str(relative_subdir).replace("\\", "/") + "/"
    else:
        prefix = ""

    # Reset prior demo data so the script is idempotent.
    clear_database()
    ensure_base_data()

    # Create a fresh mission if no missions exist.
    with session_scope() as db:
        missions = db.query(Mission).all()
        if not missions:
            missions = [
                Mission(
                    mission_id="DEMO-MISSION-001",
                    name="Demo Coastal Survey",
                    survey_area="Demo Region",
                    operator="Demo Operator",
                    status="active",
                )
            ]
            db.add_all(missions)
            db.flush()
            missions = db.query(Mission).all()

        mission_pool = missions

        # Pre-defined scan configurations to give the UI a believable shape.
        scan_configs = []
        base_time = datetime.now() - timedelta(days=14)
        for i in range(scan_count):
            mission = mission_pool[i % len(mission_pool)]
            lat = 18.5 + (i % 4) * 0.4 + random.uniform(-0.05, 0.05)
            lon = 65.0 + (i // 4) * 0.6 + random.uniform(-0.05, 0.05)
            ts = base_time + timedelta(days=i, hours=random.randint(0, 23))
            scan_configs.append((mission, lat, lon, ts, i))

        scan_records = []
        for mission, lat, lon, ts, i in scan_configs:
            filename = f"demo_scan_{i + 1:03d}.png"
            stored = f"demo_{secrets.token_hex(6)}_{filename}"
            image_path = image_dir / stored
            img, objects = _generate_sonar_image(seed=1000 + i)
            _save_image(img, image_path)
            # Store path relative to upload_path so the API can find it.
            stored_for_db = prefix + stored if prefix else stored

            scan = Scan(
                scan_uid=f"SCN-{secrets.token_hex(5).upper()}",
                mission_id=mission.id,
                filename=stored_for_db,
                original_name=filename,
                file_size=image_path.stat().st_size,
                width=img.shape[1],
                height=img.shape[0],
                status="complete",
                is_demo=True,
                timestamp=ts,
                created_at=ts,
                notes="DEMO DATA — generated by scripts/generate_demo_data.py.",
            )
            db.add(scan)
            db.flush()

            db.add(Location(
                scan_id=scan.id,
                latitude=lat,
                longitude=lon,
                depth_m=random.uniform(15, 90),
                region_label=f"R{1000 + i}",
                is_demo=True,
            ))

            # Convert objects to Detection rows.
            img_area = img.shape[0] * img.shape[1]
            det_dicts = []
            for obj in objects:
                area_ratio = (obj["width"] * obj["height"]) / img_area
                is_anom = obj["is_anomaly"]
                det_dicts.append({
                    "x1": obj["x1"], "y1": obj["y1"], "x2": obj["x2"], "y2": obj["y2"],
                    "confidence": obj["confidence"], "area_ratio": area_ratio,
                    "is_anomaly": is_anom, "class_id": obj["class_id"],
                })

            for obj in objects:
                priority, reasons = compute_priority(
                    {
                        "x1": obj["x1"], "y1": obj["y1"], "x2": obj["x2"], "y2": obj["y2"],
                        "confidence": obj["confidence"], "area_ratio": (obj["width"] * obj["height"]) / img_area,
                        "is_anomaly": obj["is_anomaly"], "class_id": obj["class_id"],
                    },
                    det_dicts,
                    img.shape[1],
                    img.shape[0],
                )
                explanation = (
                    f"Detected object has visual characteristics consistent with '{obj['class_name']}' "
                    f"(confidence {obj['confidence']:.0%}). Reasons: {'; '.join(reasons)}"
                )
                review_status = "review" if obj["is_anomaly"] else "pending"
                if random.random() < 0.25 and not obj["is_anomaly"]:
                    review_status = random.choice(["approved", "rejected"])

                det = Detection(
                    scan_id=scan.id,
                    detection_uid=f"DET-{secrets.token_hex(5).upper()}",
                    class_id=obj["class_id"],
                    class_name=obj["class_name"],
                    confidence=obj["confidence"],
                    x1=obj["x1"], y1=obj["y1"], x2=obj["x2"], y2=obj["y2"],
                    width=obj["width"], height=obj["height"],
                    area_ratio=(obj["width"] * obj["height"]) / img_area,
                    is_anomaly=obj["is_anomaly"],
                    anomaly_score=obj["anomaly_score"],
                    priority=priority,
                    review_status=review_status,
                    explanation=explanation,
                    reviewer_comment=(
                        "Confirmed by demo operator." if review_status == "approved"
                        else "Rejected — likely seafloor return." if review_status == "rejected"
                        else None
                    ),
                )
                db.add(det)
                db.flush()  # ensure det.id is populated for the FK on Review / Anomaly

                if obj["is_anomaly"]:
                    db.add(Anomaly(
                        scan_id=scan.id,
                        detection_id=det.id,
                        anomaly_score=obj["anomaly_score"],
                        method="demo+content+edge+contrast",
                        description=(
                            "Region differs significantly from typical background patterns. "
                            "Manual inspection recommended."
                        ),
                        region_label=f"R{1000 + i}",
                    ))

                if review_status != "pending":
                    db.add(Review(
                        detection_id=det.id,
                        reviewer="demo-operator",
                        decision=review_status,
                        comment=det.reviewer_comment,
                    ))
            scan_records.append(scan)

    logger.info("Demo database seeded with %d scans, %d missions.",
                len(scan_records), len(mission_pool))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo data for OceanGuard AI.")
    parser.add_argument("--clear", action="store_true", help="Clear existing demo data first.")
    parser.add_argument("--scans", type=int, default=8, help="Number of scans to create.")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Image output directory. Defaults to <upload_path>/demo so the API can serve them.",
    )
    args = parser.parse_args()

    settings = get_settings()
    project_root = Path(__file__).resolve().parents[1]

    if args.out:
        out_dir = (project_root / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    else:
        # Default: write into a "demo" subdirectory of the configured upload
        # directory so demo images are clearly separated from real uploads.
        out_dir = settings.upload_path / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    init_db()
    if args.clear:
        clear_database()
    seed_database(out_dir, scan_count=args.scans)
    logger.info("Demo data is ready at %s", out_dir)


if __name__ == "__main__":
    main()