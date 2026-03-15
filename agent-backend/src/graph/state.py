from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """
    Represents the state of our slide generation agentic workflow.
    """
    # Inputs
    template_path: str
    entities: List[str]
    
    # Processing State
    current_entity_index: int
    template_schema: Optional[Dict[str, Any]]  # The schema extracted by the Analyzer
    
    # Current Entity Data
    research_data: Optional[Dict[str, Any]]    # Raw data found by Searcher
    structured_data: Optional[Dict[str, Any]]  # Data mapped to schema by Structurer
    
    # Quality Control
    revision_notes: Optional[str]              # Comments from Corrector or User
    
    # Final Output
    final_slides_data: List[Dict[str, Any]]    # Approved data for all processed entities
    
    # Conversation history (optional, for LLM context)
    messages: List[BaseMessage]
