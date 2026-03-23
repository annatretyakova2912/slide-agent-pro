from typing import Dict, Any
from ..graph.state import GraphState
from urllib.parse import quote_plus

def asset_scouter_node(state: GraphState) -> Dict[str, Any]:
    print("--- ASSET SCOUTER ---")
    copydeck = state.get("copydeck", {})
    style = state.get("global_design_token", {})
    intent_map = state.get("intent_map", {})
    accent = style.get("palette", {}).get("accent", "#2563EB")
    intent_by_slide = {
        entry.get("slide_number"): entry for entry in intent_map.get("slides", [])
    }

    asset_slides = []
    for slide in copydeck.get("slides", []):
        slide_number = slide.get("slide_number")
        intent = intent_by_slide.get(slide_number, {})
        title = slide.get("title", "presentation")
        subtitle = slide.get("subtitle", "")
        query = quote_plus(f"{title} {subtitle}".strip())
        image_url = f"https://source.unsplash.com/1600x900/?{query}"

        icon_ids = []
        body_lines = slide.get("body_content") or slide.get("body_bullets") or []
        text_blob = " ".join([title, subtitle] + list(body_lines)).lower()
        keyword_icon_map = {
            "growth": "trending-up",
            "finance": "landmark",
            "strategy": "compass",
            "team": "users",
            "data": "database",
            "ai": "bot",
            "quality": "badge-check",
            "process": "workflow",
        }
        for keyword, icon in keyword_icon_map.items():
            if keyword in text_blob and icon not in icon_ids:
                icon_ids.append(icon)
        if not icon_ids:
            icon_ids = ["sparkles"]

        asset_slides.append(
            {
                "slide_number": slide_number,
                "image_url": image_url,
                "image_prompt": (
                    f"Editorial visual for a {slide.get('intent', intent.get('slide_intent', 'insight'))} "
                    f"({slide.get('structure_hint', '')}) slide about {title}, "
                    f"clean composition, no text in image, accent {accent}"
                ),
                "icon_ids": icon_ids[:3],
                "decorations": ["mesh-gradient", "soft-noise-texture"],
                "asset_policy": {
                    "license": "unsplash",
                    "placement_mode": (
                        "image_mask_shape" if slide.get("structure_hint") == "hero" else "inline_rect"
                    ),
                },
            }
        )

    return {"asset_plan": {"slides": asset_slides}}
