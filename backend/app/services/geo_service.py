"""Geospatial helpers: region labeling, hotspots, geocoding-free aggregation."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.orm import Detection, Location, Scan


class GeoService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------------- region labels ----------------

    @staticmethod
    def region_label_for(latitude: float, longitude: float) -> str:
        # Compute a coarse 0.5° tile id for grouping.
        lat_idx = math.floor(latitude / 0.5)
        lon_idx = math.floor(longitude / 0.5)
        return f"R{abs(lat_idx) * 100 + abs(lon_idx):04d}"

    # ---------------- hotspots ----------------

    def hotspots(self) -> list[dict]:
        """Aggregate per region: detection_count, anomaly_count, avg_confidence, risk_level."""
        # Join detections -> scan -> location.
        rows = (
            self.db.query(Detection, Scan, Location)
            .join(Scan, Detection.scan_id == Scan.id)
            .join(Location, Location.scan_id == Scan.id)
            .all()
        )
        grouped: dict[str, dict] = defaultdict(lambda: {
            "region_label": "",
            "latitude": None,
            "longitude": None,
            "detection_count": 0,
            "anomaly_count": 0,
            "high_count": 0,
            "_conf_sum": 0.0,
        })
        for det, _scan, loc in rows:
            key = loc.region_label or self.region_label_for(loc.latitude or 0.0, loc.longitude or 0.0)
            entry = grouped[key]
            entry["region_label"] = loc.region_label or key
            entry["latitude"] = loc.latitude
            entry["longitude"] = loc.longitude
            entry["detection_count"] += 1
            if det.is_anomaly:
                entry["anomaly_count"] += 1
            if det.priority == "high":
                entry["high_count"] += 1
            entry["_conf_sum"] += det.confidence

        out: list[dict] = []
        for entry in grouped.values():
            count = entry["detection_count"]
            avg_conf = entry["_conf_sum"] / count if count else 0.0
            risk = "low"
            if entry["high_count"] >= 2 or entry["anomaly_count"] >= 2 or count >= 12:
                risk = "high"
            elif entry["high_count"] >= 1 or entry["anomaly_count"] >= 1 or count >= 5:
                risk = "medium"
            out.append({
                "region_label": entry["region_label"],
                "latitude": entry["latitude"],
                "longitude": entry["longitude"],
                "detection_count": count,
                "anomaly_count": entry["anomaly_count"],
                "avg_confidence": round(avg_conf, 4),
                "risk_level": risk,
            })
        out.sort(key=lambda e: e["detection_count"], reverse=True)
        return out

    def nearest_scan(self, latitude: float, longitude: float) -> Optional[dict]:
        """Return the closest scan by simple great-circle distance."""
        locations = self.db.query(Location, Scan).join(Scan, Location.scan_id == Scan.id).all()
        best = None
        best_d = math.inf
        for loc, scan in locations:
            if loc.latitude is None or loc.longitude is None:
                continue
            d = math.hypot(loc.latitude - latitude, loc.longitude - longitude)
            if d < best_d:
                best_d = d
                best = scan
        return None if best is None else {"scan_id": best.id, "scan_uid": best.scan_uid, "distance_deg": best_d}