"""PDF report generation using ReportLab."""
from __future__ import annotations

import io
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.models.orm import Detection, Mission, Report, Scan
from app.services.ai_summary import DISCLAIMER, generate_mission_summary
from app.utils.config import get_settings


logger = logging.getLogger(__name__)


PRIORITY_COLORS = {
    "high": colors.HexColor("#dc2626"),
    "medium": colors.HexColor("#d97706"),
    "low": colors.HexColor("#16a34a"),
    "review": colors.HexColor("#7c3aed"),
}


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_mission_report(self, mission_id: int, generated_by: str = "system") -> Report:
        mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
        if mission is None:
            raise ValueError(f"Mission {mission_id} not found.")
        settings = get_settings()
        scans = (
            self.db.query(Scan)
            .filter(Scan.mission_id == mission_id)
            .order_by(Scan.created_at.asc())
            .all()
        )
        summary = generate_mission_summary(mission, scans)

        filename = f"mission_report_{mission.mission_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = settings.report_path / filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            title=f"OceanGuard AI Report - {mission.name}",
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        h1 = styles["Heading1"]
        h2 = styles["Heading2"]
        h3 = styles["Heading3"]
        body = styles["BodyText"]
        body.fontSize = 10
        body.leading = 14

        flow = []
        # Header
        flow.append(Paragraph("OceanGuard AI — Mission Analysis Report", h1))
        flow.append(Paragraph(
            f"<b>Mission:</b> {mission.name}<br/>"
            f"<b>Mission ID:</b> {mission.mission_id}<br/>"
            f"<b>Survey Area:</b> {mission.survey_area or 'N/A'}<br/>"
            f"<b>Operator:</b> {mission.operator or 'N/A'}<br/>"
            f"<b>Status:</b> {mission.status}<br/>"
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
            body,
        ))
        flow.append(Spacer(1, 0.4 * cm))

        # AI Insight
        flow.append(Paragraph("AI Insight", h2))
        flow.append(Paragraph(summary["headline"], body))
        for f in summary["findings"]:
            flow.append(Paragraph(f"&bull; {f}", body))
        flow.append(Spacer(1, 0.4 * cm))

        # Metrics table
        m_table = Table(
            [
                ["Metric", "Value"],
                ["Scan Count", str(summary["metrics"]["scan_count"])],
                ["Total Detections", str(summary["metrics"]["total_detections"])],
                ["High AI-Assisted Review Priority", str(summary["metrics"]["high_priority_count"])],
                ["Anomalies", str(summary["metrics"]["anomaly_count"])],
                ["Average Confidence", f"{summary['metrics']['avg_confidence']:.0%}"],
            ],
            colWidths=[7 * cm, 8 * cm],
        )
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ]))
        flow.append(m_table)
        flow.append(Spacer(1, 0.4 * cm))

        # Scans section
        flow.append(Paragraph("Scans in Mission", h2))
        # Compute real vs demo breakdown for this mission.
        real_scans = [s for s in scans if not s.is_demo]
        demo_scans = [s for s in scans if s.is_demo]
        real_dets = [d for s in real_scans for d in s.detections]
        demo_dets = [d for s in demo_scans for d in s.detections]

        # Source breakdown table.
        source_table = Table(
            [
                ["Source", "Scans", "Detections", "Anomalies", "High Priority"],
                [
                    "Real User Data",
                    str(len(real_scans)),
                    str(len(real_dets)),
                    str(sum(1 for d in real_dets if d.is_anomaly)),
                    str(sum(1 for d in real_dets if d.priority == "high")),
                ],
                [
                    "Demo Data",
                    str(len(demo_scans)),
                    str(len(demo_dets)),
                    str(sum(1 for d in demo_dets if d.is_anomaly)),
                    str(sum(1 for d in demo_dets if d.priority == "high")),
                ],
            ],
            colWidths=[4 * cm, 2.5 * cm, 3 * cm, 3 * cm, 3.5 * cm],
        )
        source_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ecfdf5")),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#065f46")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fef3c7")),
            ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#92400e")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ]))
        flow.append(Paragraph("Data Source Breakdown", h2))
        flow.append(source_table)
        flow.append(Spacer(1, 0.4 * cm))

        # Scans section
        flow.append(Paragraph("Scans in Mission", h2))
        scan_rows = [["Scan ID", "Source", "Timestamp", "Detections", "Anomalies", "Status"]]
        for s in scans:
            dets = len(s.detections)
            anom = sum(1 for d in s.detections if d.is_anomaly)
            scan_rows.append([
                s.scan_uid,
                "DEMO" if s.is_demo else "REAL",
                s.timestamp.strftime("%Y-%m-%d %H:%M") if s.timestamp else "",
                str(dets),
                str(anom),
                s.status,
            ])
        if len(scan_rows) == 1:
            scan_rows.append(["—", "—", "No scans", "0", "0", "—"])
        s_table = Table(scan_rows, colWidths=[3 * cm, 2 * cm, 4 * cm, 2.5 * cm, 2.5 * cm, 2 * cm])
        s_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ]))
        flow.append(s_table)
        flow.append(Spacer(1, 0.4 * cm))

        # Important detections
        important: list[tuple[Scan, Detection]] = []
        for s in scans:
            for d in s.detections:
                if d.priority in {"high", "review"} or d.is_anomaly:
                    important.append((s, d))
        if important:
            flow.append(Paragraph("Important Detections", h2))
            det_rows = [["Scan", "Class", "Confidence", "Priority", "Anomaly"]]
            for s, d in important[:20]:
                det_rows.append([
                    s.scan_uid,
                    d.class_name,
                    f"{d.confidence:.0%}",
                    d.priority,
                    "Yes" if d.is_anomaly else "No",
                ])
            d_table = Table(det_rows, colWidths=[3.5 * cm, 4 * cm, 3 * cm, 2.5 * cm, 2 * cm])
            d_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ]))
            flow.append(d_table)
            flow.append(Spacer(1, 0.4 * cm))

        # Disclaimer
        flow.append(Paragraph("Data Limitations &amp; Disclaimer", h2))
        flow.append(Paragraph(DISCLAIMER, body))
        flow.append(Paragraph(
            "Detections are AI-assisted review priorities derived from the configured inference model. "
            "They are NOT scientifically validated risk scores. Operators must use domain expertise to "
            "confirm or reject every detection before any operational action.",
            body,
        ))

        doc.build(flow)

        record = Report(
            mission_id=mission.id,
            filename=filename,
            file_path=str(file_path),
            generated_by=generated_by,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_reports(self, mission_id: Optional[int] = None) -> list[Report]:
        q = self.db.query(Report)
        if mission_id is not None:
            q = q.filter(Report.mission_id == mission_id)
        return q.order_by(Report.created_at.desc()).all()