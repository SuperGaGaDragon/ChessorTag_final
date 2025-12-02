#!/usr/bin/env python3
"""Generate golden rule-tagger cases from chess_imitator move logs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

# === Path configuration for this repository layout ===
LOG_DIR = Path("style_logs")
OUT_DIR = Path("rule_tagger_lichessbot/tests/golden_cases")

MAX_PER_FILE = 50


def iter_log_entries(log_dir: Path) -> Iterator[tuple[Path, int, dict]]:
    """Yield parsed JSON entries and their source metadata."""
    if not log_dir.exists():
        raise SystemExit(f"Log dir not found: {log_dir}")

    for path in sorted(log_dir.glob("moves_log*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[WARN] skip invalid JSON in {path} line {line_no}")
                    continue
                yield path, line_no, data


def next_cases_index(out_dir: Path) -> int:
    """Return the next numeric suffix for casesN.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = []
    for p in out_dir.glob("cases*.json"):
        match = re.match(r"cases(\d+)\.json$", p.name)
        if match:
            existing.append(int(match.group(1)))
    if not existing:
        return 1
    return max(existing) + 1


def build_case_id(log_path: Path, idx: int) -> str:
    """Produce a stable ID for the golden case entry."""
    stem = log_path.stem
    return f"log_{stem}_{idx:04d}"


def entry_to_case(idx: int, log_path: Path, entry: dict) -> dict | None:
    """Project a log entry into the golden case structure."""
    fen = entry.get("fen")
    picked = entry.get("picked") or {}
    uci = picked.get("uci") or picked.get("move")
    tags = picked.get("tags") or []

    if not fen or not uci:
        return None

    profile_name = entry.get("profile_name")
    make_error = entry.get("make_error")
    eval_drop = entry.get("eval_drop")

    description_bits = []
    if profile_name:
        description_bits.append(f"profile={profile_name}")
    if make_error is not None:
        description_bits.append(f"make_error={make_error}")
    if eval_drop is not None:
        description_bits.append(f"eval_drop={eval_drop}")

    return {
        "id": build_case_id(log_path, idx),
        "fen": fen,
        "move": uci,
        "move_uci": uci,
        "description": "; ".join(description_bits),
        "source_file": log_path.name,
        "label": "",
        "expected_tags": [],
        "current_tags": tags,
    }


def main() -> None:
    cases: list[dict] = []
    for log_idx, (log_path, _, entry) in enumerate(iter_log_entries(LOG_DIR), start=1):
        case = entry_to_case(log_idx, log_path, entry)
        if case is None:
            continue
        cases.append(case)

    if not cases:
        print("No valid log entries found, nothing to write.")
        return

    start_index = next_cases_index(OUT_DIR)
    print(f"Found {len(cases)} cases, writing starting from cases{start_index}.json")

    for chunk_offset in range(0, len(cases), MAX_PER_FILE):
        chunk = cases[chunk_offset : chunk_offset + MAX_PER_FILE]
        file_index = start_index + (chunk_offset // MAX_PER_FILE)
        out_path = OUT_DIR / f"cases{file_index}.json"
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(chunk, handle, ensure_ascii=False, indent=2)
        print(f"  wrote {len(chunk):3d} cases -> {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
