from __future__ import annotations

from io import BytesIO
from typing import Iterable

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.issue import Issue


def issues_to_xlsx(issues: Iterable[Issue]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Issues"
    ws.append(
        [
            "Issue Number",
            "Title",
            "Status",
            "Severity",
            "Station",
            "Supports",
            "Priority",
            "Created At",
            "Resolved At",
        ]
    )
    for issue in issues:
        station_code = ""
        if getattr(issue, "station", None) is not None:
            station_code = issue.station.code
        ws.append(
            [
                issue.issue_number,
                issue.title or "",
                issue.status,
                issue.severity,
                station_code,
                issue.support_count,
                float(issue.priority_score or 0),
                issue.created_at.isoformat() if issue.created_at else "",
                issue.resolved_at.isoformat() if issue.resolved_at else "",
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def issues_to_pdf(issues: list[Issue], title: str = "RailVoice Issue Report") -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Total issues: {len(issues)}", styles["Normal"]),
        Spacer(1, 16),
    ]
    rows = [["Number", "Station", "Status", "Sev", "Supports"]]
    for issue in issues[:80]:
        station = issue.station.code if getattr(issue, "station", None) else "-"
        rows.append(
            [
                issue.issue_number,
                station,
                issue.status,
                str(issue.severity),
                str(issue.support_count),
            ]
        )
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D5C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buf.getvalue()
