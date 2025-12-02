"""
End-to-end pipeline for generating a chess style report.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from style_report.metrics import compute_metrics, csv_to_raw
from style_report.scripts.report_builder import generate_analysis, render_report_html


BASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BASE_DIR.parent

PROMPTS_DIR = BASE_DIR / "prompts"
TEMPLATES_DIR = BASE_DIR / "templates"
SCRIPTS_DIR = BASE_DIR / "scripts"
TEST_PLAYERS_DIR = BASE_DIR / "Test_players"
GM_METRICS_DIR = BASE_DIR / "current GM metrics "

BLACKBOX_ROOT = REPO_ROOT / "chess_imitator" / "rule_tagger_lichessbot"
BLACKBOX_INPUT = BLACKBOX_ROOT / "Test_players"
BLACKBOX_REPORTS = BLACKBOX_ROOT / "reports"

_MAX_MOVES_OVERRIDE: Optional[int] = None


def _canonicalize_player_id(player_id: str) -> str:
    sanitized = "".join(ch for ch in player_id if ch.isalnum() or ch in ("-", "_")).strip("_")
    return sanitized.lower() or "player"


def _canonicalize_name(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _detect_player_name(pgn_path: Path, fallback_id: str) -> Optional[str]:
    """Heuristic: use the most frequent player name from the PGN headers."""
    try:
        import chess.pgn  # local import to avoid hard dependency at module import time
    except Exception:
        return None

    if not pgn_path.exists():
        return None

    name_counts: Dict[str, int] = {}
    target_tokens = {
        _canonicalize_name(fallback_id),
        _canonicalize_name(fallback_id.replace("test", "", 1)),
    }
    with pgn_path.open(encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            for key in ("White", "Black"):
                name = game.headers.get(key, "")
                if name:
                    name_counts[name] = name_counts.get(name, 0) + 1
    if not name_counts:
        return None

    # Prefer exact/substring canonical matches to the fallback player id
    canonical_map = {name: _canonicalize_name(name) for name in name_counts}
    for name, canon in canonical_map.items():
        if any(token and token in canon for token in target_tokens):
            return name

    # Otherwise pick the most frequent (or alphabetically first on tie)
    return sorted(name_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _ensure_directories() -> None:
    for path in (PROMPTS_DIR, TEMPLATES_DIR, SCRIPTS_DIR, TEST_PLAYERS_DIR):
        path.mkdir(parents=True, exist_ok=True)
    BLACKBOX_INPUT.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_player_batch(player_name: str, output_prefix: str, *, max_games: Optional[int] = None, max_moves: Optional[int] = None) -> Dict[str, Path]:
    cmd = [
        sys.executable,
        "scripts/analyze_player_batch.py",
        "--player",
        player_name,
        "--input-dir",
        str(BLACKBOX_INPUT),
        "--output-prefix",
        output_prefix,
        "--fresh-run",
    ]
    if max_games:
        cmd.extend(["--max-games", str(max_games)])
    if max_moves:
        cmd.extend(["--max-moves", str(max_moves)])
    subprocess.run(cmd, cwd=BLACKBOX_ROOT, check=True)

    csv_path = BLACKBOX_REPORTS / f"universal_{output_prefix}_summary.csv"
    moves_path = BLACKBOX_REPORTS / f"{output_prefix}_moves.jsonl"
    summary_json = BLACKBOX_REPORTS / f"universal_{output_prefix}_summary.json"
    per_game_summary = BLACKBOX_REPORTS / f"{output_prefix}_summary.json"

    if not csv_path.exists():
        raise FileNotFoundError(f"Expected CSV not found: {csv_path}")
    if not moves_path.exists():
        raise FileNotFoundError(f"Expected moves log not found: {moves_path}")

    return {
        "csv": csv_path,
        "moves": moves_path,
        "summary_json": summary_json,
        "per_game_summary": per_game_summary,
    }


def _load_gm_reference(gm_root: Path) -> Dict[str, Any]:
    gm_reference: Dict[str, Any] = {}
    if not gm_root.exists():
        return gm_reference

    for gm_dir in gm_root.iterdir():
        if not gm_dir.is_dir():
            continue
        csv_files = sorted(gm_dir.glob("*.csv"))
        if not csv_files:
            continue
        csv_file = csv_files[0]
        gm_data: Dict[str, Any] = {"tags": {}}
        with csv_file.open(encoding="utf-8") as handle:
            next(handle, None)  # header
            for line in handle:
                parts = line.strip().split(",")
                if len(parts) < 3:
                    continue
                tag, count, ratio = parts[0], parts[1], parts[2]
                try:
                    count_val = int(count)
                except ValueError:
                    count_val = 0
                try:
                    ratio_val = float(ratio)
                except ValueError:
                    ratio_val = 0.0
                gm_data["tags"][tag] = {"count": count_val, "ratio": ratio_val}
        intro_path = next(gm_dir.glob("*_intro.txt"), None)
        if intro_path and intro_path.exists():
            gm_data["intro"] = intro_path.read_text(encoding="utf-8").strip()
        gm_reference[gm_dir.name] = gm_data
    return gm_reference


def _build_profile(player_id: str, raw_data: dict, metrics: dict, gm_reference: dict) -> dict:
    totals = raw_data.get("totals", {})
    return {
        "player_id": player_id,
        "meta": {
            "games_count": totals.get("games", 0),
            "moves_count": totals.get("moves", 0),
        },
        "tag_distribution": raw_data.get("tag_distribution", {}),
        "metrics": metrics,
        "gm_reference": gm_reference,
    }


def _safe_ratio(numerator: float | int, denominator: float | int) -> float:
    try:
        return float(numerator) / float(denominator) if denominator else 0.0
    except ZeroDivisionError:
        return 0.0


def _game_accuracy_score(game: dict) -> Optional[float]:
    total_moves = 0
    loss_sum = 0.0
    for move in game.get("moves", []):
        delta = move.get("eval_delta_cp")
        if delta is None:
            continue
        total_moves += 1
        loss_sum += max(-float(delta), 0.0)
    if total_moves == 0:
        return None
    avg_loss = loss_sum / total_moves
    return max(0.0, 1.0 - avg_loss / 100)


def _summarize_openings(raw_data: dict) -> dict:
    buckets: Dict[str, Dict[tuple, Dict[str, Any]]] = {"white": {}, "black": {}}
    for game in raw_data.get("games", []):
        color = game.get("color")
        if color not in buckets:
            continue
        key = (
            (game.get("eco") or "Unknown").strip() or "Unknown",
            (game.get("opening") or "Unknown").strip() or "Unknown",
            (game.get("variation") or "").strip(),
            (game.get("first_moves") or "").strip(),
        )
        bucket = buckets[color].setdefault(
            key,
            {"games": 0, "win": 0, "draw": 0, "loss": 0, "accuracy_sum": 0.0, "accuracy_games": 0},
        )
        bucket["games"] += 1
        result = game.get("result")
        if result in {"win", "draw", "loss"}:
            bucket[result] = bucket.get(result, 0) + 1
        accuracy_score = _game_accuracy_score(game)
        if accuracy_score is not None:
            bucket["accuracy_sum"] += accuracy_score
            bucket["accuracy_games"] += 1

    summary: Dict[str, list] = {"white": [], "black": []}
    for color, groups in buckets.items():
        for (eco, opening, variation, first_moves), data in groups.items():
            games_count = data["games"]
            avg_accuracy = data["accuracy_sum"] / data["accuracy_games"] if data["accuracy_games"] else None
            summary[color].append(
                {
                    "eco": eco,
                    "opening": opening,
                    "variation": variation,
                    "first_moves": first_moves,
                    "games": games_count,
                    "win": _safe_ratio(data.get("win", 0), games_count),
                    "draw": _safe_ratio(data.get("draw", 0), games_count),
                    "loss": _safe_ratio(data.get("loss", 0), games_count),
                    "avg_accuracy": avg_accuracy,
                }
            )
        summary[color].sort(key=lambda item: (-item["games"], item["opening"]))
    return summary


def generate_report(player_id: str, max_games: Optional[int] = None) -> dict:
    """
    Run the full pipeline and return core artifacts for downstream use.
    """
    output_prefix = _canonicalize_player_id(player_id)

    _ensure_directories()

    player_dir = TEST_PLAYERS_DIR / player_id
    player_dir.mkdir(parents=True, exist_ok=True)

    source_pgn = player_dir / "games.pgn"
    if not source_pgn.exists():
        raise FileNotFoundError(f"PGN not found for player: {source_pgn}")

    blackbox_pgn = BLACKBOX_INPUT / f"{player_id}.pgn"
    shutil.copy2(source_pgn, blackbox_pgn)

    player_name = _detect_player_name(source_pgn, player_id) or player_id
    artifacts = _run_player_batch(
        player_name,
        output_prefix,
        max_games=max_games,
        max_moves=_MAX_MOVES_OVERRIDE,
    )

    analysis_csv = player_dir / "analysis.csv"
    shutil.copy2(artifacts["csv"], analysis_csv)

    raw_data = csv_to_raw(
        analysis_csv,
        player_id=player_id,
        pgn_path=source_pgn,
        moves_path=artifacts.get("moves"),
        player_name=player_name,
    )
    _write_json(player_dir / "raw.json", raw_data)

    metrics = compute_metrics(raw_data)
    metrics_path = player_dir / "metrics.json"
    _write_json(metrics_path, metrics)

    gm_reference = _load_gm_reference(GM_METRICS_DIR)
    _write_json(player_dir / "gm_snapshot.json", gm_reference)

    opening_summary = _summarize_openings(raw_data)
    profile = _build_profile(player_id, raw_data, metrics, gm_reference)
    profile["opening_summary"] = opening_summary
    profile_path = player_dir / "player_profile.json"
    _write_json(profile_path, profile)

    analysis = generate_analysis(profile, PROMPTS_DIR)
    analysis_path = player_dir / "analysis_text.json"
    _write_json(analysis_path, analysis)

    analysis_loaded = json.loads(analysis_path.read_text(encoding="utf-8"))
    report_path = player_dir / "report.html"
    rendered_html = render_report_html(player_id, analysis_loaded, TEMPLATES_DIR / "report_base.html")
    report_path.write_text(rendered_html, encoding="utf-8")

    return {
        "player_id": player_id,
        "metrics": json.loads(metrics_path.read_text(encoding="utf-8")),
        "player_profile": json.loads(profile_path.read_text(encoding="utf-8")),
        "analysis": analysis_loaded,
        "overall_md": analysis_loaded.get("overall_synthesis", ""),
        "model_md": analysis_loaded.get("performance_profile", ""),
        "report_html": rendered_html,
    }


def main() -> None:
    global _MAX_MOVES_OVERRIDE

    parser = argparse.ArgumentParser(description="Generate chess style report.")
    parser.add_argument("--player-id", required=True, help="Player identifier, used for folder and file names.")
    parser.add_argument("--pgn", default=None, help="Optional explicit PGN path; defaults to Test_players/<id>/games.pgn.")
    parser.add_argument("--max-games", type=int, default=None, help="Limit games passed to black-box analyzer (debugging).")
    parser.add_argument("--max-moves", type=int, default=None, help="Limit moves passed to black-box analyzer (debugging).")
    args = parser.parse_args()

    player_id = args.player_id
    player_dir = TEST_PLAYERS_DIR / player_id
    player_dir.mkdir(parents=True, exist_ok=True)

    source_pgn = Path(args.pgn) if args.pgn else player_dir / "games.pgn"
    if not source_pgn.exists():
        raise FileNotFoundError(f"PGN not found for player: {source_pgn}")

    if source_pgn.resolve() != (player_dir / "games.pgn").resolve():
        shutil.copy2(source_pgn, player_dir / "games.pgn")

    _MAX_MOVES_OVERRIDE = args.max_moves
    generate_report(player_id=player_id, max_games=args.max_games)


if __name__ == "__main__":
    main()
