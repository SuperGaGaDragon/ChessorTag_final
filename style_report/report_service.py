"""
Service layer to assemble the Phase 2 report payload.

This wires raw data + GM reference → fixed_data (pure metrics) and keeps
placeholders for LLM slots / visualizations.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from style_report.metrics.fixed_data import compute_fixed_data
from style_report.explanation import TAG_EXPLANATIONS
from style_report.prompts.phase2_prompts import build_llm_prompts
from style_report.llm_slots import run_llm_slots


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
GM_METRICS_DIR = BASE_DIR / "current GM metrics "

# Whitelist for GM photo usage in front-end mapping
GM_WHITELIST = {
    "bobby fischer",
    "garry kasparov",
    "anatoly karpov",
    "mihail tal",
    "tigran petrosian",
    "ding liren",
}


def load_raw_data(player_id: str) -> Dict[str, Any]:
    """
    Temporary loader: read raw_data from JSON on disk.
    Swap this out with the real aggregator output when ready.
    """
    path = SAMPLE_DATA_DIR / f"{player_id}.raw.json"
    if not path.exists():
        raise FileNotFoundError(f"raw_data not found for {player_id}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_single_gm_dir(gm_dir: Path) -> Dict[str, Any]:
    """
    Parse one GM folder (expects one CSV with tag,count,ratio).
    """
    gm_data: Dict[str, Any] = {"tags": {}}
    csv_files = sorted(gm_dir.glob("*.csv"))
    if not csv_files:
        return gm_data
    csv_file = csv_files[0]
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
    photo = next((p for p in gm_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}), None)
    if photo:
        gm_data["photo"] = photo.name
    return gm_data


def load_gm_reference() -> Dict[str, Any]:
    """
    Load real GM baseline from `current GM metrics` directory.
    """
    reference: Dict[str, Any] = {}
    if not GM_METRICS_DIR.exists():
        return reference
    for gm_dir in GM_METRICS_DIR.iterdir():
        if not gm_dir.is_dir():
            continue
        gm_name = gm_dir.name.strip()
        reference[gm_name] = _load_single_gm_dir(gm_dir)
    return reference


def _pct(val: float) -> float:
    return round(val * 100.0, 1)


def _gm_values_for_tags(gm_reference: dict, tags: list[str]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for gm_name, gm_data in gm_reference.items():
        if gm_name.strip().lower() not in GM_WHITELIST:
            continue
        gm_tags = gm_data.get("tags") or {}
        total = 0.0
        found = False
        for tag in tags:
            info = gm_tags.get(tag)
            if info and "ratio" in info:
                total += float(info["ratio"])
                found = True
        if not found:
            continue
        values.append({"name": gm_name, "value": _pct(total)})
    return values


def _build_visualizations(fixed: dict, gm_reference: dict) -> Dict[str, Any]:
    """
    Prepare visualization payloads for axes present in the template.
    """
    viz: Dict[str, Any] = {}

    def add_viz(viz_id: str, player_value: Optional[float], gm_tags: list[str]) -> None:
        if player_value is None:
            return
        viz[viz_id] = {
            "player": {"name": "You", "value": player_value},
            "gms": _gm_values_for_tags(gm_reference, gm_tags),
        }

    add_viz("viz-forced-moves-axis", fixed.get("forced", {}).get("ratio"), ["forced_move"])
    add_viz(
        "viz-positions-axis",
        fixed.get("positions", {}).get("winning", {}).get("ratio"),
        ["winning_position_handling"],
    )
    add_viz(
        "viz-maneuver-axis",
        fixed.get("style_maneuver", {}).get("total", {}).get("ratio"),
        ["constructive_maneuver", "constructive_maneuver_prepare", "neutral_maneuver", "misplaced_maneuver", "maneuver_opening", "failed_maneuver"],
    )
    add_viz(
        "viz-prophylaxis-axis",
        fixed.get("style_prophylaxis", {}).get("total", {}).get("ratio"),
        ["prophylactic_direct", "prophylactic_latent", "prophylactic_meaningless", "prophylactic_failed", "failed_prophylactic"],
    )
    add_viz(
        "viz-semantic-control-axis",
        fixed.get("style_semantic_control", {}).get("total", {}).get("ratio"),
        [
            "control_simplify",
            "control_plan_kill",
            "control_freeze_bind",
            "control_blockade_passed",
            "control_file_seal",
            "control_king_safety_shell",
            "control_space_clamp",
            "control_regroup_consolidate",
            "control_slowdown",
        ],
    )
    add_viz(
        "viz-cod-axis",
        fixed.get("style_control_over_dynamics", {}).get("overall", {}).get("ratio"),
        ["control_over_dynamics"],
    )
    add_viz(
        "viz-initiative-axis",
        fixed.get("style_initiative", {}).get("attempt", {}).get("ratio"),
        ["initiative_attempt"],
    )
    add_viz(
        "viz-tension-axis",
        fixed.get("style_tension", {}).get("creation", {}).get("ratio"),
        ["tension_creation"],
    )
    add_viz(
        "viz-structural-axis",
        fixed.get("style_structural", {}).get("integrity", {}).get("ratio"),
        ["structural_integrity"],
    )
    add_viz(
        "viz-sacrifice-axis",
        fixed.get("style_sacrifice", {}).get("total", {}).get("ratio"),
        [
            "tactical_sacrifice",
            "positional_sacrifice",
            "inaccurate_tactical_sacrifice",
            "speculative_sacrifice",
            "desperate_sacrifice",
            "tactical_combination_sacrifice",
            "tactical_initiative_sacrifice",
            "positional_structure_sacrifice",
            "positional_space_sacrifice",
        ],
    )

    return viz


def _should_use_llm(include_llm: bool | None) -> bool:
    if include_llm is not None:
        return bool(include_llm)
    return os.getenv("STYLE_REPORT_ENABLE_LLM", "").lower() in {"1", "true", "yes", "on"}


def build_report_payload(player_id: str, *, include_llm: bool | None = None) -> Dict[str, Any]:
    """
    Build the payload consumed by the Phase 2 front-end.
    """
    raw_data = load_raw_data(player_id)
    gm_reference = load_gm_reference()
    fixed = compute_fixed_data(raw_data, gm_reference)
    visualizations = _build_visualizations(fixed, gm_reference)
    llm_slots: Dict[str, Any] = {}

    display_name = raw_data.get("player_name") or raw_data.get("player_id") or player_id

    if _should_use_llm(include_llm):
        prompts = build_llm_prompts(raw_data, fixed, gm_reference)
        llm_slots = run_llm_slots(prompts)

    return {
        "player_id": display_name,
        "player_display_name": display_name,
        "player_key": player_id,
        "fixed_data": fixed,
        "llm_slots": llm_slots,
        "visualizations": visualizations,
        "tag_explanations": TAG_EXPLANATIONS,
    }
