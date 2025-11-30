"""
Slot-level prompt builder for `report_base_phase2.html`.

Each prompt targets a specific `.llm-slot` in the template and enforces:
- No headings/tables/lists (HTML structure already exists).
- Output stays within the requested word ranges.
- Use only the provided JSON data; no external knowledge.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable


def _fmt_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _gm_tag_snapshot(gm_reference: dict, tags: Iterable[str]) -> dict:
    snapshot: Dict[str, Dict[str, float]] = {}
    for gm_name, gm_data in (gm_reference or {}).items():
        gm_tags = gm_data.get("tags") or {}
        rows: Dict[str, float] = {}
        for tag in tags:
            info = gm_tags.get(tag)
            if not info:
                continue
            try:
                rows[tag] = round(float(info.get("ratio", 0.0)) * 100.0, 1)
            except Exception:
                continue
        if rows:
            snapshot[gm_name] = rows
    return snapshot


def _base_rules(slot_id: str, word_rule: str) -> str:
    return (
        f"You are a GM chess coach writing the prose for the slot `{slot_id}` "
        f"in the Phase 2 chess style report. The HTML already has headings and tables.\n"
        f"- Output: {word_rule} in English, using only <p> blocks (no headings, tables, lists, or numbering).\n"
        f"- Use ONLY the JSON numbers provided; do not invent games or GM data that are not in the JSON.\n"
        f"- Keep claims comparative: higher/lower than peers or GMs based on the given ratios."
    )


def build_llm_prompts(raw_data: dict, fixed_data: dict, gm_reference: dict | None) -> Dict[str, str]:
    """
    Build per-slot prompts aligned with `report_base_phase2.html`.
    """
    prompts: Dict[str, str] = {}

    # ---------- Section 1: Performance Profile ----------
    winrate_data = {"winrate": fixed_data.get("winrate")}
    prompts["section-1-1-winrate-llm"] = f"""{_base_rules("section-1-1-winrate-llm", "<=100 words")}

Context:
- Analyze win/loss/draw split by color and total.
- Stay factual; no style coaching.

Data JSON:
{_fmt_json(winrate_data)}
"""

    accuracy_data = {
        "accuracy": fixed_data.get("accuracy"),
        "accuracy_comparison": fixed_data.get("accuracy_comparison"),
    }
    prompts["section-1-2-accuracy-llm"] = f"""{_base_rules("section-1-2-accuracy-llm", "<=100 words")}

Context:
- Assess overall strength via accuracy and identify which phase (opening/middlegame/endgame/queenless) is stronger or weaker.
- Keep it data-grounded; short and direct.

Data JSON:
{_fmt_json(accuracy_data)}
"""

    prompts["section-1-3-advantage-llm"] = f"""{_base_rules("section-1-3-advantage-llm", "150–200 words")}

Context:
- Advantage conversion: use +1/+3/+5/+7 (white/black) win/draw/loss ratios.
- Explain where the player converts advantages cleanly vs where conversion drops off.

Data JSON:
{_fmt_json({"advantage": fixed_data.get("advantage")})}
"""

    prompts["section-1-4-defensive-llm"] = f"""{_base_rules("section-1-4-defensive-llm", "150–200 words")}

Context:
- Defensive resilience: use -1/-3/-5/-7 tables (white/black).
- Describe resilience patterns and collapse points based on the ratios.

Data JSON:
{_fmt_json({"defensive": fixed_data.get("defensive")})}
"""

    prompts["section-1-5-volatility-llm"] = f"""{_base_rules("section-1-5-volatility-llm", "200–300 words")}

Context:
- Characterize volatility types (smooth crush/collapse, small/medium/big swings, high-precision draws) by color.
- Explain what this says about risk profile and game control.

Data JSON:
{_fmt_json({"volatility": fixed_data.get("volatility")})}
"""

    prompts["section-1-6-engine-llm"] = f"""{_base_rules("section-1-6-engine-llm", "150–200 words")}

Context:
- Engine decision quality by color: best-move %, inaccuracies, mistakes, blunders.
- Extract the main quality pattern; keep comparisons explicit.

Data JSON:
{_fmt_json({"engine": fixed_data.get("engine")})}
"""

    prompts["section-1-7-tactical-llm"] = f"""{_base_rules("section-1-7-tactical-llm", "150–200 words")}

Context:
- Tactical conversion vs misses (counts and rate).
- Infer calculation sharpness and alertness.

Data JSON:
{_fmt_json({"tactical": fixed_data.get("tactical")})}
"""

    prompts["section-1-8-exchanges-llm"] = f"""{_base_rules("section-1-8-exchanges-llm", "300–400 words")}

Context:
a) Explain what total knight/bishop exchange frequency implies about style.
b) Using player vs GM ratios for accurate/inaccurate/bad exchanges, assess judgment quality.
c) Compare with closest top GMs from the provided GM snapshot (use only these numbers).

Data JSON:
{_fmt_json({"exchanges": fixed_data.get("exchanges"), "gm_reference": _gm_tag_snapshot(gm_reference, ["accurate_knight_bishop_exchange", "inaccurate_knight_bishop_exchange", "bad_knight_bishop_exchange"])})}
"""

    prompts["section-1-9-forced-llm"] = f"""{_base_rules("section-1-9-forced-llm", "300–400 words")}

Context:
a) Explain what forced-move frequency says about style, preferred positions, and strengths.
b) Compare the player's forced-move ratio to the GM snapshot to find the closest stylistic peers and shared traits.

Data JSON:
{_fmt_json({"forced": fixed_data.get("forced"), "gm_reference": _gm_tag_snapshot(gm_reference, ["forced_move"])})}
"""

    gm_positions = _gm_tag_snapshot(gm_reference, ["winning_position_handling", "losing_position_handling"])
    max_gm_win = max((vals.get("winning_position_handling", 0) for vals in gm_positions.values()), default=0)
    max_gm_loss = max((vals.get("losing_position_handling", 0) for vals in gm_positions.values()), default=0)
    prompts["section-1-10-positions-llm"] = f"""{_base_rules("section-1-10-positions-llm", "200–260 words")}

Context:
A) Analyze winning vs losing position handling ratios and what they reveal about style.
B) Compare against the GM snapshot. If the player's ratio for a tag exceeds double the highest GM value (winning>{max_gm_win*2:.1f}% or losing>{max_gm_loss*2:.1f}%), respond only with: "Data too noisy; no reliable reference value."

Data JSON:
{_fmt_json({"positions": fixed_data.get("positions"), "gm_reference": gm_positions})}
"""

    # ---------- Section 2: Style Parameters ----------
    prompts["section-2-1-maneuver-llm"] = f"""{_base_rules("section-2-1-maneuver-llm", "200–260 words")}

Context:
- Explain overall maneuver ratio meaning.
- Analyze constructive/prepare/neutral/misplaced/opening split and quality.
- Compare with closest GMs from the snapshot; avoid single-tag conclusions.

Data JSON:
{_fmt_json({"style_maneuver": fixed_data.get("style_maneuver"), "gm_reference": _gm_tag_snapshot(gm_reference, ["constructive_maneuver", "constructive_maneuver_prepare", "neutral_maneuver", "misplaced_maneuver", "failed_maneuver", "maneuver_opening"])})}
"""

    prompts["section-2-2-prophylaxis-llm"] = f"""{_base_rules("section-2-2-prophylaxis-llm", "200–260 words")}

Context:
- Evaluate overall prophylaxis (direct + latent + meaningless) level.
- Describe prevention philosophy via direct vs latent balance; assess failed/meaningless share as quality signal.
- Compare with closest GMs using the snapshot.

Data JSON:
{_fmt_json({"style_prophylaxis": fixed_data.get("style_prophylaxis"), "gm_reference": _gm_tag_snapshot(gm_reference, ["prophylactic_direct", "prophylactic_latent", "prophylactic_meaningless", "prophylactic_failed", "failed_prophylactic"])})}
"""

    prompts["section-2-3-semantic-control-llm"] = f"""{_base_rules("section-2-3-semantic-control-llm", "220–280 words")}

Context:
- Interpret overall semantic control ratio and what it signals about style.
- Break down simplify / plan_kill / freeze_bind / blockade / file_seal / king_safety_shell / space_clamp / regroup / slowdown preferences.
- Compare with two closest GMs using the snapshot; use relative statements rather than raw percentages only.

Data JSON:
{_fmt_json({"style_semantic_control": fixed_data.get("style_semantic_control"), "gm_reference": _gm_tag_snapshot(gm_reference, ["control_simplify", "control_plan_kill", "control_freeze_bind", "control_blockade_passed", "control_file_seal", "control_king_safety_shell", "control_space_clamp", "control_regroup_consolidate", "control_slowdown"])})}
"""

    prompts["section-2-4-cod-llm"] = f"""{_base_rules("section-2-4-cod-llm", "200–260 words")}

Context:
- Explain overall control_over_dynamics meaning.
- Use nine sub-tags to infer style/ability; compare only with provided GM snapshot.
- Avoid labeling as pure control player solely on high ratios; reference other clusters.

Data JSON:
{_fmt_json({"style_control_over_dynamics": fixed_data.get("style_control_over_dynamics"), "gm_reference": _gm_tag_snapshot(gm_reference, ["control_over_dynamics", "control_file_seal", "control_freeze_bind", "control_king_safety_shell", "control_regroup_consolidate", "control_plan_kill", "control_blockade_passed", "control_simplify", "control_space_clamp", "control_slowdown"])})}
"""

    prompts["section-2-5-initiative-llm"] = f"""{_base_rules("section-2-5-initiative-llm", "170–230 words")}

Context:
- Evaluate initiative_attempt vs deferred vs premature attack vs c-file pressure.
- Use comparisons with GM snapshot to judge aggressiveness vs patience.

Data JSON:
{_fmt_json({"style_initiative": fixed_data.get("style_initiative"), "gm_reference": _gm_tag_snapshot(gm_reference, ["initiative_attempt", "deferred_initiative", "premature_attack", "c_file_pressure"])})}
"""

    prompts["section-2-6-tension-llm"] = f"""{_base_rules("section-2-6-tension-llm", "170–230 words")}

Context:
- Analyze tension_creation vs neutral_tension_creation to judge whether the player keeps or releases tension.
- Compare with GM snapshot to anchor conclusions.

Data JSON:
{_fmt_json({"style_tension": fixed_data.get("style_tension"), "gm_reference": _gm_tag_snapshot(gm_reference, ["tension_creation", "neutral_tension_creation"])})}
"""

    prompts["section-2-7-structural-llm"] = f"""{_base_rules("section-2-7-structural-llm", "170–230 words")}

Context:
- Interpret structural integrity vs dynamic/static compromises and what it says about risk tolerance.
- Compare to GMs using the snapshot.

Data JSON:
{_fmt_json({"style_structural": fixed_data.get("style_structural"), "gm_reference": _gm_tag_snapshot(gm_reference, ["structural_integrity", "structural_compromise_dynamic", "structural_compromise_static"])})}
"""

    prompts["section-2-8-sacrifice-llm"] = f"""{_base_rules("section-2-8-sacrifice-llm", "220–300 words")}

Context:
- Explain overall sacrifice ratio meaning.
- Analyze tactical vs positional vs speculative vs desperate + combination/init/structure/space split.
- Compare with two closest GMs from the snapshot; avoid single-tag conclusions.

Data JSON:
{_fmt_json({"style_sacrifice": fixed_data.get("style_sacrifice"), "gm_reference": _gm_tag_snapshot(gm_reference, ["tactical_sacrifice", "positional_sacrifice", "inaccurate_tactical_sacrifice", "speculative_sacrifice", "desperate_sacrifice", "tactical_combination_sacrifice", "tactical_initiative_sacrifice", "positional_structure_sacrifice", "positional_space_sacrifice"])})}
"""

    prompts["section-2-9-synthesis-llm"] = f"""{_base_rules("section-2-9-synthesis-llm", "300–400 words")}

Context:
- Synthesize the entire style parameter section (2.x) without mixing performance profile data.
- Build a holistic style portrait using maneuver/prophylaxis/control/initiative/tension/structure/sacrifice/exchanges/forced tags only.

Data JSON:
{_fmt_json({"style": {k: fixed_data.get(k) for k in fixed_data if k.startswith("style_")}, "exchanges": fixed_data.get("exchanges"), "forced": fixed_data.get("forced")})}
"""

    # ---------- Section 3: Overall Synthesis ----------
    gm_all_tags = set()
    for gm_data in (gm_reference or {}).values():
        gm_all_tags.update((gm_data.get("tags") or {}).keys())
    prompts["section-3-1-ability-llm"] = f"""{_base_rules("section-3-1-ability-llm", "350–500 words")}

Context:
- Integrate all available data (performance + style + openings) into a detailed style/level evaluation.
- Identify key strengths/weaknesses, preferred positions/openings, and comparisons to top GM clusters.
- Do not add headings or lists; write continuous paragraphs.

Data JSON:
{_fmt_json({"player_id": raw_data.get("player_id"), "fixed_data": fixed_data, "gm_reference": _gm_tag_snapshot(gm_reference, gm_all_tags)})}
"""

    prompts["section-3-2-rating-llm"] = f"""{_base_rules("section-3-2-rating-llm", "180–260 words")}

Context:
- Estimate the player's FIDE rating based only on the provided data.
- State an explicit error margin (e.g., ±80) and note that more games reduce uncertainty.
- Briefly describe how the player's profile differs from the next higher and next lower rating bands.
- Use continuous prose; no lists.

Data JSON:
{_fmt_json({"player_id": raw_data.get("player_id"), "fixed_data": fixed_data, "gm_reference": _gm_tag_snapshot(gm_reference, gm_all_tags)})}
"""

    # ---------- Section 4: Opening Repertoire ----------
    openings_data = fixed_data.get("openings") or {}
    prompts["section-4-1-white-openings-llm"] = f"""{_base_rules("section-4-1-white-openings-llm", "100–150 words")}

Context:
- Identify which white openings/variations perform best or worst using the table data.
- Stay concise; no headings or bullet points.

Data JSON:
{_fmt_json({"white": openings_data.get("white")})}
"""

    prompts["section-4-2-black-openings-llm"] = f"""{_base_rules("section-4-2-black-openings-llm", "100–150 words")}

Context:
- Identify which black defenses/variations perform best or worst.

Data JSON:
{_fmt_json({"black": openings_data.get("black")})}
"""

    prompts["section-4-3-main-repertoires-llm"] = f"""{_base_rules("section-4-3-main-repertoires-llm", "140–200 words")}

Context:
- From opening tables, label the main repertoires (highest game volume/consistency) for White and Black.
- Explain why these lines are considered core choices.

Data JSON:
{_fmt_json(openings_data)}
"""

    prompts["section-4-4-secondary-llm"] = f"""{_base_rules("section-4-4-secondary-llm", "120–180 words")}

Context:
- Highlight secondary or surprise weapons (lower volume but notable performance or accuracy).
- Mention when sample sizes are too small.

Data JSON:
{_fmt_json(openings_data)}
"""

    prompts["section-4-5-depth-llm"] = f"""{_base_rules("section-4-5-depth-llm", "120–180 words")}

Context:
- Use accuracy per line and variation diversity to infer theoretical depth/preparation quality for both colors.

Data JSON:
{_fmt_json(openings_data)}
"""

    prompts["section-4-6-style-llm"] = f"""{_base_rules("section-4-6-style-llm", "140–200 words")}

Context:
- Connect opening choices to style parameters (maneuver/control/initiative/sacrifice, etc.).
- Use style totals from fixed_data plus opening trends to explain stylistic coherence.

Data JSON:
{_fmt_json({"openings": openings_data, "style": {k: fixed_data.get(k) for k in fixed_data if k.startswith("style_")}, "forced": fixed_data.get("forced"), "exchanges": fixed_data.get("exchanges")})}
"""

    prompts["section-4-7-performance-llm"] = f"""{_base_rules("section-4-7-performance-llm", "140–200 words")}

Context:
- Contrast underperforming vs shining openings for both colors using win/draw/loss + accuracy.
- Mention sample-size caveats when appropriate.

Data JSON:
{_fmt_json(openings_data)}
"""

    prompts["section-4-8-takeaways-llm"] = f"""{_base_rules("section-4-8-takeaways-llm", "120–170 words")}

Context:
- Give practical repertoire takeaways based solely on the opening tables (keep within JSON data).
- One tight paragraph; no bullet lists or coaching beyond what data implies.

Data JSON:
{_fmt_json(openings_data)}
"""

    # ---------- Section 5: Training Recommendations ----------
    prompts["section-5-1-priorities-llm"] = f"""{_base_rules("section-5-1-priorities-llm", "140–200 words")}

Context:
- Based on weaknesses from performance/style metrics, list key training priorities (text only, no bullets).

Data JSON:
{_fmt_json(fixed_data)}
"""

    prompts["section-5-2-study-llm"] = f"""{_base_rules("section-5-2-study-llm", "140–200 words")}

Context:
- Suggest study methods tailored to observed strengths/weaknesses (openings, calculation, structural play) using only provided metrics.

Data JSON:
{_fmt_json(fixed_data)}
"""

    prompts["section-5-3-habits-llm"] = f"""{_base_rules("section-5-3-habits-llm", "140–200 words")}

Context:
- Recommend practical habits (time management, risk control, review focus) grounded in the metrics.

Data JSON:
{_fmt_json(fixed_data)}
"""

    # ---------- Section 6: Opponent Preparation ----------
    prompts["section-6-1-vs-white-llm"] = f"""{_base_rules("section-6-1-vs-white-llm", "140–200 words")}

Context:
- As opponent preparing vs this player with White: choose openings/structures exploiting weaknesses shown in data (openings + style/performance).

Data JSON:
{_fmt_json({"openings": openings_data, "style": {k: fixed_data.get(k) for k in fixed_data if k.startswith("style_")}, "performance": {k: fixed_data.get(k) for k in ("winrate", "accuracy", "advantage", "defensive", "volatility", "engine", "tactical", "exchanges", "forced", "positions")}})}
"""

    prompts["section-6-2-vs-black-llm"] = f"""{_base_rules("section-6-2-vs-black-llm", "140–200 words")}

Context:
- As opponent preparing vs this player with Black: suggest opening directions/structures using weaknesses from metrics.

Data JSON:
{_fmt_json({"openings": openings_data, "style": {k: fixed_data.get(k) for k in fixed_data if k.startswith("style_")}, "performance": {k: fixed_data.get(k) for k in ("winrate", "accuracy", "advantage", "defensive", "volatility", "engine", "tactical", "exchanges", "forced", "positions")}})}
"""

    prompts["section-6-3-middlegame-llm"] = f"""{_base_rules("section-6-3-middlegame-llm", "140–200 words")}

Context:
- Middlegame plans against this player: exploit style weaknesses (initiative, tension, maneuver, sacrifices, control) plus conversion/defense trends.

Data JSON:
{_fmt_json({"style": {k: fixed_data.get(k) for k in fixed_data if k.startswith("style_")}, "performance": {k: fixed_data.get(k) for k in ("advantage", "defensive", "volatility", "engine", "tactical", "exchanges", "forced")}})}
"""

    prompts["section-6-4-endgame-llm"] = f"""{_base_rules("section-6-4-endgame-llm", "140–200 words")}

Context:
- Endgame strategies vs this player using accuracy (endgame/queenless), maneuver quality, structural play, and winning/losing position handling.

Data JSON:
{_fmt_json({"accuracy": fixed_data.get("accuracy"), "style_maneuver": fixed_data.get("style_maneuver"), "style_structural": fixed_data.get("style_structural"), "positions": fixed_data.get("positions")})}
"""

    prompts["section-6-5-psychology-llm"] = f"""{_base_rules("section-6-5-psychology-llm", "140–200 words")}

Context:
- Describe psychological/risk profile inferred from volatility, initiative/tension choices, sacrifices, and conversion/defense.
- Provide opponent-facing advice grounded in data.

Data JSON:
{_fmt_json({"volatility": fixed_data.get("volatility"), "style_initiative": fixed_data.get("style_initiative"), "style_tension": fixed_data.get("style_tension"), "style_sacrifice": fixed_data.get("style_sacrifice"), "advantage": fixed_data.get("advantage"), "defensive": fixed_data.get("defensive")})}
"""

    prompts["section-6-6-gameplan-llm"] = f"""{_base_rules("section-6-6-gameplan-llm", "140–200 words")}

Context:
- Summarize a full opponent game plan (opening to endgame) that exploits the quantified tendencies. No bullets.

Data JSON:
{_fmt_json({"openings": openings_data, "performance": {k: fixed_data.get(k) for k in ("winrate", "accuracy", "advantage", "defensive", "volatility", "engine", "tactical", "exchanges", "forced", "positions")}, "style": {k: fixed_data.get(k) for k in fixed_data if k.startswith("style_")}})}
"""

    return prompts
