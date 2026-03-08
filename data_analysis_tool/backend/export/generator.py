"""Export analysis to PPT, PDF 1-pager, or DOCX."""
import io
from typing import Any, Dict, Tuple

from .docx_gen import build_docx
from .pdf_gen import build_pdf
from .ppt_gen import build_ppt


def export_analysis(analysis: Dict[str, Any], format: str) -> Tuple[bytes, str, str]:
    """
    Generate export file. Returns (file_bytes, media_type, filename).
    format is one of: ppt, pdf, docx
    """
    if analysis.get("error"):
        raise ValueError("No analysis available to export")
    format = format.lower().strip()
    if format == "ppt":
        return build_ppt(analysis)
    if format == "pdf":
        return build_pdf(analysis)
    if format == "docx":
        return build_docx(analysis)
    raise ValueError(f"Unsupported format: {format}. Use ppt, pdf, or docx.")

