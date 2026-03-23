from typing import Dict, Any
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


def strategist_node(state: GraphState) -> Dict[str, Any]:

    """
    Agent #1: Strategist
    The Strategist agent is responsible for creating a clear slide-by-slide intent outline from user content.
    Takes user_input, desires_count and additional_information as input 
    Returns a JSON object with the slide-by-slide intent outline.
    """

    print("--- STRATEGIST ---")
    source_text = state.get("user_input") or state.get("topic") or ""
    desired_count = state.get("desired_slide_count", 7)
    audience = state.get("audience", "general")
    additional_information = state.get("additional_information", "")

    system_prompt = (
        "You are The Strategist agent for slide generation. "
        "Your job is to create a clear slide-by-slide intent outline from user content. "
        "Make sure you keep all the important details, the slides cannot lose any important content."
        "Do not write final slide copy. Return strict JSON only."
    )
    human_prompt = f"""
Create a presentation outline from this input :
\"\"\"{source_text}\"\"\"

Audience: {audience}
Target slide count: {desired_count}
Additional information: {additional_information}

Constraints:
- Keep exactly {desired_count} slides unless the content strongly requires +/- 1.
- Include a heading slide with the title of the presentation.
- Each slide must include: slide_number, title, objective, intent_type, key_points.
- key_points must be concise and max 4 items.
- intent_type examples: heading, table of contents, hook, problem, insight, solution, process, proof, call_to_action, comparison, timeline / biography, conclusion.
- Keep narrative flow coherent from intro to conclusion.
- Make sure you pay attention to the {additional_information} when you create the slides. 

Return this JSON schema:
{{
  "presentation_goal": "string",
  "narrative_arc": "string",
  "slides": [
    {{
      "slide_number": 1,
      "title": "string",
      "objective": "string",
      "intent_type": "string",
      "key_points": ["string"]
    }}
  ]
}}
"""

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        )
        outline = _parse_json_payload(response.content)
    except Exception:
        fallback_slides = []
        for i in range(1, desired_count + 1):
            fallback_slides.append(
                {
                    "slide_number": i,
                    "title": f"Slide {i}",
                    "objective": "Clarify one core message.",
                    "intent_type": "insight" if i != desired_count else "call_to_action",
                    "key_points": ["Main point", "Supporting detail"],
                }
            )
        outline = {
            "presentation_goal": "Deliver a clear and persuasive presentation.",
            "narrative_arc": "Problem to solution progression.",
            "slides": fallback_slides,
        }

    return {"outline": outline}
