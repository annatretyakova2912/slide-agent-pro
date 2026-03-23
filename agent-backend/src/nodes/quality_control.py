from typing import Dict, Any
from ..graph.state import GraphState


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = (value or "").strip().lstrip("#")
    if len(v) != 6:
        return (15, 23, 42)
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    l1 = _relative_luminance(_hex_to_rgb(hex_a))
    l2 = _relative_luminance(_hex_to_rgb(hex_b))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def quality_control_node(state: GraphState) -> Dict[str, Any]:
    print("--- VISUAL QA CRITIC ---")
    rendered = state.get("rendered_presentation", {})
    current_round = state.get("revision_count", 0)
    max_rounds = state.get("max_revision_rounds", 2)
    issues = []

    for slide in rendered.get("slides", []):
        slide_number = slide.get("slide_number")
        slots = slide.get("slots", {}) or {}
        body = slots.get("body") or slots.get("body_content") or []
        body_word_count = sum(len(str(item).split()) for item in body)
        if body_word_count > 40:
            issues.append(
                {
                    "slide_number": slide_number,
                    "severity": "high",
                    "issue": f"Body text too long ({body_word_count} words).",
                    "recommendation": "Shorten bullets and keep one idea per bullet.",
                    "agent": "copywriter_intent_matcher",
                }
            )
        if len(body) > 5:
            issues.append(
                {
                    "slide_number": slide_number,
                    "severity": "medium",
                    "issue": f"Too many bullet lines ({len(body)}).",
                    "recommendation": "Keep max 4 bullets to preserve white space.",
                    "agent": "copywriter_intent_matcher",
                }
            )

        text_color = rendered.get("css_variables", {}).get("--color-text", "#0F172A")
        bg_color = rendered.get("css_variables", {}).get("--color-bg", "#F8FAFC")
        ratio = _contrast_ratio(text_color, bg_color)
        if ratio < 4.5:
            issues.append(
                {
                    "slide_number": slide_number,
                    "severity": "high",
                    "issue": f"Insufficient text/background contrast ({ratio:.2f}:1).",
                    "recommendation": "Use contrast ratio >= 4.5:1.",
                    "agent": "style_selector",
                }
            )

        title_len = len(str(slide.get("slots", {}).get("title", "")).split())
        if title_len > 10:
            issues.append(
                {
                    "slide_number": slide_number,
                    "severity": "medium",
                    "issue": f"Title too long ({title_len} words).",
                    "recommendation": "Limit title to <=10 words.",
                    "agent": "copywriter_intent_matcher",
                }
            )

    needs_revision = len(issues) > 0 and current_round < max_rounds
    next_action = issues[0]["agent"] if needs_revision else "done"

    quality_report = {
        "status": "needs_revision" if needs_revision else "approved",
        "issues": issues,
    }

    return {
        "quality_report": quality_report,
        "needs_revision": needs_revision,
        "next_action": next_action,
        "revision_count": current_round + (1 if needs_revision else 0),
    }

    