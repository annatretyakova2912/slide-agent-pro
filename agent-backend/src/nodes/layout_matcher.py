"""
Template selector + layout orchestrator.

After Content Architect produces final copy + structure_hint per slide, this node:
1) loads your uploaded template catalog,
2) filters candidates that match the slide structure_hint,
3) asks an LLM to pick the best template id (or none),
4) resolves the .pptx path + slide_index for the renderer.

If no catalog entry matches or no file exists, falls back to internal layout ids
(plain box compiler).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..graph.state import GraphState
from ..services import template_catalog as tc


def _slide_body(slide: Dict[str, Any]) -> List[str]:
    raw = slide.get("body_content") or slide.get("body_bullets") or []
    if isinstance(raw, str):
        return [raw] if raw.strip() else []
    return [str(x) for x in raw if str(x).strip()]


def _pick_fallback_template_id(structure_hint: str, bullet_count: int) -> str:
    hint = (structure_hint or "").strip().lower()
    hint_map = {
        "hero": "HERO_TITLE_INSIGHT",
        "split_50_50": "SPLIT_SCREEN_50_50",
        "timeline": "PROCESS_TIMELINE",
        "process_steps": "PROCESS_TIMELINE",
        "feature_grid_3": "TOC_GRID_3_CIRCLES",
        "comparison_2col": "COMPARISON_2COL",
        "stats_focus": "STATS_FOCUS",
        "quote_focus": "QUOTE_FOCUS",
        "table_of_contents": "TOC_GRID_3_CIRCLES",
        "image_focus": "HERO_TITLE_INSIGHT",
    }
    if hint in hint_map:
        return hint_map[hint]
    if bullet_count <= 2:
        return "HERO_TITLE_INSIGHT"
    if bullet_count == 3:
        return "TOC_GRID_3_CIRCLES"
    if bullet_count >= 4:
        return "FOUR_POINTS_MATRIX"
    return "TITLE_BODY_DEFAULT"


def _parse_json_payload(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _llm_select_templates(
    slides_context: List[Dict[str, Any]],
    candidates_by_id: Dict[str, Dict[str, Any]],
) -> Dict[int, str]:
    """Returns slide_number -> catalog template id or 'none'."""
    if not candidates_by_id:
        return {}

    catalog_snippet = tc.format_catalog_for_llm(list(candidates_by_id.values()))
    system = (
        "You are a presentation template curator. You choose which uploaded master slide "
        "best fits each slide's structure_hint and copy. Pick ONLY ids from the catalog JSON. "
        "If nothing fits well, answer 'none' for that slide. Return strict JSON only."
    )
    human = f"""
Slides to match:
{json.dumps(slides_context, ensure_ascii=False, indent=2)}

Available catalog templates:
{catalog_snippet}

Return JSON:
{{
  "selections": [
    {{ "slide_number": 1, "catalog_template_id": "some_id_or_none", "rationale": "short" }}
  ]
}}
Rules:
- Every slide_number from the input must appear exactly once.
- catalog_template_id must be one of the catalog ids or the string "none".
- Prefer timelines for timeline/process_steps; comparison templates for comparison_2col; hero for hook/opening.
"""
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
        payload = _parse_json_payload(resp.content)
        out: Dict[int, str] = {}
        for row in payload.get("selections", []):
            num = row.get("slide_number")
            tid = row.get("catalog_template_id", "none")
            if isinstance(num, (int, float)):
                out[int(num)] = str(tid).strip() if tid is not None else "none"
        return out
    except Exception:
        return {}


def layout_matcher_node(state: GraphState) -> Dict[str, Any]:
    print("--- TEMPLATE + LAYOUT ORCHESTRATOR ---")
    copydeck = state.get("copydeck", {}) or {}
    slides_in = copydeck.get("slides", []) or []
    style = state.get("global_design_token", {})
    feedback = state.get("quality_report", {}).get("issues", [])

    # Candidate templates per deck: union of matches per slide, capped for the LLM context
    seen_ids: Dict[str, Dict[str, Any]] = {}
    all_entries = tc.list_templates()
    for slide in slides_in:
        hint = (slide.get("structure_hint") or "").strip().lower()
        matched = tc.filter_by_structure_hint(hint) if hint else []
        pool = matched if matched else all_entries[:18]
        for entry in pool:
            eid = entry.get("id")
            if eid:
                seen_ids[eid] = entry

    slides_context: List[Dict[str, Any]] = []
    for slide in slides_in:
        slides_context.append(
            {
                "slide_number": slide.get("slide_number"),
                "title": slide.get("title", ""),
                "subtitle": slide.get("subtitle", ""),
                "structure_hint": slide.get("structure_hint", ""),
                "intent": slide.get("intent", ""),
                "bullet_count": len(_slide_body(slide)),
                "visual_instructions": slide.get("visual_instructions", ""),
            }
        )

    llm_choices = _llm_select_templates(slides_context, seen_ids) if seen_ids else {}

    slides_layout: List[Dict[str, Any]] = []
    for slide in slides_in:
        slide_number = slide.get("slide_number")
        structure_hint = slide.get("structure_hint", "") or ""
        body = _slide_body(slide)
        local_feedback = [i for i in feedback if i.get("slide_number") == slide_number]

        chosen_id = llm_choices.get(slide_number, "none")
        catalog_entry = seen_ids.get(chosen_id) if chosen_id and chosen_id != "none" else None
        pptx_path: str | None = None
        slide_index = 0
        if catalog_entry:
            resolved = tc.resolve_pptx_path(catalog_entry)
            slide_index = int(catalog_entry.get("slide_index", 0))
            if resolved and os.path.isfile(resolved):
                pptx_path = resolved
            else:
                catalog_entry = None

        fallback_id = _pick_fallback_template_id(structure_hint, len(body))

        slots: Dict[str, Any] = {
            "title": slide.get("title", ""),
            "subtitle": slide.get("subtitle", ""),
            "body": body,
            "slogan": slide.get("slogan", ""),
            "visual_instructions": slide.get("visual_instructions", ""),
        }

        slides_layout.append(
            {
                "slide_number": slide_number,
                "template_id": fallback_id,
                "catalog_template_id": chosen_id if pptx_path else None,
                "template_pptx_path": pptx_path,
                "template_slide_index": slide_index,
                "structure_hint": structure_hint,
                "intent": slide.get("intent", ""),
                "rationale": (
                    f"Catalog template '{chosen_id}'"
                    if pptx_path
                    else f"Fallback layout '{fallback_id}' (no catalog match or missing file)."
                ),
                "layout_constraints": {
                    "balance_rule": "distribute visual weight; preserve margins",
                    "min_whitespace_ratio": 0.18,
                    "feedback_applied": [f.get("recommendation", "") for f in local_feedback],
                },
                "slots": slots,
            }
        )

    layout_plan = {
        "style_id": style.get("style_id", "EDITORIAL_MINIMAL"),
        "slides": slides_layout,
    }
    return {"layout_plan": layout_plan}
