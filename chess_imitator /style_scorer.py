"""Helpers to score engine candidates against a target player's style profile."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List

from rule_tagger_lichessbot.tag_postprocess import apply_forced_move_tag

try:
    # Support running as a module using package-style imports.
    from .move_logger import _log_move_decision  # type: ignore[import]
except ImportError:  # pragma: no cover - not needed when running as a package.
    from move_logger import _log_move_decision

_PLAYERS_DIR = Path(__file__).resolve().parent / "players"
_PROFILE_CACHE: Dict[str, Dict[str, Any]] = {}
_LOGGER = logging.getLogger(__name__)


def _get_failure_tag_names(style_profile: Dict[str, Any]) -> set[str]:
    """
    Defines which tags count as failures.
    Prefer explicit *failure_tags* when provided, otherwise use penalty tag keys.
    """
    penalty_tags: Dict[str, float] = style_profile.get("penalty_tags", {}) or {}
    failure_tags = style_profile.get("failure_tags")
    if isinstance(failure_tags, list):
        return set(failure_tags)
    return set(penalty_tags.keys())


def _compute_error_rate(style_profile: Dict[str, Any]) -> float:
    """
    Estimate the global mistake likelihood from a player's tag weights.
    """
    config = style_profile.get("config", {}) or {}
    tag_weights: Dict[str, float] = style_profile.get("tag_weights", {}) or {}
    if not tag_weights:
        return 0.0

    total_mass = sum(float(w or 0.0) for w in tag_weights.values())
    if total_mass <= 0.0:
        return 0.0

    failure_tag_names = _get_failure_tag_names(style_profile)
    failure_mass = 0.0
    for tag_name in failure_tag_names:
        failure_mass += float(tag_weights.get(tag_name, 0.0) or 0.0)

    if failure_mass <= 0.0:
        return 0.0

    raw_rate = failure_mass / total_mass
    multiplier = float(config.get("error_rate_multiplier", 1.0))
    error_rate = raw_rate * multiplier
    if error_rate < 0.0:
        return 0.0
    if error_rate > 0.5:
        return 0.5
    return error_rate


def _pick_failure_candidate(
    candidates: List[Dict[str, Any]],
    style_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Among failing candidates, pick one weighted by the configured failure distribution.
    """
    tag_weights: Dict[str, float] = style_profile.get("tag_weights", {}) or {}
    penalty_tags: Dict[str, float] = style_profile.get("penalty_tags", {}) or {}
    if not candidates or not tag_weights or not penalty_tags:
        return dict(random.choice(candidates)) if candidates else {}

    failure_tag_names = _get_failure_tag_names(style_profile)
    weights: List[float] = []
    for cand in candidates:
        cand_tags = cand.get("tags", []) or []
        mass = 0.0
        for tag in cand_tags:
            if tag in failure_tag_names:
                base = float(tag_weights.get(tag, 0.0) or 0.0)
                severity = float(penalty_tags.get(tag, 1.0) or 1.0)
                mass += base * severity
        weights.append(max(mass, 1e-9))

    total = sum(weights)
    if total <= 0.0:
        return dict(random.choice(candidates))

    probs = [w / total for w in weights]
    r = random.random()
    cumulative = 0.0
    for cand, prob in zip(candidates, probs):
        cumulative += prob
        if r <= cumulative:
            return dict(cand)

    return dict(candidates[-1])


def load_style_profile(name: str) -> Dict[str, Any]:
    """
    Load the style profile stored at *players/<name>.json*.
    """
    normalized = name.strip()
    if normalized in _PROFILE_CACHE:
        return _PROFILE_CACHE[normalized]
    path = _PLAYERS_DIR / f"{normalized}.json"
    _LOGGER.info("Loading style profile %s from %s", normalized, path)
    with path.open("r", encoding="utf-8") as handle:
        profile = json.load(handle)
    _PROFILE_CACHE[normalized] = profile
    return profile


def score_candidate(
    tags: List[str],
    sf_eval: float,
    style_profile: Dict[str, Any],
    best_eval: float,
) -> float:
    """
    Compute a higher-is-better score for the candidate identified by *tags* and *sf_eval*.
    """
    sf_eval = float(sf_eval if sf_eval is not None else 0.0)
    best_eval = float(best_eval if best_eval is not None else sf_eval)
    delta_cp = best_eval - sf_eval
    config = style_profile.get("config", {})
    min_eval_drop = float(config.get("min_eval_cp", 150))
    if delta_cp > min_eval_drop:
        return float("-inf")
    tag_weights = style_profile.get("tag_weights", {})
    penalty_tags = style_profile.get("penalty_tags", {})

    positive = sum(tag_weights.get(tag, 0.0) for tag in tags)
    negative = sum(penalty_tags.get(tag, 0.0) for tag in tags)
    style_score = positive - negative
    aggressiveness = float(config.get("aggressiveness", 1.0))
    base_weight = float(config.get("eval_weight", 0.001))
    agg_factor = max(aggressiveness, 0.001)
    penalty_weight = base_weight / agg_factor
    eval_penalty = delta_cp * penalty_weight
    return style_score - eval_penalty


def pick_best_move(payload_with_tags: Dict[str, Any], style_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pick the candidate move that best matches *style_profile*, possibly forcing a failure.
    """
    candidates = payload_with_tags.get("candidates", [])
    if not candidates:
        raise ValueError("Payload must contain at least one candidate move.")

    config = style_profile.get("config", {}) or {}
    deterministic = bool(config.get("deterministic", False))

    best_eval = max(
        float(candidate.get("sf_eval", 0.0) if candidate.get("sf_eval") is not None else 0.0)
        for candidate in candidates
    )

    scored: List[Dict[str, Any]] = []
    for candidate in candidates:
        candidate_copy = dict(candidate)
        score = score_candidate(
            tags=candidate_copy.get("tags", []),
            sf_eval=candidate_copy.get("sf_eval", 0.0),
            style_profile=style_profile,
            best_eval=best_eval,
        )
        candidate_copy["style_score"] = score
        scored.append(candidate_copy)

    failure_tag_names = _get_failure_tag_names(style_profile)
    failure_candidates: List[Dict[str, Any]] = [
        candidate
        for candidate in scored
        if float(candidate.get("style_score", float("-inf"))) != float("-inf")
        and any(tag in failure_tag_names for tag in (candidate.get("tags", []) or []))
    ]

    error_rate = 0.0 if deterministic else _compute_error_rate(style_profile)
    make_error = False
    if failure_candidates and error_rate > 0.0 and random.random() < error_rate:
        make_error = True

    if make_error:
        picked = _pick_failure_candidate(failure_candidates, style_profile)
    else:
        picked = max(scored, key=lambda c: float(c.get("style_score", float("-inf"))))

    forced_tags = apply_forced_move_tag(
        candidates,
        picked_uci=(picked.get("uci") or picked.get("move")),
    )
    if forced_tags is not None:
        picked["tags"] = forced_tags

    _log_move_decision(
        payload_with_tags=payload_with_tags,
        style_profile=style_profile,
        picked=picked,
        make_error=make_error,
        error_rate=error_rate,
    )

    return picked


__all__ = ["load_style_profile", "score_candidate", "pick_best_move"]
