"""Run the Data Analysis Tool server. Execute from data_analysis_tool directory: py run.py"""
import os
import sys
from pathlib import Path

# Run from backend directory so imports (analysis, ingestion, etc.) resolve
backend = Path(__file__).resolve().parent / "backend"
os.chdir(backend)
sys.path.insert(0, str(backend))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
