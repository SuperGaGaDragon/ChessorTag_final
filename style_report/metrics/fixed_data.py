"""
Utilities to compute the Phase 2 `fixed_data` payload expected by
`report_base_phase2.html`.

This module converts the raw JSON (and optional GM reference data) into
fully-populated metric structures the front-end can render without
LLM involvement.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional


def _safe_ratio(numerator: float | int, denominator: float | int) -> float:
    try:
        return float(numerator) / float(denominator) if denominator else 0.0
    except ZeroDivisionError:
        return 0.0


def _pct(value: float, digits: int = 1) -> float:
    """Convert a ratio (0-1) to percentage with rounding."""
    return round(float(value) * 100.0, digits)


def _avg(values: Iterable[float]) -> Optional[float]:
    values = [v for v in values if v is not None]
    return mean(values) if values else None


def _gm_avg_ratio(gm_reference: dict | None, tags: Iterable[str]) -> Optional[float]:
    """
    Average the provided tag ratios across all GMs.
    Returns percentage (0-100) or None if unavailable.
    """
    if not gm_reference:
        return None
    ratios: List[float] = []
    tag_list = list(tags)
    for gm in gm_reference.values():
        gm_tags = gm.get("tags") or {}
        total_ratio = 0.0
        found = False
        for tag in tag_list:
            info = gm_tags.get(tag)
            if info and "ratio" in info:
                total_ratio += float(info["ratio"])
                found = True
        if found:
            ratios.append(total_ratio)
    if not ratios:
        return 0.0
    return _pct(_avg(ratios))


def _gather_moves(games: Iterable[dict]) -> Iterable[tuple[dict, dict]]:
    for game in games:
        for move in game.get("moves", []):
            yield game, move


def _winrate_by_color(games: List[dict]) -> dict[str, Any]:
    buckets = {
        "white": {"games": 0, "win": 0, "draw": 0, "loss": 0, "elos": []},
        "black": {"games": 0, "win": 0, "draw": 0, "loss": 0, "elos": []},
    }
    for game in games:
        color = game.get("color")
        if color not in buckets:
            continue
        bucket = buckets[color]
        bucket["games"] += 1
        result = game.get("result")
        if result in bucket:
            bucket[result] += 1
        elo = game.get("opponent_elo")
        if isinstance(elo, (int, float)):
            bucket["elos"].append(float(elo))

    def finalize(bucket: dict) -> dict:
        games_count = bucket["games"] or 0
        return {
            "win": _pct(_safe_ratio(bucket["win"], games_count)),
            "draw": _pct(_safe_ratio(bucket["draw"], games_count)),
            "loss": _pct(_safe_ratio(bucket["loss"], games_count)),
            "elo": round(_avg(bucket["elos"]), 1) if bucket["elos"] else None,
        }

    white = finalize(buckets["white"])
    black = finalize(buckets["black"])
    total_games = buckets["white"]["games"] + buckets["black"]["games"]
    total = {
        "win": _pct(_safe_ratio(buckets["white"]["win"] + buckets["black"]["win"], total_games)),
        "draw": _pct(_safe_ratio(buckets["white"]["draw"] + buckets["black"]["draw"], total_games)),
        "loss": _pct(_safe_ratio(buckets["white"]["loss"] + buckets["black"]["loss"], total_games)),
        "elo": round(
            _avg((buckets["white"]["elos"] + buckets["black"]["elos"])),
            1,
        )
        if (buckets["white"]["elos"] + buckets["black"]["elos"])
        else None,
    }
    return {"white": white, "black": black, "total": total}


def _accuracy_by_phase(games: List[dict]) -> dict[str, Any]:
    buckets = defaultdict(lambda: {"moves": 0, "loss_sum": 0.0})
    for _, move in _gather_moves(games):
        phase = (move.get("phase") or "unknown").lower()
        delta = move.get("eval_delta_cp")
        if delta is None:
            continue
        loss = max(-float(delta), 0.0)
        buckets["overall"]["moves"] += 1
        buckets["overall"]["loss_sum"] += loss
        if phase in ("opening", "middlegame", "endgame"):
            buckets[phase]["moves"] += 1
            buckets[phase]["loss_sum"] += loss
        has_queen = move.get("has_queen")
        if has_queen is True:
            buckets["queenful"]["moves"] += 1
            buckets["queenful"]["loss_sum"] += loss
        elif has_queen is False:
            buckets["queenless"]["moves"] += 1
            buckets["queenless"]["loss_sum"] += loss

    def finalize(bucket: dict) -> dict:
        moves = bucket["moves"]
        if moves == 0:
            return {"moves": 0, "avg_loss": None, "score": None}
        avg_loss = bucket["loss_sum"] / moves
        score = max(0.0, 1.0 - avg_loss / 100.0)
        return {
            "moves": moves,
            "avg_loss": round(avg_loss, 2),
            "score": round(score, 3),
        }

    phases = ("overall", "opening", "middlegame", "endgame", "queenful", "queenless")
    return {phase: finalize(buckets[phase]) for phase in phases}


def _threshold_wdl_by_color(games: List[dict], thresholds_cp: List[int], *, positive: bool) -> dict[str, Any]:
    """
    For advantage (positive=True) and defensive (positive=False) conversion.
    """
    data: dict[str, dict[str, dict[int, dict[str, int]]]] = {
        "white": defaultdict(lambda: {"win": 0, "draw": 0, "loss": 0, "games": 0}),
        "black": defaultdict(lambda: {"win": 0, "draw": 0, "loss": 0, "games": 0}),
    }
    for game in games:
        color = game.get("color")
        if color not in data:
            continue
        evaluations = [mv.get("cp_before") for mv in game.get("moves", []) if mv.get("cp_before") is not None]
        if not evaluations:
            continue
        max_cp = max(evaluations)
        min_cp = min(evaluations)
        result = game.get("result")
        for thr in thresholds_cp:
            reached = max_cp >= thr if positive else min_cp <= -thr
            if not reached:
                continue
            bucket = data[color][thr]
            bucket["games"] += 1
            if result in {"win", "draw", "loss"}:
                bucket[result] = bucket.get(result, 0) + 1

    def finalize(bucket: dict[str, int]) -> dict[str, float]:
        total = bucket.get("games", 0) or 0
        return {
            "win": _pct(_safe_ratio(bucket.get("win", 0), total)),
            "draw": _pct(_safe_ratio(bucket.get("draw", 0), total)),
            "loss": _pct(_safe_ratio(bucket.get("loss", 0), total)),
        }

    output: dict[str, Any] = {}
    for thr in thresholds_cp:
        key = f"{'+' if positive else '-'}{int(thr/100)}"
        output[key] = {
            "white": finalize(data["white"][thr]),
            "black": finalize(data["black"][thr]),
        }
    return output


def _volatility_by_color(games: List[dict]) -> dict[str, Any]:
    buckets: dict[str, defaultdict[str, int]] = {
        "white": defaultdict(int),
        "black": defaultdict(int),
    }
    totals = {"white": 0, "black": 0}

    for game in games:
        color = game.get("color")
        if color not in buckets:
            continue
        evaluations = [mv.get("cp_before") for mv in game.get("moves", []) if mv.get("cp_before") is not None]
        if not evaluations:
            continue
        result = game.get("result", "unknown")
        max_cp = max(evaluations)
        min_cp = min(evaluations)
        span = max_cp - min_cp

        label = None
        if result == "win" and min_cp >= 100:
            label = "smooth_crush"
        elif result == "loss" and max_cp <= -100:
            label = "smooth_collapse"
        elif result == "draw" and span <= 80:
            label = "high_precision_draws"
        elif span <= 200:
            label = "small_swings"
        elif span <= 400:
            label = "medium_swings"
        else:
            label = "big_swings"

        buckets[color][label] += 1
        totals[color] += 1

    def to_row(label: str) -> dict[str, Any]:
        white_total = totals["white"] or 0
        black_total = totals["black"] or 0
        return {
            "white": {
                "games": buckets["white"][label],
                "ratio": _pct(_safe_ratio(buckets["white"][label], white_total)),
            },
            "black": {
                "games": buckets["black"][label],
                "ratio": _pct(_safe_ratio(buckets["black"][label], black_total)),
            },
        }

    labels = ["smooth_crush", "smooth_collapse", "small_swings", "medium_swings", "big_swings", "high_precision_draws"]
    return {label: to_row(label) for label in labels}


def _engine_quality(games: List[dict]) -> dict[str, Any]:
    top1 = 0
    top3 = 0
    blunder = 0
    total = 0
    for _, move in _gather_moves(games):
        delta = move.get("eval_delta_cp")
        if delta is None:
            continue
        total += 1
        if delta >= -1e-9:
            top1 += 1
        if delta >= -50:
            top3 += 1
        if delta < -100:
            blunder += 1

    return {
        "top1": {"player": _pct(_safe_ratio(top1, total)), "peer": 0, "gm": 0},
        "top3": {"player": _pct(_safe_ratio(top3, total)), "peer": 0, "gm": 0},
        "blunder": {"player": _pct(_safe_ratio(blunder, total)), "peer": 0, "gm": 0},
    }


def _tactical_conversion(games: List[dict]) -> dict[str, Any]:
    total = 0
    exploited = 0
    for _, move in _gather_moves(games):
        tags = [t.lower() for t in move.get("tags", [])]
        if not any("tactic" in t for t in tags):
            continue
        total += 1
        delta = move.get("eval_delta_cp")
        if delta is None or delta >= -50:
            exploited += 1
    missed = total - exploited
    return {
        "found": exploited,
        "missed": missed,
        "rate": _pct(_safe_ratio(exploited, total)),
    }


def _tag_from_distribution(raw_data: dict, tag: str) -> dict[str, Any]:
    dist = raw_data.get("tag_distribution", {})
    info = dist.get(tag, {}) or {}
    count = info.get("count", 0) or 0
    ratio = info.get("ratio", 0.0) or 0.0
    return {"count": count, "ratio": _pct(ratio)}


def _style_section(
    raw_data: dict,
    gm_reference: dict | None,
    tag_map: dict[str, list[str]],
    *,
    include_total: bool = True,
) -> dict[str, Any]:
    section: dict[str, Any] = {}
    total_count = 0
    total_ratio = 0.0
    for key, tags in tag_map.items():
        rec = {"count": 0, "ratio": 0.0, "gm": 0.0}
        for tag in tags:
            data = _tag_from_distribution(raw_data, tag)
            rec["count"] += data["count"]
            rec["ratio"] += data["ratio"]
        rec["gm"] = _gm_avg_ratio(gm_reference, tags)
        section[key] = rec
        total_count += rec["count"]
        total_ratio += rec["ratio"]
    if include_total:
        section["total"] = {
            "count": total_count,
            "ratio": round(total_ratio, 1),
            "gm": _gm_avg_ratio(gm_reference, [t for tags in tag_map.values() for t in tags]),
        }
    return section


def _exchanges_data(raw_data: dict, gm_reference: dict | None) -> dict[str, Any]:
    tags = {
        "accurate": "accurate_knight_bishop_exchange",
        "inaccurate": "inaccurate_knight_bishop_exchange",
        "bad": "bad_knight_bishop_exchange",
    }
    data = {}
    total_count = 0
    total_ratio = 0.0
    for key, tag in tags.items():
        rec = _tag_from_distribution(raw_data, tag)
        total_count += rec["count"]
        total_ratio += rec["ratio"]
        gm_ratio = _gm_avg_ratio(gm_reference, [tag])
        data[key] = {"count": rec["count"], "ratio": rec["ratio"], "gm": gm_ratio}
    data["total"] = {
        "count": total_count,
        "ratio": round(total_ratio, 1),
        "gm": _gm_avg_ratio(gm_reference, tags.values()),
    }
    return data


def _forced_data(raw_data: dict, gm_reference: dict | None) -> dict[str, Any]:
    rec = _tag_from_distribution(raw_data, "forced_move")
    return {
        "count": rec["count"],
        "ratio": rec["ratio"],
        "gm": _gm_avg_ratio(gm_reference, ["forced_move"]),
    }


def _positions_data(raw_data: dict, gm_reference: dict | None) -> dict[str, Any]:
    winning = _tag_from_distribution(raw_data, "winning_position_handling")
    losing = _tag_from_distribution(raw_data, "losing_position_handling")
    return {
        "winning": {
            "count": winning["count"],
            "ratio": winning["ratio"],
            "gm": _gm_avg_ratio(gm_reference, ["winning_position_handling"]),
        },
        "losing": {
            "count": losing["count"],
            "ratio": losing["ratio"],
            "gm": _gm_avg_ratio(gm_reference, ["losing_position_handling"]),
        },
    }


def _opening_summary(raw_data: dict) -> dict[str, list]:
    try:
        import chess
        from chess.polyglot import opening_name as _polyglot_opening_name
    except Exception:  # pragma: no cover - optional dependency
        chess = None
        _polyglot_opening_name = None

    def infer_opening(game: dict) -> tuple[str, str]:
        """
        Return (line, variation) using PGN metadata fallback + polyglot name if available.
        """
        eco = (game.get("eco") or "Unknown").strip() or "Unknown"
        opening = (game.get("opening") or "").strip()
        variation = (game.get("variation") or "").strip()
        line = f"{eco} {opening}".strip()

        if chess and _polyglot_opening_name:
            try:
                board = chess.Board()
                for mv in game.get("moves", []):
                    uci = mv.get("uci")
                    if not uci:
                        continue
                    board.push_uci(uci)
                poly_name = _polyglot_opening_name(board)
                if poly_name:
                    # Use polyglot as line; keep PGN variation if present
                    line = poly_name
            except Exception:
                pass

        return line or "Unknown", variation

    buckets: Dict[str, Dict[tuple, Dict[str, Any]]] = {"white": {}, "black": {}}
    for game in raw_data.get("games", []):
        color = game.get("color")
        if color not in buckets:
            continue
        line, variation = infer_opening(game)
        key = (
            line,
            variation,
            (game.get("first_moves") or "").strip(),
        )
        bucket = buckets[color].setdefault(
            key,
            {"games": 0, "win": 0, "draw": 0, "loss": 0, "acc_sum": 0.0, "acc_games": 0},
        )
        bucket["games"] += 1
        result = game.get("result")
        if result in {"win", "draw", "loss"}:
            bucket[result] = bucket.get(result, 0) + 1
        # simple per-game accuracy approximation
        moves = [mv for mv in game.get("moves", []) if mv.get("eval_delta_cp") is not None]
        if moves:
            loss_sum = sum(max(-float(mv["eval_delta_cp"]), 0.0) for mv in moves)
            avg_loss = loss_sum / len(moves)
            score = max(0.0, 1.0 - avg_loss / 100.0)
            bucket["acc_sum"] += score
            bucket["acc_games"] += 1

    summary: Dict[str, list] = {"white": [], "black": []}
    for color, groups in buckets.items():
        for (line, variation, first_moves), data in groups.items():
            games_count = data["games"]
            summary[color].append(
                {
                    "line": line,
                    "variation": variation,
                    "games": games_count,
                    "win": _pct(_safe_ratio(data.get("win", 0), games_count)),
                    "draw": _pct(_safe_ratio(data.get("draw", 0), games_count)),
                    "loss": _pct(_safe_ratio(data.get("loss", 0), games_count)),
                    "accuracy": round(
                        data["acc_sum"] / data["acc_games"], 3
                    )
                    if data["acc_games"]
                    else None,
                    "first_moves": first_moves,
                }
            )
        summary[color].sort(key=lambda item: (-item["games"], item["line"]))
    return summary


def compute_fixed_data(raw_data: dict, gm_reference: dict | None = None) -> dict[str, Any]:
    """
    Build the complete fixed_data structure expected by the front-end.
    """
    games = raw_data.get("games", []) or []
    thresholds_cp = [100, 300, 500, 700]

    winrate = _winrate_by_color(games)
    accuracy = _accuracy_by_phase(games)
    advantage = _threshold_wdl_by_color(games, thresholds_cp, positive=True)
    defensive = _threshold_wdl_by_color(games, thresholds_cp, positive=False)
    volatility = _volatility_by_color(games)
    engine = _engine_quality(games)
    tactical = _tactical_conversion(games)
    exchanges = _exchanges_data(raw_data, gm_reference)
    forced = _forced_data(raw_data, gm_reference)
    positions = _positions_data(raw_data, gm_reference)
    openings = _opening_summary(raw_data)
    style_maneuver = _style_section(
        raw_data,
        gm_reference,
        {
            "constructive": ["constructive_maneuver"],
            "prepare": ["constructive_maneuver_prepare"],
            "neutral": ["neutral_maneuver"],
            "misplaced": ["misplaced_maneuver", "failed_maneuver"],
            "opening": ["maneuver_opening"],
        },
    )
    style_prophylaxis = _style_section(
        raw_data,
        gm_reference,
        {
            "direct": ["prophylactic_direct"],
            "latent": ["prophylactic_latent"],
            "meaningless": ["prophylactic_meaningless"],
            "failed": ["prophylactic_failed", "failed_prophylactic"],
        },
    )
    style_semantic_control = _style_section(
        raw_data,
        gm_reference,
        {
            "simplify": ["control_simplify"],
            "plankill": ["control_plan_kill"],
            "freeze": ["control_freeze_bind"],
            "blockade": ["control_blockade_passed"],
            "fileseal": ["control_file_seal"],
            "kingsafety": ["control_king_safety_shell"],
            "spaceclamp": ["control_space_clamp"],
            "regroup": ["control_regroup_consolidate"],
            "slowdown": ["control_slowdown"],
        },
    )
    style_cod = _style_section(
        raw_data,
        gm_reference,
        {
            "overall": ["control_over_dynamics"],
            "fileseal": ["control_file_seal"],
            "freeze": ["control_freeze_bind"],
            "kingsafety": ["control_king_safety_shell"],
            "regroup": ["control_regroup_consolidate"],
            "plankill": ["control_plan_kill"],
            "blockade": ["control_blockade_passed"],
            "simplify": ["control_simplify"],
            "spaceclamp": ["control_space_clamp"],
            "slowdown": ["control_slowdown"],
        },
        include_total=False,
    )
    style_initiative = _style_section(
        raw_data,
        gm_reference,
        {
            "attempt": ["initiative_attempt"],
            "deferred": ["deferred_initiative"],
            "premature": ["premature_attack"],
            "cfile": ["c_file_pressure"],
        },
        include_total=False,
    )
    style_tension = _style_section(
        raw_data,
        gm_reference,
        {
            "creation": ["tension_creation"],
            "neutral": ["neutral_tension_creation"],
        },
        include_total=False,
    )
    style_structural = _style_section(
        raw_data,
        gm_reference,
        {
            "integrity": ["structural_integrity"],
            "dynamic": ["structural_compromise_dynamic"],
            "static": ["structural_compromise_static"],
        },
        include_total=False,
    )
    style_sacrifice = _style_section(
        raw_data,
        gm_reference,
        {
            "tactical": ["tactical_sacrifice"],
            "positional": ["positional_sacrifice"],
            "inaccurate": ["inaccurate_tactical_sacrifice"],
            "speculative": ["speculative_sacrifice"],
            "desperate": ["desperate_sacrifice"],
            "combination": ["tactical_combination_sacrifice"],
            "init": ["tactical_initiative_sacrifice"],
            "structure": ["positional_structure_sacrifice"],
            "space": ["positional_space_sacrifice"],
        },
    )

    # Placeholder accuracy comparison: mirror player data until peer/GM sources exist.
    accuracy_comparison = {
        phase: {
            "player": accuracy.get(phase, {}).get("score"),
            "peer": None,
            "gm": None,
        }
        for phase in ("overall", "opening", "middlegame", "endgame")
    }

    return {
        "winrate": winrate,
        "accuracy": accuracy,
        "accuracy_comparison": accuracy_comparison,
        "advantage": advantage,
        "defensive": defensive,
        "volatility": volatility,
        "engine": engine,
        "tactical": tactical,
        "exchanges": exchanges,
        "forced": forced,
        "positions": positions,
        "openings": openings,
        "style_maneuver": style_maneuver,
        "style_prophylaxis": style_prophylaxis,
        "style_semantic_control": style_semantic_control,
        "style_control_over_dynamics": style_cod,
        "style_initiative": style_initiative,
        "style_tension": style_tension,
        "style_structural": style_structural,
        "style_sacrifice": style_sacrifice,
    }
