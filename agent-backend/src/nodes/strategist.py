from typing import Dict, Any
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..services.python_pptx import export_slide_context_for_llm
from ..graph.state import GraphState
import os

def strategist_node(state: GraphState) -> Dict[str, Any]:
    print("--- STRATEGIST ---")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    system_prompt = """
    """
