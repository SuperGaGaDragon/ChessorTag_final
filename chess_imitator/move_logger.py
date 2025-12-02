"""Helpers to persist style move decisions to a JSONL log."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Tuple

_LOGGER = logging.getLogger(__name__)

_LOG_DIR = Path(__file__).resolve().parent / "style_logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE_BASE = "moves_log"
_LOG_FILE_EXT = ".jsonl"
_MAX_LINES_PER_FILE = 50


def _log_file_index(path: Path) -> int:
    """Return the rotation index encoded in a log file name."""
    stem = path.stem
    if stem == _LOG_FILE_BASE:
        return 0
    prefix = f"{_LOG_FILE_BASE}_"
    if stem.startswith(prefix):
        suffix = stem[len(prefix) :]
        if suffix.isdigit():
            return int(suffix)
    return -1


def _format_log_file(index: int) -> Path:
    """Build the log path for a particular rotation index."""
    if index <= 0:
        name = f"{_LOG_FILE_BASE}{_LOG_FILE_EXT}"
    else:
        name = f"{_LOG_FILE_BASE}_{index}{_LOG_FILE_EXT}"
    return _LOG_DIR / name


def _enumerate_existing_log_files() -> list[Tuple[int, Path]]:
    """Return sorted log candidates by their rotation index."""
    files: list[Tuple[int, Path]] = []
    pattern = f"{_LOG_FILE_BASE}*{_LOG_FILE_EXT}"
    for entry in _LOG_DIR.glob(pattern):
        idx = _log_file_index(entry)
        if idx >= 0:
            files.append((idx, entry))
    files.sort(key=lambda pair: pair[0])
    return files


def _count_lines(path: Path) -> int:
    """Return the number of lines currently in the file."""
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _initialize_log_state() -> Tuple[Path, int]:
    """Boot the log rotation state when the module is imported."""
    files = _enumerate_existing_log_files()
    if not files:
        return _format_log_file(0), 0
    last_idx, last_path = files[-1]
    lines = _count_lines(last_path)
    if lines >= _MAX_LINES_PER_FILE:
        return _format_log_file(last_idx + 1), 0
    return last_path, lines


_CURRENT_LOG_FILE, _CURRENT_LINE_COUNT = _initialize_log_state()


def _rotate_log_file_if_needed() -> None:
    """Switch to a new log file once the current one reaches the size limit."""
    global _CURRENT_LOG_FILE, _CURRENT_LINE_COUNT

    if _CURRENT_LINE_COUNT < _MAX_LINES_PER_FILE:
        return
    current_index = _log_file_index(_CURRENT_LOG_FILE)
    next_path = _format_log_file(current_index + 1)
    _CURRENT_LOG_FILE = next_path
    _CURRENT_LINE_COUNT = 0


def _log_move_decision(
    payload_with_tags: Dict[str, Any],
    style_profile: Dict[str, Any],
    picked: Dict[str, Any],
    *,
    make_error: bool,
    error_rate: float,
) -> None:
    """
    Persist the current move decision into a JSONL log entry.

    Failures are absorbed so the engine never raises because of logging.
    """
    global _CURRENT_LINE_COUNT

    try:
        game_id = payload_with_tags.get("game_id")
        ply = payload_with_tags.get("ply")
        fen = payload_with_tags.get("fen")
        side = payload_with_tags.get("side_to_move")

        profile_name = style_profile.get("player_name")
        config = style_profile.get("config", {}) or {}

        picked_uci = picked.get("uci") or picked.get("move")
        picked_tags = picked.get("tags", []) or []
        picked_eval = picked.get("sf_eval")

        candidates = payload_with_tags.get("candidates", [])

        entry = {
            "ts": time.time(),
            "game_id": game_id,
            "ply": ply,
            "side_to_move": side,
            "fen": fen,
            "profile_name": profile_name,
            "config": {
                "deterministic": bool(config.get("deterministic", False)),
                "error_rate": float(error_rate),
            },
            "make_error": bool(make_error),
            "picked": {
                "uci": picked_uci,
                "tags": picked_tags,
                "sf_eval": picked_eval,
                "style_score": picked.get("style_score"),
            },
            "candidates": candidates,
        }

        _rotate_log_file_if_needed()
        with _CURRENT_LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _CURRENT_LINE_COUNT += 1

    except Exception as exc:  # noqa: BLE001
        _LOGGER.error("Failed to log move decision: %s", exc)
