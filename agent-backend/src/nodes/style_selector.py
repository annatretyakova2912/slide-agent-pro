from typing import Dict, Any
from ..graph.state import GraphState
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json

def style_selector_node(state: GraphState) -> Dict[str, Any]: