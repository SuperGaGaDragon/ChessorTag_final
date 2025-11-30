"""
Lightweight FastAPI entrypoint to serve the Phase 2 report payload and static assets.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from style_report.report_service import build_report_payload


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "style_report"


app.mount(
    "/style_report",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="style_report",
)


@app.get("/api/report/{player_id}")
def api_get_report(player_id: str) -> dict:
    try:
        return build_report_payload(player_id)
    except FileNotFoundError as exc:  # surfaced as 404 for missing player data
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - surfaced to client
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/report/{player_id}", response_class=HTMLResponse)
def report_page(player_id: str) -> HTMLResponse:
    html_path = FRONTEND_DIR / "templates" / "report_base_phase2.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Report template not found.")
    html = html_path.read_text(encoding="utf-8")
    return HTMLResponse(html)
