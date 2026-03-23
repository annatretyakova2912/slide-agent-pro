from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..graph.state import GraphState
import json

def quality_control_node(state: GraphState) -> Dict[str, Any]:
    print("--- QUALITY CONTROL ---")


    