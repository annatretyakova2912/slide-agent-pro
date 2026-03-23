from typing import Dict, Any, List
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..graph.state import GraphState


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


def _compress_bullets(bullets: List[str]) -> List[str]:
    cleaned = []
    for bullet in bullets[:4]:
        words = bullet.split()
        if len(words) > 12:
            bullet = " ".join(words[:12]).rstrip(",.;:") + "..."
        cleaned.append(bullet)
    return cleaned


def copywriter_intent_matcher_node(state: GraphState) -> Dict[str, Any]:

    """
    # Agent #2 : Copywriter & Intent Matcher 
    The Content Architect agent is responsible for writing concise visual-first copy for each slide and selecting the most creative and effective slide structure.
    Takes outline and quality_report as input
    Returns a JSON object with the slide-by-slide copy and the slide-by-slide structure.
    """

    print("--- CONTENT ARCHITECT ---")
    outline = state.get("outline", {})
    feedback = state.get("quality_report", {}).get("issues", [])
    additional_information = state.get("additional_information", "")
    
    system_prompt = (
        "You are the Content Architect. Your role is to write high-impact, visual-first copy "
        "and simultaneously select the most creative and effective slide structure. "
        "You must ensure the text perfectly fits the chosen layout. Return strict JSON only."
        f"Make sure you take into account the {additional_information} when you write the copy."
    )

    human_prompt = f"""
        Outline: {json.dumps(outline, ensure_ascii=False)}
        Feedback: {json.dumps(feedback, ensure_ascii=False)}

        TASK:
        1. For each slide in the outline, select the best creative structure from this list: 
        [hero, split_50_50, timeline, table_of_contents, comparison_2col, feature_grid_3, stats_focus, quote_focus, process_steps, image_focus].
        2. For each slide in the outline, write the final copy (Title, Subtitle, Body) based on the selected structure. 
        For example, if it's the title slide, keep the title of the presentatin and maybe add a subtitle if needed.
        If it's a timeline, keep all the dates and events and make sure there are short descriptions of the events if needed.

        RULES:
        - The slides should be more concise than the given text 
        (max 80 words per slide body, unless you are creating a detailed timeline 
        or unless the additional_information wants slides to be more detailed)
        - Make sure you don't miss out any important content from the outline.
        - If comparing pros/cons -> use 'comparison_2col'.
        - If listing steps or history -> use 'timeline' or 'process_steps'.
        - If it's the start -> use 'table_of_contents' or 'hero'.
        - Keep copy extremely brief: Title < 8 words, Bullets < 20 words.
        - Ensure 'structure_hint' matches the complexity of the 'body_content'.
        - Make sure you take into account the {additional_information} when you write the copy.

        Return JSON:
        {{
        "slides": [
            {{
            "slide_number": 1,
            "title": "string",
            "subtitle": "string",
            "body_content": ["string"],
            "intent": "hook",
            "structure_hint": "hero",
            "visual_instructions": "e.g., Use a circular mask for images, place text on the left"
            }}
        ]
        }}
        """

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        response = llm.invoke([
            SystemMessage(content=system_prompt), 
            HumanMessage(content=human_prompt)
        ])
        # On utilise ton parser existant
        payload = _parse_json_payload(response.content)
        
        # Post-processing pour garantir la brièveté (ta fonction _compress_bullets)
        for slide in payload.get("slides", []):
            slide["body_content"] = _compress_bullets(slide.get("body_content", []))
            
    except Exception as e:
        print(f"Error in Content Architect: {e}")
        # Fallback simplifié
        payload = {"slides": [{"slide_number": 1, "title": "Error", "structure_hint": "hero"}]}

    return {"copydeck": payload, "intent_map": payload} # On remplit les deux clés pour la compatibilité du graphe