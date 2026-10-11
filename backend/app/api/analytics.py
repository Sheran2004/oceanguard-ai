"""Analytics endpoint."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.orm import Detection, Scan


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _split_by_demo(detections: list[Detection], scans: list[Scan]) -> dict:
    """Return a separate real-vs-demo aggregate so the UI can show both."""
    scan_is_demo = {s.id: s.is_demo for s in scans}
    real_scans = [s for s in scans if not s.is_demo]
    demo_scans = [s for s in scans if s.is_demo]
    real_dets = [d for d in detections if not scan_is_demo.get(d.scan_id, True)]
    demo_dets = [d for d in detections if scan_is_demo.get(d.scan_id, True)]

    def _agg(scan_list, det_list):
        if not det_list:
            return {"scans": len(scan_list), "detections": 0, "anomalies": 0, "high": 0,
                    "avg_confidence": 0.0}
        avg = sum(d.confidence for d in det_list) / len(det_list)
        return {
            "scans": len(scan_list),
            "detections": len(det_list),
            "anomalies": sum(1 for d in det_list if d.is_anomaly),
            "high": sum(1 for d in det_list if d.priority == "high"),
            "avg_confidence": round(avg, 4),
        }

    return {"real": _agg(real_scans, real_dets), "demo": _agg(demo_scans, demo_dets)}


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db), include_demo: bool = True) -> dict:
    """Aggregate analytics. By default includes demo data with clear labels.

    Set include_demo=false to get ONLY real user-uploaded data — useful when
    the user wants to see operational numbers without the demo noise.
    """
    all_scans = db.query(Scan).all()
    if include_demo:
        scans = all_scans
    else:
        scans = [s for s in all_scans if not s.is_demo]

    scan_ids = {s.id for s in scans}
    detections = [d for d in db.query(Detection).all() if d.scan_id in scan_ids]
    total_detections = len(detections)
    avg_conf = sum(d.confidence for d in detections) / total_detections if total_detections else 0.0
    class_counter = Counter(d.class_name for d in detections)
    priority_counter = Counter(d.priority for d in detections)
    anomaly_count = sum(1 for d in detections if d.is_anomaly)
    high = sum(1 for d in detections if d.priority == "high")

    # Confidence buckets.
    buckets = [
        ("0.0-0.2", 0), ("0.2-0.4", 0), ("0.4-0.6", 0), ("0.6-0.8", 0), ("0.8-1.0", 0),
    ]
    for d in detections:
        c = d.confidence
        if c < 0.2:
            buckets[0] = (buckets[0][0], buckets[0][1] + 1)
        elif c < 0.4:
            buckets[1] = (buckets[1][0], buckets[1][1] + 1)
        elif c < 0.6:
            buckets[2] = (buckets[2][0], buckets[2][1] + 1)
        elif c < 0.8:
            buckets[3] = (buckets[3][0], buckets[3][1] + 1)
        else:
            buckets[4] = (buckets[4][0], buckets[4][1] + 1)

    # Anomaly / detection trend (last 14 days).
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    trend = []
    by_day: dict = defaultdict(lambda: {"detections": 0, "anomalies": 0})
    for d in detections:
        if d.created_at is None:
            continue
        key = d.created_at.date()
        by_day[key]["detections"] += 1
        if d.is_anomaly:
            by_day[key]["anomalies"] += 1
    for day in days:
        trend.append({
            "date": day.isoformat(),
            "detections": by_day[day]["detections"],
            "anomalies": by_day[day]["anomalies"],
        })

    # Real-vs-demo split is computed against the WHOLE dataset, not the
    # filtered one, so the UI can always tell the user how much is real.
    split = _split_by_demo(db.query(Detection).all(), all_scans)

    return {
        "total_scans": len(scans),
        "total_detections": total_detections,
        "total_missions": len({s.mission_id for s in scans}),
        "debris_count": sum(1 for d in detections if d.class_name in {
            "Marine Debris", "Plastic Debris", "Fishing Net",
        }),
        "anomaly_count": anomaly_count,
        "high_priority_count": high,
        "avg_confidence": round(avg_conf, 4),
        "class_distribution": dict(class_counter),
        "priority_distribution": dict(priority_counter),
        "anomaly_trend": trend,
        "confidence_buckets": [{"range": k, "count": v} for k, v in buckets],
        "real_vs_demo": split,
        "data_source": "real+demo" if include_demo else "real-only",
    }


@router.get("/timeline")
def timeline(db: Session = Depends(get_db)) -> list[dict]:
    """Per-scan detection count timeline."""
    scans = db.query(Scan).order_by(Scan.created_at.asc()).all()
    out = []
    for s in scans:
        out.append({
            "scan_id": s.id,
            "scan_uid": s.scan_uid,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "detections": len(s.detections),
            "anomalies": sum(1 for d in s.detections if d.is_anomaly),
        })
    return out