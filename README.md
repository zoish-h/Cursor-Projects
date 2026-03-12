# Cursor Projects

A collection of projects built in Cursor.

## Contents

### [Data Analysis Tool](data_analysis_tool/)

Web app that ingests **CSV, Excel, PDF, and XML** files, auto-analyses data with metric selection and explainability, answers natural language questions via **Ollama**, and exports to **PPT**, **PDF 1-pager**, or **DOCX**.

- **Run:** From `data_analysis_tool/`: `py run.py` → open http://localhost:8000/app/
- **Setup:** See [data_analysis_tool/README.md](data_analysis_tool/README.md)

### Planetary Runner (platformer)

A Pygame platformer: survive the Martian terrain with obstacles, power-ups, and leaderboard.

- **Run:** `py platformer.py` (requires `pygame` — see `requirements.txt` in repo or `martian_game/requirements.txt`)

### [Job Application Autofill (Chrome Extension)](job-autofill-extension/)

Chrome extension that securely auto-fills repeated job application fields (experience, dates, survey questions, etc.) across common ATS platforms like Workday, Greenhouse, Lever, Jobvite, SmartRecruiters, Eightfold, and Uber careers pages. All data is stored locally in your browser and can be searched and cleared per site.

### martian_game/

Alternate or extended version of the platformer game (includes `platformer.py` and `leaderboard.json`).

---

## Quick start

| Project              | Command                          |
|----------------------|-----------------------------------|
| Data Analysis Tool   | `cd data_analysis_tool` then `py run.py` |
| Platformer           | `py platformer.py`               |

## Requirements

- **Data Analysis Tool:** Python 3.9+, see [data_analysis_tool/requirements_data_tool.txt](data_analysis_tool/requirements_data_tool.txt)
- **Platformer:** `pygame` (e.g. `pip install pygame` or use `requirements.txt`)
