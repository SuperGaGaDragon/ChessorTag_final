"""
Helper utilities to build prompts, call the LLM, and render HTML sections.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any, Dict, List

import markdown

from style_report.llm_client import call_llm


SECTION_PROMPTS: Dict[str, str] = {
    "performance_profile": "performance_profile.md",
    "overall_synthesis": "overall_synthesis.md",
    "opening_repertoire": "opening_repertoire.md",
    "training_recommendations": "training_recommendations.md",
    "opponent_preparation": "opponent_preparation.md",
}

STYLE_PROMPTS: List[tuple[str, str, str]] = [
    ("maneuver", "style_maneuver.md", "Maneuvering"),
    ("prophylaxis", "style_prophylaxis.md", "Prophylaxis"),
    ("semantic_control", "style_semantic_control.md", "Semantic Control"),
    ("control_over_dynamics", "style_cod.md", "Control Over Dynamics"),
    ("initiative", "style_initiative.md", "Initiative"),
    ("tension", "style_tension.md", "Tension Management"),
    ("structural", "style_structural.md", "Structural Play"),
    ("sacrifice", "style_sacrifice.md", "Sacrificial Play"),
    ("exchanges_forced", "style_exchanges_forced.md", "Exchanges & Forced Moves"),
]


def _build_prompt(template_path: Path, profile: dict) -> str:
    template = template_path.read_text(encoding="utf-8").strip()
    payload = json.dumps(profile, indent=2)
    return f"{template}\n\n[PLAYER_PROFILE_JSON]\n{payload}"


def _run_prompt(template_path: Path, profile: dict) -> str:
    if not template_path.exists():
        return f"LLM analysis unavailable; prompt missing: {template_path.name}"
    prompt = _build_prompt(template_path, profile)
    try:
        return call_llm(prompt)
    except Exception as exc:  # pragma: no cover - surfaced to HTML for debugging
        return f"LLM analysis unavailable; check API key or credentials. Details: {exc}"


def generate_analysis(profile: dict, prompts_dir: Path) -> dict:
    analysis: Dict[str, Any] = {}
    for key, filename in SECTION_PROMPTS.items():
        analysis[key] = _run_prompt(prompts_dir / filename, profile)

    style_sections: Dict[str, Any] = {}
    order: List[str] = []
    for key, filename, title in STYLE_PROMPTS:
        order.append(key)
        style_sections[key] = {
            "title": title,
            "markdown": _run_prompt(prompts_dir / filename, profile),
        }
    analysis["style_parameters"] = {"order": order, "sections": style_sections}
    return analysis


def _render_markdown(md_text: str) -> str:
    md_text = (md_text or "").strip()
    if not md_text:
        return "<p>LLM analysis unavailable.</p>"
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )


def render_style_parameters(style_payload: Dict[str, Any]) -> str:
    if not style_payload:
        return "<p>No style analysis available.</p>"

    sections = style_payload.get("sections") or {}
    order = style_payload.get("order") or list(sections.keys())
    blocks: List[str] = []
    for key in order:
        section = sections.get(key)
        if not section:
            continue
        title = section.get("title") or key.replace("_", " ").title()
        blocks.append(f'<div class="style-block" id="style-{escape(key)}">')
        blocks.append(f"<h3>{escape(title)}</h3>")
        blocks.append(_render_markdown(section.get("markdown", "")))
        blocks.append("</div>")
    return "\n".join(blocks) if blocks else "<p>No style analysis available.</p>"


def _extract_gm_similarities(analysis: dict) -> list[dict[str, str]]:
    """Extract top 3 similar GMs from the overall synthesis text."""
    overall_text = analysis.get("overall_synthesis", "")

    # GM name to photo mapping
    gm_photos = {
        "tigran petrosian": "Petrosian.jpg",
        "petrosian": "Petrosian.jpg",
        "garry kasparov": "Kasparov.jpg",
        "kasparov": "Kasparov.jpg",
        "mikhail tal": "Tal.jpg",
        "mihail tal": "Tal.jpg",
        "tal": "Tal.jpg",
        "bobby fischer": "Fischer.jpg",
        "fischer": "Fischer.jpg",
        "anatoly karpov": "Karpov.jpg",
        "karpov": "Karpov.jpg",
        "vladimir kramnik": "Kramnik.jpg",
        "kramnik": "Kramnik.jpg",
        "magnus carlsen": "Carlsen.jpg",
        "carlsen": "Carlsen.jpg",
        "levon aronian": "Aronian.jpg",
        "aronian": "Aronian.jpg",
    }

    # Try to extract GM names and similarity scores from text
    gm_cards = []
    import re

    # Look for patterns like "GM Name (X% similarity)" or "GM Name: X%" or "similar to GM Name"
    patterns = [
        r"([A-Z][a-z]+ [A-Z][a-z]+)\s*\((\d+)%",  # Name (85%)
        r"([A-Z][a-z]+ [A-Z][a-z]+)[\s:]+(\d+)%",  # Name: 85% or Name 85%
        r"similar to ([A-Z][a-z]+ [A-Z][a-z]+)\s*\((\d+)%",  # similar to Name (85%)
    ]

    for pattern in patterns:
        matches = re.findall(pattern, overall_text)
        for match in matches:
            if len(match) == 2:
                name, score = match
            else:
                continue

            name_lower = name.lower()
            photo = None
            for key, photo_file in gm_photos.items():
                if key in name_lower:
                    photo = photo_file
                    break

            # Only add if we found a matching photo and haven't added this GM yet
            if photo and not any(gm['name'] == name for gm in gm_cards) and len(gm_cards) < 3:
                gm_cards.append({
                    "name": name,
                    "score": f"{score}%",
                    "photo": photo
                })

        if len(gm_cards) >= 3:
            break

    # Fill with defaults if we don't have 3 GMs
    default_gms = [
        {"name": "Tigran Petrosian", "score": "Analysis in progress", "photo": "Petrosian.jpg"},
        {"name": "Anatoly Karpov", "score": "Analysis in progress", "photo": None},
        {"name": "Bobby Fischer", "score": "Analysis in progress", "photo": "Fischer.jpg"},
    ]

    while len(gm_cards) < 3:
        gm_cards.append(default_gms[len(gm_cards)])

    return gm_cards[:3]


def _render_gm_cards(gm_cards: list[dict[str, str]]) -> str:
    """Render GM similarity cards HTML."""
    cards_html = []
    for gm in gm_cards:
        photo = gm.get("photo")
        if photo:
            avatar_html = f'<div class="gm-avatar"><img src="../../assets/gm_photos/{escape(photo)}" alt="{escape(gm["name"])}" /></div>'
        else:
            initials = "".join(word[0] for word in gm["name"].split()[:2])
            avatar_html = f'<div class="gm-avatar">{escape(initials)}</div>'

        card_html = f'''<div class="gm-card">
              {avatar_html}
              <div>
                <div class="gm-name">{escape(gm["name"])}</div>
                <div class="gm-score">Similarity: {escape(gm["score"])}</div>
              </div>
            </div>'''
        cards_html.append(card_html)

    return "\n            ".join(cards_html)


def render_report_html(player_id: str, analysis: dict, template_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")

    # Extract GM similarities
    gm_cards = _extract_gm_similarities(analysis)
    gm_cards_html = _render_gm_cards(gm_cards)

    replacements = {
        "{{PLAYER_ID}}": escape(player_id),
        "{{GM_CARDS}}": gm_cards_html,
        "{{PERFORMANCE_PROFILE_HTML}}": _render_markdown(analysis.get("performance_profile", "")),
        "{{STYLE_PARAMETERS_HTML}}": render_style_parameters(analysis.get("style_parameters", {})),
        "{{OVERALL_SYNTHESIS_HTML}}": _render_markdown(analysis.get("overall_synthesis", "")),
        "{{OPENING_REPERTOIRE_HTML}}": _render_markdown(analysis.get("opening_repertoire", "")),
        "{{TRAINING_RECOMMENDATIONS_HTML}}": _render_markdown(analysis.get("training_recommendations", "")),
        "{{OPPONENT_PREPARATION_HTML}}": _render_markdown(analysis.get("opponent_preparation", "")),
    }

    html = template
    for needle, value in replacements.items():
        html = html.replace(needle, value)
    return html
