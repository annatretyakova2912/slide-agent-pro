from typing import Dict, Any
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..graph.state import GraphState
import json
import os

def structurer_node(state: GraphState) -> Dict[str, Any]:
    print("--- STRUCTURER ---")
    
    schema = state.get("template_schema", {})
    research_data = state.get("research_data", {})
    entity = state.get("entities", [])[state.get("current_entity_index", 0)]
    
    raw_text = research_data.get("raw_text", "")
    
    if not os.environ.get("OPENAI_API_KEY"):
         print("OPENAI_API_KEY not found. Falling back to raw mapping.")
         # Fallback mappings retaining shape_ids
         mapped = []
         for field in schema.get("fields", []):
             mapped.append({
                 "shape_id": field["shape_id"],
                 "new_text": f"{field['field_name'].upper()}: {entity} - {raw_text[:20]}..."
             })
         return {"structured_data": {"mapped_fields": mapped}}
         
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    system_prompt = """
    You are an expert data structurer and copywriter.
    You will be provided with:
    1. The target schema containing text `fields` (with their `shape_id`s, `original_text`, and `max_word_count`) and optionally `visual_elements` (scoring grids with icons that need repositioning).
    2. A comprehensive research report with all the information contained in the slide. 
    
    Your job is to map the correct facts into the provided schema.

    FOR TEXT FIELDS:
    MATCH the format, tone, and length of the `original_text` EXACTLY! 
    CRITICAL CONSTRAINT: You MUST NEVER exceed the `max_word_count` for any given shape. If you overflow the word count, the layout will look terrible on the slide!
    
    FOR VISUAL ELEMENTS (if any):
    If the text contains a `visual_elements` array, it means there are shapes (like checkmarks) that need to be physically moved over a specific target box (like a score from 1-10). Check the research data to see what score the entity got, and use the `options_mapping` dictionary to find the `target_shape_id` corresponding to that score string.
    
    Output ONLY valid JSON containing a dictionary with two keys:
    1. "mapped_fields": A list of objects with "shape_id" (integer) and "new_text" (string).
    2. "mapped_visual_elements": A list of objects with "shape_id_to_move" (integer) and "target_shape_id" (integer) mapping the icon to the specific score box.
    
    Example:
    {{
       "mapped_fields": [
           {{"shape_id": 4, "new_text": "Udemy: Online Learning"}},
           {{"shape_id": 8, "new_text": "- 50M+ users\\n- 100k+ courses"}}
       ],
       "mapped_visual_elements": [
           {{"shape_id_to_move": 108, "target_shape_id": 26}} 
       ]
    }}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Entity: {entity}\n\nTarget Schema:\n{schema}\n\nRaw Research Data:\n{raw_text}")
    ])
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        structured_data = chain.invoke({
            "entity": entity,
            "schema": json.dumps(schema, indent=2),
            "raw_text": raw_text
        })
        print(f"Mapped Data: {structured_data}")
    except Exception as e:
         print(f"Error structuring data via LLM: {e}")
         mapped = [{"shape_id": f["shape_id"], "new_text": f"{f['field_name']}: {entity}"} for f in schema.get("fields", [])]
         structured_data = {"mapped_fields": mapped}

    return {"structured_data": structured_data}
