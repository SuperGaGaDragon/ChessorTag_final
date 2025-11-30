"""
End-to-end Phase 2 pipeline with graceful fallbacks:
- If sample_data/<id>.raw.json exists → reuse it.
- Else if Test_players/<id>/raw.json exists → reuse it.
- Else run the black-box analyzer on PGN (default: Test_players/<id>/games.pgn)
  to produce raw.json.
- Always copy raw → sample_data/<id>.raw.json (for build_report_payload).
- Build Phase 2 payload (fixed_data + llm_slots + visualizations).
- Emit JSON and a static HTML using report_base_phase2.html.

Usage:
    python3 -m style_report.scripts.run_phase2_report \
        --player-id testYuyaochen \
        [--pgn /path/to/games.pgn] \
        [--max-games 50] \
        [--max-moves 400] \
        [--with-llm]

Outputs:
- Test_players/<id>/raw.json           (if generated or reused)
- sample_data/<id>.raw.json            (always refreshed)
- Test_players/<id>/report_phase2.json
- Test_players/<id>/report_phase2.html (inline data, openable without API)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from style_report.metrics import csv_to_raw
from style_report.metrics.fixed_data import compute_fixed_data
from style_report.report_service import build_report_payload, load_gm_reference
from style_report.scripts.run_full_report import (
    BLACKBOX_INPUT,
    BLACKBOX_REPORTS,
    PROMPTS_DIR,
    SCRIPTS_DIR,
    TEMPLATES_DIR,
    TEST_PLAYERS_DIR,
    _canonicalize_player_id,
    _detect_player_name,
    _ensure_directories,
    _run_player_batch,
    _write_json,
)

BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"


def _static_phase2_html(payload: Dict[str, Any], template_path: Path) -> str:
    """Inline the payload into the Phase 2 template so it can open without API."""
    html = template_path.read_text(encoding="utf-8")

    # Adjust asset paths for output under Test_players/<id>/
    html = (
        html.replace("../assets/", "../../assets/")
        .replace("/style_report/assets/", "../../assets/")
        .replace("../current GM metrics ", "../../current GM metrics ")
    )

    # Replace simple placeholders (player id, GM cards placeholder)
    player_id = payload.get("player_id", "player")
    html = html.replace("{{PLAYER_ID}}", str(player_id))
    html = html.replace("{{GM_CARDS}}", "")

    json_blob = json.dumps(payload, ensure_ascii=False)
    inline_script = f"window.__PHASE2_INLINE_PAYLOAD__ = {json_blob};"
    html = html.replace("// window.fillReportData({{REPORT_DATA_JSON}});", inline_script)
    return html


def _load_existing_raw(player_id: str) -> Optional[Dict[str, Any]]:
    """
    Try existing raw files before running black-box.
    Priority: sample_data/<id>.raw.json → Test_players/<id>/raw.json
    """
    sample_path = SAMPLE_DATA_DIR / f"{player_id}.raw.json"
    if sample_path.exists():
        return json.loads(sample_path.read_text(encoding="utf-8"))

    player_raw = TEST_PLAYERS_DIR / player_id / "raw.json"
    if player_raw.exists():
        return json.loads(player_raw.read_text(encoding="utf-8"))
    return None


def _convert_from_csv(
    csv_path: Path,
    player_id: str,
    source_pgn: Path,
    moves_path: Optional[Path],
    player_name: str,
) -> Dict[str, Any]:
    """Build raw.json from CSV + PGN (+moves if available)."""
    return csv_to_raw(
        csv_path,
        player_id=player_id,
        pgn_path=source_pgn,
        moves_path=moves_path,
        player_name=player_name,
    )


def run_phase2_report(
    player_id: str,
    *,
    pgn_path: Optional[Path] = None,
    max_games: Optional[int] = None,
    max_moves: Optional[int] = None,
    include_llm: bool = False,
) -> Dict[str, Any]:
    _ensure_directories()

    player_id = _canonicalize_player_id(player_id)
    player_dir = TEST_PLAYERS_DIR / player_id
    player_dir.mkdir(parents=True, exist_ok=True)

    source_pgn = pgn_path if pgn_path else player_dir / "games.pgn"
    if not source_pgn.exists():
        raise FileNotFoundError(f"PGN not found for player: {source_pgn}")

    # 1) Try existing raw to avoid unnecessary black-box work
    raw_data = _load_existing_raw(player_id)
    detected_name = _detect_player_name(source_pgn, player_id) or player_id
    raw_path = player_dir / "raw.json"

    if raw_data is None:
        # Copy PGN into black-box input
        blackbox_pgn = BLACKBOX_INPUT / f"{player_id}.pgn"
        shutil.copy2(source_pgn, blackbox_pgn)

        artifacts = _run_player_batch(
            detected_name,
            player_id,
            max_games=max_games,
            max_moves=max_moves,
        )

        # Convert to raw.json from CSV/moves
        analysis_csv = player_dir / "analysis.csv"
        shutil.copy2(artifacts["csv"], analysis_csv)
        raw_data = _convert_from_csv(
            analysis_csv,
            player_id=player_id,
            source_pgn=source_pgn,
            moves_path=artifacts.get("moves"),
            player_name=detected_name,
        )
        _write_json(raw_path, raw_data)
    else:
        # Ensure raw.json is present under player folder for visibility
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(raw_path, raw_data)

    # Ensure player_name is present even when reusing raw
    if not raw_data.get("player_name"):
        raw_data["player_name"] = detected_name
        _write_json(raw_path, raw_data)
        _write_json(SAMPLE_DATA_DIR / f"{player_id}.raw.json", raw_data)

    # Copy to Phase 2 sample_data for build_report_payload
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    phase2_raw_path = SAMPLE_DATA_DIR / f"{player_id}.raw.json"
    _write_json(phase2_raw_path, raw_data)

    gm_reference = load_gm_reference()
    fixed_data = compute_fixed_data(raw_data, gm_reference)

    payload = build_report_payload(player_id, include_llm=include_llm)
    display_name = raw_data.get("player_name") or detected_name
    payload["player_display_name"] = display_name
    payload["player_id"] = display_name

    # Persist outputs
    payload_path = player_dir / "report_phase2.json"
    _write_json(payload_path, payload)

    html = _static_phase2_html(payload, TEMPLATES_DIR / "report_base_phase2.html")
    html_path = player_dir / "report_phase2.html"
    html_path.write_text(html, encoding="utf-8")

    return {
        "player_id": player_id,
        "raw_path": raw_path,
        "phase2_raw_path": phase2_raw_path,
        "payload_path": payload_path,
        "html_path": html_path,
        "fixed_data": fixed_data,
        "payload": payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 2 pipeline from PGN to Phase 2 report.")
    parser.add_argument("--player-id", required=True, help="Player identifier (folder name under Test_players).")
    parser.add_argument("--pgn", default=None, help="Optional explicit PGN path; defaults to Test_players/<id>/games.pgn.")
    parser.add_argument("--max-games", type=int, default=None, help="Limit games passed to black-box analyzer.")
    parser.add_argument("--max-moves", type=int, default=None, help="Limit moves passed to black-box analyzer.")
    parser.add_argument("--with-llm", action="store_true", help="Generate llm_slots using configured LLM.")
    args = parser.parse_args()

    pgn_path = Path(args.pgn) if args.pgn else None

    result = run_phase2_report(
        player_id=args.player_id,
        pgn_path=pgn_path,
        max_games=args.max_games,
        max_moves=args.max_moves,
        include_llm=args.with_llm,
    )

    print(json.dumps(
        {
            "player_id": result["player_id"],
            "raw_json": str(result["raw_path"]),
            "phase2_raw": str(result["phase2_raw_path"]),
            "payload_json": str(result["payload_path"]),
            "html": str(result["html_path"]),
        },
        indent=2,
    ))


if __name__ == "__main__":  # pragma: no cover
    main()
