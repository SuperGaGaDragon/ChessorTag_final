#!/usr/bin/env python3
"""
Batch refactor remaining CoD detectors.
"""

import re

# Read the file
filepath = "rule_tagger_lichessbot/rule_tagger2/legacy/cod_detectors.py"
with open(filepath, "r") as f:
    content = f.read()

# Define replacements for remaining detectors
replacements = [
    # blockade_passed
    (
        r'def detect_cod_blockade_passed\(ctx: Dict\[str, Any\], cfg: Dict\[str, Any\]\) -> Tuple\[Optional\[Dict\[str, Any\]\], Dict\[str, Any\]\]:\n(?:.*?\n)*?    return candidate, gate',
        '''def detect_cod_blockade_passed(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """CoD wrapper for blockade_passed pattern detection."""
    semantic_result = is_blockade_passed(ctx, cfg)
    if not semantic_result.passed:
        return None, {}
    metrics = semantic_result.metrics
    min_drop = float(cfg.get("PASSED_PUSH_MIN", CONTROL_DEFAULTS["PASSED_PUSH_MIN"]))
    gate = _cod_gate(
        ctx, subtype="blockade_passed",
        opp_passed_exists=ctx.get("opp_passed_exists", False),
        blockade_established=ctx.get("blockade_established", False),
        push_drop=metrics.get("opp_passed_push_drop", 0.0),
        push_threshold=min_drop,
        see_non_positive=metrics.get("see_non_positive", False),
        push_ok=metrics.get("push_ok", False),
    )
    gate["passed"] = True
    candidate = {
        "name": "blockade_passed",
        "metrics": metrics,
        "why": semantic_result.why,
        "score": semantic_result.score,
        "gate": gate,
    }
    return candidate, gate'''
    ),
    # file_seal
    (
        r'def detect_cod_file_seal\(ctx: Dict\[str, Any\], cfg: Dict\[str, Any\]\) -> Tuple\[Optional\[Dict\[str, Any\]\], Dict\[str, Any\]\]:\n(?:.*?\n)*?    return candidate, gate',
        '''def detect_cod_file_seal(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """CoD wrapper for file_seal pattern detection."""
    semantic_result = is_file_seal(ctx, cfg)
    if not semantic_result.passed:
        return None, {}
    metrics = semantic_result.metrics
    line_min = float(cfg.get("LINE_MIN", CONTROL_DEFAULTS["LINE_MIN"]))
    gate = _cod_gate(
        ctx, subtype="file_seal",
        opp_line_pressure_drop=metrics.get("opp_line_pressure_drop", 0.0),
        break_candidates_delta=metrics.get("break_candidates_delta", 0.0),
        mobility_drop=metrics.get("opp_mobility_drop", 0.0),
        line_min=line_min,
        volatility_drop=metrics.get("volatility_drop_cp", 0.0),
    )
    gate["passed"] = True
    candidate = {
        "name": "file_seal",
        "metrics": metrics,
        "why": semantic_result.why,
        "score": semantic_result.score,
        "gate": gate,
    }
    return candidate, gate'''
    ),
    # king_safety_shell
    (
        r'def detect_cod_king_safety_shell\(ctx: Dict\[str, Any\], cfg: Dict\[str, Any\]\) -> Tuple\[Optional\[Dict\[str, Any\]\], Dict\[str, Any\]\]:\n(?:.*?\n)*?    return candidate, gate',
        '''def detect_cod_king_safety_shell(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """CoD wrapper for king_safety_shell pattern detection."""
    semantic_result = is_king_safety_shell(ctx, cfg)
    if not semantic_result.passed:
        return None, {}
    metrics = semantic_result.metrics
    threshold = float(cfg.get("KS_MIN", CONTROL_DEFAULTS["KS_MIN"])) / 100.0
    gate = _cod_gate(
        ctx, subtype="king_safety_shell",
        king_safety_gain=metrics.get("king_safety_gain", 0.0),
        opp_tactics=metrics.get("opp_tactics_change_eval", 0.0),
        opp_mobility_drop=metrics.get("opp_mobility_drop", 0.0),
        king_safety_threshold=threshold,
    )
    gate["passed"] = True
    candidate = {
        "name": "king_safety_shell",
        "metrics": metrics,
        "why": semantic_result.why,
        "score": semantic_result.score,
        "gate": gate,
    }
    return candidate, gate'''
    ),
    # space_clamp
    (
        r'def detect_cod_space_clamp\(ctx: Dict\[str, Any\], cfg: Dict\[str, Any\]\) -> Tuple\[Optional\[Dict\[str, Any\]\], Dict\[str, Any\]\]:\n(?:.*?\n)*?    return candidate, gate',
        '''def detect_cod_space_clamp(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """CoD wrapper for space_clamp pattern detection."""
    semantic_result = is_space_clamp(ctx, cfg)
    if not semantic_result.passed:
        return None, {}
    metrics = semantic_result.metrics
    phase_adjust = phase_bonus(ctx, cfg)
    space_threshold = float(cfg.get("SPACE_MIN", CONTROL_DEFAULTS["SPACE_MIN"])) / 10.0
    mob_threshold = cfg.get("OP_MOBILITY_DROP", CONTROL_OPP_MOBILITY_DROP)
    vol_threshold = cfg.get("VOLATILITY_DROP_CP", CONTROL_VOLATILITY_DROP_CP) + phase_adjust["VOL_BONUS"]
    gate = _cod_gate(
        ctx, subtype="space_clamp",
        space_gain=metrics.get("space_gain", 0.0),
        space_control_gain=metrics.get("space_control_gain", 0.0),
        opp_mobility_drop=metrics.get("opp_mobility_drop", 0.0),
        tension_delta=metrics.get("tension_delta", 0.0),
        volatility_drop_cp=metrics.get("volatility_drop_cp", 0.0),
        space_threshold=space_threshold,
        mobility_threshold=mob_threshold,
        volatility_threshold=vol_threshold,
    )
    gate.update({
        "space_ok": metrics.get("space_ok", False),
        "tension_ok": metrics.get("tension_ok", False),
        "mobility_ok": metrics.get("mobility_ok", False),
        "env_ok": metrics.get("env_ok", False),
        "passed": True,
    })
    candidate = {
        "name": "space_clamp",
        "metrics": metrics,
        "why": semantic_result.why,
        "score": semantic_result.score,
        "gate": gate,
    }
    return candidate, gate'''
    ),
    # regroup_consolidate
    (
        r'def detect_cod_regroup_consolidate\(ctx: Dict\[str, Any\], cfg: Dict\[str, Any\]\) -> Tuple\[Optional\[Dict\[str, Any\]\], Dict\[str, Any\]\]:\n(?:.*?\n)*?    return candidate, gate',
        '''def detect_cod_regroup_consolidate(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """CoD wrapper for regroup_consolidate pattern detection."""
    semantic_result = is_regroup_consolidate(ctx, cfg)
    if not semantic_result.passed:
        return None, {}
    metrics = semantic_result.metrics
    gate = _cod_gate(
        ctx, subtype="regroup_consolidate",
        king_safety_gain=metrics.get("king_safety_gain", 0.0),
        structure_gain=metrics.get("structure_gain", 0.0),
        self_mobility_change=metrics.get("self_mobility_change", 0.0),
        volatility_drop=metrics.get("volatility_drop_cp", 0.0),
    )
    gate["passed"] = True
    candidate = {
        "name": "regroup_consolidate",
        "metrics": metrics,
        "why": semantic_result.why,
        "score": semantic_result.score,
        "gate": gate,
    }
    return candidate, gate'''
    ),
    # slowdown
    (
        r'def detect_cod_slowdown\(ctx: Dict\[str, Any\], cfg: Dict\[str, Any\]\) -> Tuple\[Optional\[Dict\[str, Any\]\], Dict\[str, Any\]\]:\n(?:.*?\n)*?    return candidate, gate',
        '''def detect_cod_slowdown(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """CoD wrapper for slowdown pattern detection."""
    semantic_result = is_slowdown(ctx, cfg)
    if not semantic_result.passed:
        return None, {}
    metrics = semantic_result.metrics
    vol_bonus = phase_bonus(ctx, cfg)["VOL_BONUS"]
    mob_bonus = phase_bonus(ctx, cfg)["OP_MOB_DROP"]
    vol_threshold = cfg.get("VOLATILITY_DROP_CP", CONTROL_VOLATILITY_DROP_CP) + vol_bonus
    mob_threshold = cfg.get("OP_MOBILITY_DROP", CONTROL_OPP_MOBILITY_DROP) + mob_bonus
    phase_bucket = ctx.get("phase_bucket", "middlegame")
    tension_threshold = _control_tension_threshold(phase_bucket)
    gate = _cod_gate(
        ctx, subtype="slowdown",
        has_dynamic=ctx.get("has_dynamic_in_band", False),
        played_kind=ctx.get("played_kind"),
        eval_drop_cp=metrics.get("eval_drop_cp", 0),
        eval_threshold=cfg.get("EVAL_DROP_CP", CONTROL_EVAL_DROP),
        volatility_drop=metrics.get("volatility_drop_cp", 0.0),
        volatility_threshold=vol_threshold,
        tension_delta=metrics.get("tension_delta", 0.0),
        tension_threshold=tension_threshold,
        opp_mobility_drop=metrics.get("opp_mobility_drop", 0.0),
        mobility_threshold=mob_threshold,
    )
    gate["passed"] = True
    candidate = {
        "name": "slowdown",
        "metrics": metrics,
        "why": semantic_result.why,
        "score": semantic_result.score,
        "gate": gate,
    }
    return candidate, gate'''
    ),
]

# Apply replacements
for pattern, replacement in replacements:
    matches = list(re.finditer(pattern, content, re.DOTALL))
    if matches:
        print(f"Found {len(matches)} match(es) for pattern")
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        print(f"WARNING: No matches found for pattern: {pattern[:50]}...")

# Write back
with open(filepath, "w") as f:
    f.write(content)

print(f"\nRefactored {filepath}")
print("Done!")
