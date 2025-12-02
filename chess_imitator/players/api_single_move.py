# Bridge between the imitator candidates and the rule_tagger API.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

_RULE_TAGGER_PATH = Path(__file__).resolve().parent.parent / "rule_tagger_lichessbot"
if str(_RULE_TAGGER_PATH) not in sys.path:
    sys.path.insert(0, str(_RULE_TAGGER_PATH))

from rule_tagger_lichessbot.codex_utils import analyze_position


def _extract_tags_from_analysis(analysis: Dict[str, Any]) -> List[str]:
    tags_section = analysis.get("tags", {})
    if not isinstance(tags_section, dict):
        return []
    for bucket in ("primary", "active", "secondary"):
        value = tags_section.get(bucket)
        if isinstance(value, list) and value:
            return [str(tag) for tag in value]
    return []


def tag_single_move(
    fen: str,
    move_uci: str,
    engine_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Run the real rule_tagger on a single engine candidate.

    Returns a normalized result that includes the list of tags and the raw analysis.
    """
    engine_meta = engine_meta or {}
    engine_path = engine_meta.get("engine_path")

    analysis = analyze_position(fen, move_uci, engine_path=engine_path)
    tags = _extract_tags_from_analysis(analysis)

    return {
        "tags": tags,
        "analysis": analysis,
    }
