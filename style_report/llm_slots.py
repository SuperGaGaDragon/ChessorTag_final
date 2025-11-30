"""
Generate `llm_slots` payloads for the Phase 2 report.
"""
from __future__ import annotations

from typing import Dict

from style_report.llm_client import call_llm


def run_llm_slots(prompts: Dict[str, str]) -> Dict[str, str]:
    """
    Execute prompts → HTML snippets map. Errors are captured per slot.
    """
    outputs: Dict[str, str] = {}
    for slot_id, prompt in prompts.items():
        try:
            outputs[slot_id] = call_llm(prompt)
        except Exception as exc:  # pragma: no cover - surfaced to client
            outputs[slot_id] = f"LLM analysis unavailable for {slot_id}: {exc}"
    return outputs
