"""FastAPI app: upload, analysis, ask, export."""
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from analysis import run_analysis
from export import export_analysis
from ingestion import load_file
from nl import build_context, stream_ask

# In-memory session: session_id -> { "dfs": [...], "analysis": {...} }
_sessions: Dict[str, Dict[str, Any]] = {}
_current_session_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # cleanup if needed
    pass


app = FastAPI(title="Data Analysis Tool", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def _get_session(session_id: Optional[str] = None) -> Tuple[Optional[str], Dict[str, Any]]:
    sid = session_id or _current_session_id
    if not sid or sid not in _sessions:
        return sid, {}
    return sid, _sessions[sid]


class AskBody(BaseModel):
    question: str


class ExportBody(BaseModel):
    format: str  # ppt | pdf | docx


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    global _current_session_id
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    session_id = str(uuid.uuid4())
    all_dfs: List[pd.DataFrame] = []
    for f in files:
        content = await f.read()
        dfs, err = load_file(content, f.filename or "unknown")
        if err:
            raise HTTPException(status_code=400, detail=err)
        all_dfs.extend(dfs)
    if not all_dfs:
        raise HTTPException(status_code=400, detail="No data extracted from files")
    analysis = run_analysis(all_dfs)
    _sessions[session_id] = {"dfs": all_dfs, "analysis": analysis}
    _current_session_id = session_id
    return {"session_id": session_id, "analysis": analysis}


@app.get("/analysis")
@app.get("/analysis/{session_id}")
async def get_analysis(session_id: Optional[str] = None):
    sid, data = _get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="No analysis found. Upload a file first.")
    return data["analysis"]


@app.post("/ask")
async def ask(body: AskBody, session_id: Optional[str] = None):
    sid, data = _get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="No dataset loaded. Upload a file first.")
    analysis = data["analysis"]
    context = build_context(analysis)

    async def event_generator():
        async for chunk in stream_ask(body.question, context):
            yield {"data": chunk}

    return EventSourceResponse(event_generator())


@app.post("/export")
async def export(body: ExportBody, session_id: Optional[str] = None):
    sid, data = _get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="No analysis to export. Upload a file first.")
    analysis = data["analysis"]
    try:
        file_bytes, media_type, filename = export_analysis(analysis, body.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/")
async def root():
    return {"message": "Data Analysis Tool API. Use /upload, /analysis, /ask, /export. Open /app for the UI."}


# Serve frontend (open http://localhost:8000/app/)
_frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_path.exists():
    app.mount("/app", StaticFiles(directory=_frontend_path, html=True), name="frontend")
