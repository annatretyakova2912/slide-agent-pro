from typing import Dict, Any
from ..graph.state import GraphState
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import json

def researcher_node(state: GraphState) -> Dict[str, Any]:
    """
    Search agent that reasons about the required slide fields.
    It looks at the `template_schema` (which includes the original text examples)
    and uses an LLM to generate a comprehensive markdown report for the target entity
    that the Structurer can then cleanly parse.
    """
    print("--- RESEARCHER (Searcher) ---")
    
    entity = state.get("entities", [])[state.get("current_entity_index", 0)]
    schema = state.get("template_schema", {})
    revision_notes = state.get("revision_notes", "")
    
    print(f"Researching for entity: {entity}")
    
    # 1. Gather some basic raw data if Tavily is available
    raw_search_context = ""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key:
        print(f"Executing Tavily search for background context on: {entity}")
        try:
            search = TavilySearchResults(max_results=3)
            # Find general data about them
            results = search.invoke({"query": f"{entity} platform pricing, features, courses, and review criteria"})
            raw_search_context = "\n".join([doc.get("content", "") for doc in results])
        except Exception as e:
            print(f"Search failed: {e}. Relying purely on LLM knowledge.")
    
    # 2. Use an LLM to reason through the schema and the original text
    if not os.environ.get("OPENAI_API_KEY"):
         print("OPENAI_API_KEY not found. Skipping reasoning step.")
         return {"research_data": {"raw_text": f"Mock data for {entity}. Schema: {schema}"}}

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    system_prompt = """
    You are an expert Research Assistant. Your job is to gather and reason about information for a specific entity so that another agent can build a presentation slide about them.
    
    You will be provided with:
    1. The target entity name.
    2. A "Data Schema" detailing exactly what fields are on the slide. Crucially, the schema includes the `original_text` that was on the template slide for a different entity!
    3. (Optional) Raw search context from the web.
    
    YOUR TASK:
    Write a comprehensive text document that provides the appropriate information for the target entity for EACH field in the schema.
    Use the `original_text` as a direct example of the formatting, tone, and TYPE of information required. 
    For example, if the original text was a price like "$100", find or estimate the price for the new entity.
    If the original text was a list of courses, provide a list of courses for the new entity.
    If the original text was a score out of 10 for "User-friendliness", provide a realistic score for the new entity.
    
    Be exhaustive. Make sure every single field requested in the schema is addressed in your output comprehensively.
    """
    
    prompt_str = "Entity: {entity}\n\nSchema:\n{schema}\n\n"
    if raw_search_context:
        prompt_str += "Web Search Context:\n{raw_search_context}\n\n"
    if revision_notes:
        prompt_str += "CRITICAL REVISION NOTES FROM QUALITY QA:\n{revision_notes}\n\n"
        
    prompt_str += "Please write the comprehensive research document now."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", prompt_str)
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        print("Prompting LLM Researcher to generate comprehensive data document...")
        raw_text = chain.invoke({
            "entity": entity,
            "schema": json.dumps(schema, indent=2),
            "raw_search_context": raw_search_context,
            "revision_notes": revision_notes
        })
    except Exception as e:
        print(f"Error reasoning research via LLM: {e}")
        raw_text = f"Fallback text. Failed to reason for {entity}."

    return {"research_data": {"raw_text": raw_text}}
