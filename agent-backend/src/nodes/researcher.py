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
    ### ROLE
    You are a Senior Market Researcher and Content Strategist. Your goal is to transform raw research into structured content that fits a specific PowerPoint slide layout perfectly.

    ### INPUTS
    1. **Target Topic**: {entity} (The entity or subject you are researching).
    2. **Slide Schema**: {schema} (The "DNA" of the slide including field names, original text examples, and structural groups).
    3. **Search Context**: {raw_search_context} (Raw data found from the web).

    ### MISSION
    Your mission is to "Clone" the logic of the template slide but with the "DNA" of the new Topic. You must fulfill every requirement in the Schema.

    ### GUIDING RULES
    1. **Tone & Length Matching**: Use the `original_text` as a constraint. If the template uses 3-word bullet points, your output must be 3-word bullet points. If it uses a 50-word paragraph, write exactly 50 words (±10%).
    2. **Structural Fidelity**: 
    - If the schema defines a `structural_group` (like a 3-column grid), you must provide exactly 3 sets of data.
    - If there is a `dynamic_element` (like a 1-10 rating), you must reason based on the search context to provide a justified score.
    3. **Adaptation**: If the topic is very different from the template, maintain the *functional role* of the text. (e.g., if the template has "Engine Horsepower" but the topic is "Software," change the header to "Processing Speed").
    4. **No Placeholders**: Never say "Information not found." If data is missing, make a high-confidence inference based on the context or use a professional generic equivalent that fits the industry.

    ### OUTPUT FORMAT
    Provide a clean JSON object that maps the `field_name` or `element_name` from the schema to your new researched content:

    {{
    "research_summary": "Short explanation of how the research fits this specific slide structure.",
    "field_data": [
        {{
        "field_name": "...",
        "content": "...",
        "reasoning": "Briefly explain why this data fits the original's tone/length."
        }}
    ],
    "visual_data": [
        {{
        "element_name": "...",
        "selected_value": "...",
        "justification": "Why you chose this score/value."
        }}
    ]
    }}
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
