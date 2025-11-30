"""
Lightweight OpenAI client wrapper for style_report.
"""
from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

MODEL_NAME = os.getenv("STYLE_REPORT_MODEL", "gpt-5.1")
API_KEY = os.getenv("OPENAI_API_KEY")

_client = OpenAI(api_key=API_KEY) if API_KEY else None


def call_llm(prompt: str) -> str:
    if _client is None:
        return "LLM call skipped: OPENAI_API_KEY not set."

    system_message = (
        "You are a professional chess coach and style analyst. "
        "CRITICAL: When comparing players to GMs (Petrosian, Kasparov, Fischer, Tal, etc.), "
        "you MUST use ONLY the GM metrics data provided in the user's JSON input. "
        "DO NOT invent, guess, or use GM statistics from your training data. "
        "Only cite GM ratios that are explicitly present in the provided JSON data. "
        "If a specific GM metric is not in the JSON, do NOT make that comparison."
    )

    resp: Any = _client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()
