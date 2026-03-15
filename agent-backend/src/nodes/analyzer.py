from typing import Dict, Any
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..services.python_pptx import export_slide_context_for_llm
from ..graph.state import GraphState
import os

def template_analyzer_node(state: GraphState) -> Dict[str, Any]:
    print("--- TEMPLATE ANALYZER ---")
    template_path = state.get("template_path")
    
    raw_context_str = export_slide_context_for_llm(template_path, slide_index=0)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not found. Falling back to generic schema.")
        # Fallback uses shape_ids observed in the typical Template .pptx
        return {"template_schema": {
            "fields": [
                {"field_name": "title", "description": "Platform Name", "shape_id": 13, "original_text": "Platform / Provider Name"},
                {"field_name": "description", "description": "Platform Description", "shape_id": 8, "original_text": "Coursera is a leading global platform..."},
                {"field_name": "courses", "description": "Relevant Courses", "shape_id": 16, "original_text": "Introduction to ML..."},
            ]
        }}
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    system_prompt = """
    You are an expert presentation analyzer. Your job is to look at the JSON representation of a PowerPoint slide 
    and extract a "Data Schema" out of it. 
    
    Identify EVERY logical piece of text information (the "fields") that another agent needs to research and 
    provide in order to populate a slide with this exact same structure for a different entity.
    This includes titles, body paragraphs, bullet points, numbers denoting prices, etc.
    
    CRITICAL FOR TEXT FIELDS: For every text field you identify, you MUST include:
    1. A descriptive `field_name`.
    2. A `description` of what data belongs there.
    3. The exact `shape_id` found in the JSON for the shape that holds the text.
    4. The exact `original_text` that is currently in that shape. DO NOT TRUNCATE OR ABBREVIATE IT. You must provide the full text so its word count can be accurately determined.
    
    CRITICAL FOR VISUAL ELEMENTS: There may ALSO be "scoring grids" where a visual icon (like a tick mark image) is placed over a specific number (e.g. 1 to 10) to indicate a score. For these visual elements, you must extract:
    1. `element_name` (e.g., "user_friendliness_score")
    2. `description` 
    3. `shape_id_to_move`: The exact `shape_id` of the tick mark icon (usually a PICTURE or Graphic) that represents the score marker!
    4. `options_mapping`: A dictionary mapping the score strings ("1", "2", "3", etc.) to the `shape_id` of the text box that holds that number on that row.

    Output ONLY valid JSON representing a dictionary with two keys: "fields" (list of text objects) and "visual_elements" (list of visual grid objects):
    {{
      "fields": [
        {{
           "field_name": "main_subtitle_description",
           "description": "A 3-4 string description of the entity overview",
           "shape_id": 8,
           "original_text": "Coursera is a leading global platform that partners with over 375 premier universities and companies..."
        }}
      ],
      "visual_elements": [
        {{
           "element_name": "user_friendliness_score",
           "description": "Score from 1 to 10 for User-friendliness",
           "shape_id_to_move": 108,
           "options_mapping": {{"1": 21, "2": 22, "3": 23, "4": 24, "5": 25, "6": 26, "7": 27, "8": 28, "9": 29, "10": 30}}
        }}
      ]
    }}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the layout JSON for the slide template:\n\n{layout_json}")
    ])
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        template_schema = chain.invoke({"layout_json": raw_context_str})
        
        # Programmatically add max_word_count to avoid LLM math hallucinations
        for field in template_schema.get("fields", []):
            orig = field.get("original_text", "")
            field["max_word_count"] = len(orig.split()) + 10
            
        print(f"Extracted Schema: {template_schema}")
    except Exception as e:
        print(f"Error extracting schema via LLM: {e}")
        template_schema = {"fields": [{"field_name": "title", "description": "Main title", "shape_id": 4, "original_text": "Title", "max_word_count": 12}]}
    
    return {"template_schema": template_schema}
