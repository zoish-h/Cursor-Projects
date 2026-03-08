# Data Analysis Tool

Web app that ingests **CSV, Excel, PDF, and XML** files, auto-analyses data (with metric selection and explainability), answers natural language questions via **Ollama**, and exports to **PPT**, **PDF 1-pager**, or **DOCX**.

## Setup

1. **Python 3.9+** and a virtual environment recommended.

2. **Install dependencies** (from this folder):

   ```bash
   pip install -r requirements_data_tool.txt
   ```

3. **Optional – natural language Q&A**: Install and run [Ollama](https://ollama.com), then pull a model:

   ```bash
   ollama run llama3.2
   ```

   Keep Ollama running. If it is not running, the "Ask" feature will show an error message.

## Run

From the `data_analysis_tool` directory:

```bash
py run.py
```

Or manually:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open in a browser: **http://localhost:8000/app/**

- **Upload**: Drag and drop or select CSV, Excel (.xlsx/.xls), XML, or PDF (tables/text).
- **Analysis**: View auto-selected metrics and explainability; expand column profile.
- **Ask**: Type a question in natural language (requires Ollama).
- **Export**: Download the analysis as PPT, PDF 1-pager, or DOCX.

## API

- `POST /upload` – upload file(s), returns analysis and session.
- `GET /analysis` – get current analysis.
- `POST /ask` – body `{"question": "..."}` – streamed answer (SSE).
- `POST /export` – body `{"format": "ppt"|"pdf"|"docx"}` – file download.

## Notes

- **Large files**: Consider a max upload size (e.g. 50 MB); all processing is in memory.
- **PDF**: Table extraction works best with clear table layouts; otherwise text is extracted.
- **XML**: Expects a repeating element (e.g. `<record>`) that maps to rows.
