"""
Compute aggregated metrics from raw.json payload.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    try:
        return float(numerator) / float(denominator) if denominator else 0.0
    except ZeroDivisionError:
        return 0.0


def _result_buckets() -> dict[str, int]:
    return {"win": 0, "loss": 0, "draw": 0, "unknown": 0}


def _gather_moves(games: Iterable[dict]) -> Iterable[tuple[dict, dict]]:
    for game in games:
        for move in game.get("moves", []):
            yield game, move


@dataclass
class AccuracyBucket:
    total_moves: int = 0
    cp_loss_sum: float = 0.0

    def add_move(self, eval_delta_cp: Optional[float]) -> None:
        if eval_delta_cp is None:
            return
        self.total_moves += 1
        loss = max(-float(eval_delta_cp), 0.0)
        self.cp_loss_sum += loss

    def to_dict(self) -> dict:
        if self.total_moves == 0:
            return {"moves": 0, "avg_loss_cp": None, "score": None}
        avg_loss = self.cp_loss_sum / self.total_moves
        score = max(0.0, 1.0 - avg_loss / 100)
        return {"moves": self.total_moves, "avg_loss_cp": round(avg_loss, 2), "score": round(score, 3)}


def _winrate(games: List[dict]) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = {
        "white": {"games": 0, "results": _result_buckets(), "opponent_elos": []},
        "black": {"games": 0, "results": _result_buckets(), "opponent_elos": []},
        "total": {"games": 0, "results": _result_buckets(), "opponent_elos": []},
    }
    for game in games:
        color = game.get("color", "unknown")
        result = game.get("result", "unknown")
        opp_elo = game.get("opponent_elo")
        targets = ["total"]
        if color in ("white", "black"):
            targets.append(color)
        for key in targets:
            bucket = buckets[key]
            bucket["games"] += 1
            bucket["results"][result] = bucket["results"].get(result, 0) + 1
            if isinstance(opp_elo, int):
                bucket["opponent_elos"].append(opp_elo)

    def finalize(bucket: dict) -> dict:
        games_count = bucket["games"] or 0
        wins = bucket["results"].get("win", 0)
        draws = bucket["results"].get("draw", 0)
        losses = bucket["results"].get("loss", 0)
        avg_elo = round(sum(bucket["opponent_elos"]) / len(bucket["opponent_elos"]), 1) if bucket["opponent_elos"] else None
        return {
            "games": games_count,
            "win": _safe_ratio(wins, games_count),
            "draw": _safe_ratio(draws, games_count),
            "loss": _safe_ratio(losses, games_count),
            "avg_opponent_elo": avg_elo,
        }

    return {key: finalize(bucket) for key, bucket in buckets.items()}


def _accuracy(games: List[dict]) -> dict[str, Any]:
    buckets: dict[str, AccuracyBucket] = {
        "overall": AccuracyBucket(),
        "opening": AccuracyBucket(),
        "middlegame": AccuracyBucket(),
        "endgame": AccuracyBucket(),
        "queenful": AccuracyBucket(),
        "queenless": AccuracyBucket(),
    }

    for _, move in _gather_moves(games):
        phase = (move.get("phase") or "unknown").lower()
        has_queen = move.get("has_queen")
        delta = move.get("eval_delta_cp")
        buckets["overall"].add_move(delta)
        if phase in buckets:
            buckets[phase].add_move(delta)
        if has_queen is True:
            buckets["queenful"].add_move(delta)
        elif has_queen is False:
            buckets["queenless"].add_move(delta)

    return {name: bucket.to_dict() for name, bucket in buckets.items()}


def _threshold_outcomes(games: List[dict], thresholds: list[int]) -> dict[str, Any]:
    positive = {thr: _result_buckets() for thr in thresholds}
    negative = {thr: _result_buckets() for thr in thresholds}

    for game in games:
        cp_before_values = [mv.get("cp_before") for mv in game.get("moves", []) if mv.get("cp_before") is not None]
        if not cp_before_values:
            continue
        max_cp = max(cp_before_values)
        min_cp = min(cp_before_values)
        result = game.get("result", "unknown")
        for thr in thresholds:
            if max_cp >= thr:
                positive[thr][result] = positive[thr].get(result, 0) + 1
            if min_cp <= -thr:
                negative[thr][result] = negative[thr].get(result, 0) + 1

    def format_bucket(bucket: dict) -> dict:
        total = sum(bucket.values())
        return {
            "games": total,
            "win": _safe_ratio(bucket.get("win", 0), total),
            "draw": _safe_ratio(bucket.get("draw", 0), total),
            "loss": _safe_ratio(bucket.get("loss", 0), total),
        }

    return {
        "advantage_conversion": {f"+{thr}": format_bucket(bucket) for thr, bucket in positive.items()},
        "defensive_resilience": {f"-{thr}": format_bucket(bucket) for thr, bucket in negative.items()},
    }


def _volatility(games: List[dict]) -> dict[str, Any]:
    buckets = Counter()
    for game in games:
        evaluations = [mv.get("cp_before") for mv in game.get("moves", []) if mv.get("cp_before") is not None]
        if not evaluations:
            continue
        result = game.get("result", "unknown")
        max_cp = max(evaluations)
        min_cp = min(evaluations)
        span = max_cp - min_cp

        if result == "win" and min_cp >= 100:
            buckets["smooth_crush"] += 1
        elif result == "loss" and max_cp <= -100:
            buckets["smooth_crushed"] += 1
        elif result == "draw" and span <= 80:
            buckets["high_precision_draw"] += 1
        elif span <= 200:
            buckets["small_swings"] += 1
        else:
            buckets["big_swings"] += 1

    total_games = sum(buckets.values()) or 1
    return {label: {"games": count, "ratio": _safe_ratio(count, total_games)} for label, count in buckets.items()}


def _move_quality(games: List[dict]) -> dict[str, Any]:
    thresholds = {
        "inaccuracy": -50,
        "mistake": -100,
        "blunder": -300,
    }
    counts = Counter()
    total = 0
    for _, move in _gather_moves(games):
        delta = move.get("eval_delta_cp")
        if delta is None:
            continue
        total += 1
        if delta >= thresholds["inaccuracy"]:
            counts["best_or_ok"] += 1
        elif delta >= thresholds["mistake"]:
            counts["inaccuracy"] += 1
        elif delta >= thresholds["blunder"]:
            counts["mistake"] += 1
        else:
            counts["blunder"] += 1

    return {
        "total_moves": total,
        "best_or_ok": _safe_ratio(counts["best_or_ok"], total),
        "inaccuracy": _safe_ratio(counts["inaccuracy"], total),
        "mistake": _safe_ratio(counts["mistake"], total),
        "blunder": _safe_ratio(counts["blunder"], total),
    }


def _tactics(games: List[dict]) -> dict[str, Any]:
    total = 0
    exploited = 0
    missed = 0
    for _, move in _gather_moves(games):
        tags = [t.lower() for t in move.get("tags", [])]
        if not any("tactic" in t for t in tags):
            continue
        total += 1
        delta = move.get("eval_delta_cp")
        if delta is None or delta >= -50:
            exploited += 1
        else:
            missed += 1
    return {
        "total": total,
        "exploited": exploited,
        "missed": missed,
        "exploited_ratio": _safe_ratio(exploited, total),
        "missed_ratio": _safe_ratio(missed, total),
    }


def _tag_ratio(games: List[dict], tag_names: Iterable[str]) -> dict[str, Any]:
    counts = Counter()
    total_moves = 0
    for _, move in _gather_moves(games):
        total_moves += 1
        tags = set(move.get("tags", []))
        for tag in tag_names:
            if tag in tags:
                counts[tag] += 1
    return {
        "counts": dict(counts),
        "ratios": {tag: _safe_ratio(counts.get(tag, 0), total_moves) for tag in tag_names},
        "total_moves": total_moves,
    }


def _winning_losing_handling(games: List[dict]) -> dict[str, Any]:
    tags = ("winning_position_handling", "losing_position_handling")
    data = _tag_ratio(games, tags)
    return {
        "total_moves": data["total_moves"],
        "counts": data["counts"],
        "ratios": data["ratios"],
    }


def compute_metrics(raw_data: dict) -> dict[str, Any]:
    games = raw_data.get("games", []) or []
    thresholds = [100, 300, 500, 700]

    metrics: Dict[str, Any] = {}
    metrics["winrate"] = _winrate(games)
    metrics["accuracy"] = _accuracy(games)
    metrics.update(_threshold_outcomes(games, thresholds))
    metrics["volatility"] = _volatility(games)
    metrics["move_quality"] = _move_quality(games)
    metrics["tactics"] = _tactics(games)
    metrics["exchange_family"] = _tag_ratio(
        games,
        ("accurate_knight_bishop_exchange", "inaccurate_knight_bishop_exchange", "bad_knight_bishop_exchange"),
    )
    metrics["forced_moves"] = _tag_ratio(games, ("forced_move",))
    metrics["winning_losing_handling"] = _winning_losing_handling(games)

    return metrics

