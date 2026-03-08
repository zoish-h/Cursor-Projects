"""Load CSV, Excel, XML, PDF into one or more pandas DataFrames."""
import io
from pathlib import Path
from typing import List, Tuple

import pandas as pd


def get_supported_extensions() -> List[str]:
    return [".csv", ".xlsx", ".xls", ".xml", ".pdf"]


def _load_csv(content: bytes, filename: str) -> List[pd.DataFrame]:
    try:
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8", on_bad_lines="skip")
    except Exception:
        df = pd.read_csv(io.BytesIO(content), encoding="latin-1", on_bad_lines="skip")
    if df.empty or df.shape[1] <= 1 and df.shape[0] == 0:
        df = pd.read_csv(io.BytesIO(content), sep=None, engine="python", on_bad_lines="skip")
    return [df]


def _load_excel(content: bytes, filename: str) -> List[pd.DataFrame]:
    xl = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    return [xl.parse(sheet_name) for sheet_name in xl.sheet_names]


def _load_xml(content: bytes, filename: str) -> List[pd.DataFrame]:
    try:
        df = pd.read_xml(io.BytesIO(content))
        return [df]
    except Exception:
        import xml.etree.ElementTree as ET

        tree = ET.parse(io.BytesIO(content))
        root = tree.getroot()
        # Find a repeating child (e.g. <record>, <row>, <item>)
        children = list(root)
        if not children:
            return [pd.DataFrame()]
        # Use first level of repeating elements
        rows = []
        for child in children:
            row = {}
            for sub in child:
                tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                row[tag] = sub.text
            if row:
                rows.append(row)
        if not rows:
            return [pd.DataFrame()]
        return [pd.DataFrame(rows)]


def _load_pdf(content: bytes, filename: str) -> List[pd.DataFrame]:
    import pdfplumber

    dfs = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for t in tables:
                    if t and len(t) > 0:
                        df = pd.DataFrame(t[1:], columns=t[0] if t[0] else None)
                        if not df.empty:
                            dfs.append(df)
        if not dfs:
            # Fallback: extract text and put in one column
            lines = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.splitlines():
                        if line.strip():
                            lines.append({"text": line})
            if lines:
                dfs.append(pd.DataFrame(lines))
    return dfs if dfs else [pd.DataFrame()]


_DISPATCH = {
    ".csv": _load_csv,
    ".xlsx": _load_excel,
    ".xls": _load_excel,
    ".xml": _load_xml,
    ".pdf": _load_pdf,
}


def load_file(content: bytes, filename: str) -> Tuple[List[pd.DataFrame], str]:
    """
    Load file into list of DataFrames.
    Returns (list of DataFrames, error_message or empty string).
    """
    ext = Path(filename).suffix.lower()
    if ext not in _DISPATCH:
        return [], f"Unsupported format: {ext}. Use one of {get_supported_extensions()}"
    try:
        dfs = _DISPATCH[ext](content, filename)
        dfs = [df for df in dfs if df is not None and not df.empty]
        if not dfs:
            return [], "No data could be extracted from the file."
        return dfs, ""
    except Exception as e:
        return [], str(e)
