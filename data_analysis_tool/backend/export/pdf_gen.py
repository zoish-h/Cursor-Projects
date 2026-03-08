"""Generate PDF 1-pager from analysis."""
import io
from typing import Any, Dict, List, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _metrics_rows(analysis: Dict[str, Any]) -> List[List[str]]:
    dl = analysis.get("dataset_level", {})
    metrics = dl.get("metrics", {}) or {}
    return [[k, str(v)[:80]] for k, v in metrics.items() if k != "explanation_type"]


def build_pdf(analysis: Dict[str, Any]) -> Tuple[bytes, str, str]:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(name="Title", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    story.append(Paragraph("Data Analysis Report (1-pager)", title_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(f"<b>Dataset:</b> {analysis.get('row_count', 0)} rows, {analysis.get('column_count', 0)} columns. "
                          f"Kind: {analysis.get('dataset_level', {}).get('characterization', {}).get('kind', 'generic')}.", styles["Normal"]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("<b>Explainability</b>", styles["Heading2"]))
    for msg in analysis.get("explainability", []):
        story.append(Paragraph(f"• {msg}", styles["Normal"]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("<b>Key metrics</b>", styles["Heading2"]))
    rows = _metrics_rows(analysis)
    if rows:
        t = Table([["Metric", "Value"]] + rows[:15], colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), "#e0e0e0"), ("GRID", (0, 0), (-1, -1), 0.5, "gray"), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
        story.append(t)
    else:
        story.append(Paragraph("No metrics computed.", styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue(), "application/pdf", "analysis_report.pdf"

