from langgraph.graph import StateGraph, END
from typing import TypedDict, Any

from .state import GraphState
from ..nodes.analyzer import template_analyzer_node
from ..nodes.researcher import researcher_node
from ..nodes.structurer import structurer_node
from ..nodes.corrector import corrector_node
from ..nodes.compiler import compiler_node

# --- ROUTING FUNCTIONS ---
def route_after_corrector(state: GraphState) -> str:
    """
    Determines where to go after the Corrector validates the data.
    """
    # If there are revision notes, we failed the quality gate.
    if state.get("revision_notes"):
        print("-- ROUTER: Issues found. Routing back to Researcher (or Structurer).")
        return "researcher"
        
    # If the index has reached the length of the entities array, we are done.
    current_index = state.get("current_entity_index", 0)
    entities = state.get("entities", [])
    
    if current_index >= len(entities):
        print("-- ROUTER: All entities processed. Routing to Compiler.")
        return "compiler"
        
    # Otherwise, loop back to the researcher for the NEXT entity.
    print(f"-- ROUTER: Moving to next entity (Index {current_index}). Routing to Researcher.")
    return "researcher"

# --- BUILD THE GRAPH ---
def build_slide_agent_graph():
    """Builds and returns the compiled LangGraph."""
    workflow = StateGraph(GraphState)
    
    # Add Nodes
    workflow.add_node("analyzer", template_analyzer_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("structurer", structurer_node)
    workflow.add_node("corrector", corrector_node)
    workflow.add_node("compiler", compiler_node)
    
    # Add Edges
    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "researcher")
    workflow.add_edge("researcher", "structurer")
    workflow.add_edge("structurer", "corrector")
    
    # Add Conditional Edges from Corrector
    workflow.add_conditional_edges(
        "corrector",
        route_after_corrector,
        {
            "researcher": "researcher",
            "compiler": "compiler"
        }
    )
    
    # After compiler, we end (or wait for user interrupt logically)
    workflow.add_edge("compiler", END)
    
    # Compile the graph
    app = workflow.compile(
        # Optional: You can add an interrupt here to wait for user approval
        # interrupt_after=["compiler"]
    )
    
    return app
