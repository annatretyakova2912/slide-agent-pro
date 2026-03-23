from typing import Any, Dict

from ..graph.state import GraphState


def rendering_orchestrator_node(state: GraphState) -> Dict[str, Any]:
    print("--- RENDERING ORCHESTRATOR ---")
    style = state.get("global_design_token", {})
    layout = state.get("layout_plan", {})
    assets = state.get("asset_plan", {})

    asset_by_slide = {
        slide.get("slide_number"): slide for slide in assets.get("slides", [])
    }
    rendered_slides = []
    for layout_slide in layout.get("slides", []):
        slide_number = layout_slide.get("slide_number")
        slide_assets = asset_by_slide.get(slide_number, {})
        slots = dict(layout_slide.get("slots", {}))
        # Normalize body key for downstream QA / compiler
        if "body" not in slots and slots.get("body_content") is not None:
            slots["body"] = slots["body_content"]

        rendered_slides.append(
            {
                "slide_number": slide_number,
                "template_id": layout_slide.get("template_id"),
                "catalog_template_id": layout_slide.get("catalog_template_id"),
                "template_pptx_path": layout_slide.get("template_pptx_path"),
                "template_slide_index": layout_slide.get("template_slide_index", 0),
                "structure_hint": layout_slide.get("structure_hint"),
                "slots": slots,
                "assets": slide_assets,
            }
        )

    css_variables = {
        "--color-bg": style.get("palette", {}).get("bg", "#F8FAFC"),
        "--color-surface": style.get("palette", {}).get("surface", "#FFFFFF"),
        "--color-text": style.get("palette", {}).get("text", "#0F172A"),
        "--color-accent": style.get("palette", {}).get("accent", "#2563EB"),
        "--font-heading": style.get("fonts", {}).get("heading", "Inter"),
        "--font-body": style.get("fonts", {}).get("body", "Inter"),
        "--radius": style.get("rules", {}).get("corner_radius", "12px"),
        "--shadow": style.get("rules", {}).get("shadow", "0 6px 24px rgba(15,23,42,0.08)"),
    }

    rendered = {
        "engine": "react-tailwind",
        "design_token": style,
        "css_variables": css_variables,
        "slides": rendered_slides,
    }
    return {"rendered_presentation": rendered}
