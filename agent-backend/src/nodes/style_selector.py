from typing import Dict, Any
from ..graph.state import GraphState
from langchain_openai import ChatOpenAI
import json

def style_selector_node(state: GraphState) -> Dict[str, Any]:
    print("--- ART DIRECTOR ---")
    topic = state.get("topic") or state.get("user_input", "")
    outline = state.get("outline", {})
    intent_map = state.get("intent_map", {})

    style_catalog = [
        {
            "style_id": "EDITORIAL_MINIMAL",
            "fit": ["consulting", "strategy", "finance", "analysis"],
            "palette": {"bg": "#F8FAFC", "surface": "#FFFFFF", "text": "#0F172A", "accent": "#2563EB"},
            "fonts": {"heading": "Inter", "body": "Inter"},
            "rules": {"corner_radius": "12px", "shadow": "0 6px 24px rgba(15,23,42,0.08)"},
        },
        {
            "style_id": "VIVID_CREATIVE",
            "fit": ["art", "brand", "marketing", "design", "culture"],
            "palette": {"bg": "#0B1020", "surface": "#141A2E", "text": "#F8FAFC", "accent": "#A78BFA"},
            "fonts": {"heading": "Poppins", "body": "Inter"},
            "rules": {"corner_radius": "16px", "shadow": "0 10px 30px rgba(3,7,18,0.45)"},
        },
        {
            "style_id": "TECH_FUTURE",
            "fit": ["ai", "tech", "product", "startup", "engineering"],
            "palette": {"bg": "#020617", "surface": "#0F172A", "text": "#E2E8F0", "accent": "#22D3EE"},
            "fonts": {"heading": "Space Grotesk", "body": "Inter"},
            "rules": {"corner_radius": "10px", "shadow": "0 8px 26px rgba(15,23,42,0.4)"},
        },
    ]

    prompt = f"""
You are The Art Director.
Given topic, outline and intents, choose the best style from this catalog:
{json.dumps(style_catalog, ensure_ascii=False)}

Topic:
{topic}

Outline:
{json.dumps(outline, ensure_ascii=False)}

Intent map:
{json.dumps(intent_map, ensure_ascii=False)}

Return strict JSON:
{{
  "style_id": "string",
  "justification": "string",
  "palette": {{"bg":"#hex","surface":"#hex","text":"#hex","accent":"#hex"}},
  "fonts": {{"heading":"string","body":"string"}},
  "rules": {{"corner_radius":"string","shadow":"string","shape_language":"string"}},
  "contrast_ratio_target": ">=4.5"
}}
"""

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        response = llm.invoke(prompt)
        text = response.content.strip()
        start, end = text.find("{"), text.rfind("}")
        design_token = json.loads(text[start : end + 1])
    except Exception:
        default = style_catalog[0]
        design_token = {
            "style_id": default["style_id"],
            "justification": "Default clean style for broad readability.",
            "palette": default["palette"],
            "fonts": default["fonts"],
            "rules": {**default["rules"], "shape_language": "smooth_waves"},
            "contrast_ratio_target": ">=4.5",
        }

    return {"global_design_token": design_token}