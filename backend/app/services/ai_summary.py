"""AI Insight: deterministic, conservative scan & mission summaries."""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from app.models.orm import Detection, Scan, Mission


DISCLAIMER = (
    "AI-generated detections are decision-support outputs and should be "
    "independently verified by qualified personnel."
)


def _safe_list(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def generate_scan_summary(scan: Scan, detections: Iterable[Detection]) -> dict:
    detections = list(detections)
    total = len(detections)
    class_counter = Counter(d.class_name for d in detections)
    anomaly_count = sum(1 for d in detections if d.is_anomaly)
    high_count = sum(1 for d in detections if d.priority == "high")
    avg_conf = sum(d.confidence for d in detections) / total if total else 0.0

    classes_top = class_counter.most_common(3)
    clustered = total >= 3
    headline = (
        f"{total} potential object{'s were' if total != 1 else ' was'} detected in this scan."
        if total else
        "No objects were detected in this scan. This does not imply that the area is free of debris."
    )

    findings: list[str] = []
    if high_count:
        findings.append(f"{high_count} high-confidence detection{'s' if high_count != 1 else ''} that warrant priority review.")
    for cls, count in classes_top:
        findings.append(f"{count} detection{'s' if count != 1 else ''} consistent with '{cls}'.")
    if anomaly_count:
        findings.append(f"{anomaly_count} unknown region{'s' if anomaly_count != 1 else ''} flagged as anomalies and require human review.")
    if clustered:
        findings.append("Multiple detections appear spatially clustered within this survey region.")
    if not findings:
        findings.append("No significant findings produced by the AI model on this scan.")

    return {
        "headline": headline,
        "findings": findings,
        "metrics": {
            "total_detections": total,
            "anomaly_count": anomaly_count,
            "high_priority_count": high_count,
            "avg_confidence": round(avg_conf, 4),
            "top_classes": [{"class_name": c, "count": n} for c, n in classes_top],
        },
        "disclaimer": DISCLAIMER,
    }


def generate_mission_summary(mission: Mission, scans: Iterable[Scan]) -> dict:
    scans = list(scans)
    scan_count = len(scans)
    total_detections = sum(len(s.detections) for s in scans)
    anomalies = sum(sum(1 for d in s.detections if d.is_anomaly) for s in scans)
    high = sum(sum(1 for d in s.detections if d.priority == "high") for s in scans)
    avg_conf = 0.0
    if total_detections:
        all_d = [d for s in scans for d in s.detections]
        avg_conf = sum(d.confidence for d in all_d) / len(all_d)

    headline = (
        f"Mission '{mission.name}' includes {scan_count} scan{'s' if scan_count != 1 else ''} "
        f"with {total_detections} AI detection{'s' if total_detections != 1 else ''}."
    )
    findings = [
        f"{high} high-AI-assisted-review-priority detection{'s' if high != 1 else ''} identified." if high else
        "No high-AI-assisted-review-priority detections produced.",
        f"{anomalies} anomaly review entr{'ies' if anomalies != 1 else 'y'} require operator attention." if anomalies else
        "No anomalies were flagged across scans.",
        "Average AI confidence across scans: {:.0%}.".format(avg_conf),
    ]
    return {
        "headline": headline,
        "findings": findings,
        "metrics": {
            "scan_count": scan_count,
            "total_detections": total_detections,
            "high_priority_count": high,
            "anomaly_count": anomalies,
            "avg_confidence": round(avg_conf, 4),
        },
        "disclaimer": DISCLAIMER,
    }