from langgraph.graph import StateGraph, END
from typing import Any
from .state import GraphState
from ..nodes.strategist import strategist_node
from ..nodes.copywriter_intent_matcher import copywriter_intent_matcher_node
from ..nodes.style_selector import style_selector_node
from ..nodes.layout_matcher import layout_matcher_node
from ..nodes.asset_scouter import asset_scouter_node
from ..nodes.rendering_orchestrator import rendering_orchestrator_node
from ..nodes.quality_control import quality_control_node


def _route_after_quality(state: GraphState) -> str:
    if not state.get("needs_revision", False):
        return "end"
    next_action = state.get("next_action", "")
    if next_action == "copywriter_intent_matcher":
        return "copywriter_intent_matcher"
    if next_action == "layout_matcher":
        return "layout_matcher"
    if next_action == "style_selector":
        return "style_selector"
    return "end"


def build_graph() -> Any:
    workflow = StateGraph(GraphState)

    workflow.add_node("strategist", strategist_node)
    workflow.add_node("copywriter_intent_matcher", copywriter_intent_matcher_node)
    workflow.add_node("style_selector", style_selector_node)
    workflow.add_node("layout_matcher", layout_matcher_node)
    workflow.add_node("asset_scouter", asset_scouter_node)
    workflow.add_node("rendering_orchestrator", rendering_orchestrator_node)
    workflow.add_node("quality_control", quality_control_node)

    workflow.set_entry_point("strategist")
    workflow.add_edge("strategist", "copywriter_intent_matcher")
    workflow.add_edge("copywriter_intent_matcher", "style_selector")
    workflow.add_edge("style_selector", "layout_matcher")
    workflow.add_edge("layout_matcher", "asset_scouter")
    workflow.add_edge("asset_scouter", "rendering_orchestrator")
    workflow.add_edge("rendering_orchestrator", "quality_control")

    workflow.add_conditional_edges(
        "quality_control",
        _route_after_quality,
        {
            "copywriter_intent_matcher": "copywriter_intent_matcher",
            "layout_matcher": "layout_matcher",
            "style_selector": "style_selector",
            "end": END,
        },
    )

    return workflow.compile()
