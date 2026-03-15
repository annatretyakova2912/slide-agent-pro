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
                "fields": [],
                "visual_elements": []
        }}
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    system_prompt = """
    You are a Lead Presentation Architect. Your task is to reverse-engineer a PowerPoint slide's "Functional DNA" from its JSON representation. 

Another agent (the Researcher) will use your output to find data for a new topic, and a third agent (the Structurer) will use it to rebuild the slide. You must capture not just the content, but the logical structure, intent, organization and design.

### GUIDING PRINCIPLES
1. INTERPRET STRUCTURE: Don't just list shapes. Identify if shapes form a "Logical Group" (e.g., 3 columns forming a "Benefits" section, a 1-10 scale forming a "Rating Grid", a set of arrows forming a "Process Flow", a chart, a table, a mind map, etc.).
2. HIERARCHY MATTERS: Distinguish between the Main Title, Section Headers, and Body Text.
3. VISUAL LOGIC: Identify "Markers" (icons, checkmarks, or highlight boxes) that are meant to be moved or duplicated based on data. Some of them might have to be adapted / moved by the Structurer. 

### EXTRACTION REQUIREMENTS

#### 1. Text Fields (`fields`)
For every logical text block, provide:
- `field_name`: A semantic name (e.g., "competitor_name_header").
- `description`: Instructions for the researcher (e.g., "Find the official name of the company").
- `shape_id`: The unique ID from the JSON.
- `original_text`: The full, verbatim text.
- `formatting_logic`: Note if the text contains mixed styles (e.g., "First word is Bold/Blue, rest is standard" or "The number is in font size X, the rest is in font size Y").

#### 2. Logical Groups & Grids (`structural_groups`)
Identify collections of shapes that work together:
- `group_type`: (e.g., "data_grid", "process_steps", "comparison_table", "rating_scale").
- `member_shape_ids`: A list of all shape IDs / other objects involved in this structure.
- `logic_description`: Explain how it works (e.g., "This is a 5-step horizontal chevron flow. Each chevron contains a title and a description.").

#### 3. Dynamic Visual Elements (`dynamic_elements`)
For icons or shapes that represent data points (like tick marks / checkmarks / scores):
- `element_name`: (e.g., "market_presence_indicator").
- `shape_id_to_transform`: The ID of the icon/shape that needs to move or change.
- `interaction_type`: (e.g., "reposition", "change_color", "duplicate").
- `mapping_reference`: A dictionary of possible values to their corresponding anchor `shape_ids` (e.g., Score "High" maps to Shape ID 45).

### OUTPUT FORMAT
Output ONLY valid JSON:
{{
  "slide_summary": "A brief description of the slide's purpose (e.g., 'Competitor Comparison Table')",
  "fields": [...],
  "structural_groups": [...],
  "dynamic_elements": [...]
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
