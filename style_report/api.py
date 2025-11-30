"""
Minimal FastAPI application for generating chess style reports.

Run locally:
    uvicorn style_report.api:app --reload --port 8001
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from style_report.scripts.run_full_report import generate_report
from style_report.report_service import build_report_payload


app = FastAPI()


class ReportRequest(BaseModel):
    player_id: str
    max_games: Optional[int] = None


@app.post("/report")
def create_report(request: ReportRequest) -> dict:
    try:
        return generate_report(player_id=request.player_id, max_games=request.max_games)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - surfaced to client
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/report/{player_id}")
def get_report_payload(player_id: str, with_llm: bool = False) -> dict:
    try:
        return build_report_payload(player_id, include_llm=with_llm)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - surfaced to client
        raise HTTPException(status_code=500, detail=str(exc))
