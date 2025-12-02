"""Batch tagger that applies rule_tagger2 to a list of engine candidates."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from players.api_single_move import tag_single_move

from rule_tagger_lichessbot.tag_postprocess import normalize_candidate_tags

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

_TAGGER_EMPTY = "_TAGGER_EMPTY"
_TAGGER_ERROR = "_TAGGER_ERROR"


def _collect_tags(result: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
    tags = result.get("tags", [])
    if isinstance(tags, list) and tags:
        return tags
    fallback = result.get("analysis", {}).get("tags", {})
    for bucket in ("primary", "active", "secondary"):
        values = fallback.get(bucket)
        if isinstance(values, list) and values:
            return values  # already list[str]
    existing = candidate.get("tags")
    if isinstance(existing, list) and existing:
        return existing
    return []


def tag_candidates_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tag every candidate move inside *payload* with rule_tagger2 tags.

    The payload should contain a FEN and a list of candidates similar to
    the output from a UCI engine running `multipv`.
    """
    fen = payload.get("fen", "")
    candidates = payload.get("candidates", [])
    tagged: List[Dict[str, Any]] = []
    for candidate in candidates:
        uci = candidate.get("uci")
        if not uci:
            logger.warning("Skipping candidate without a UCI string: %s", candidate)
            continue
        engine_meta = candidate.get("engine_meta")
        candidate_copy = dict(candidate)
        tags: List[str] = []
        analysis: Dict[str, Any] = {}
        try:
            result = tag_single_move(fen, uci, engine_meta=engine_meta)
        except Exception as exc:  # pragma: no cover (defensive logging)
            print(
                f"[TAGGER_BRIDGE] failed to tag {uci}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            tags = list(candidate_copy.get("tags", []))
            if _TAGGER_ERROR not in tags:
                tags.append(_TAGGER_ERROR)
        else:
            analysis = result.get("analysis", {})
            tags = _collect_tags(result, candidate_copy)
            if not tags:
                tags = [_TAGGER_EMPTY]
        candidate_copy["tags"] = normalize_candidate_tags(tags, analysis)
        tagged.append(candidate_copy)
    payload_copy = dict(payload)
    payload_copy["candidates"] = tagged
    return payload_copy


def _read_payload(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_payload(data: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def cli_main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Tag a JSON payload of candidate moves with the rule_tagger style tags."
    )
    parser.add_argument("input", type=Path, help="JSON file describing a FEN and move candidates.")
    parser.add_argument("output", type=Path, help="Path to write the tagged payload.")
    args = parser.parse_args(argv)
    payload = _read_payload(args.input)
    tagged = tag_candidates_payload(payload)
    _write_payload(tagged, args.output)
    logger.info("Tagged %d candidates from %s", len(tagged["candidates"]), args.input)


__all__ = ["tag_candidates_payload", "cli_main"]


if __name__ == "__main__":
    cli_main()
