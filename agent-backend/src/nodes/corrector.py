from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..graph.state import GraphState
import json

def corrector_node(state: GraphState) -> Dict[str, Any]:
    """
    Checks for overlaps (text too long for the box) or hallucinations.
    Uses an LLM to evaluate the generated structured data against the schema.
    """
    print("--- CORRECTOR (Quality Gate) ---")
    
    structured_data = state.get("structured_data", {})
    entity_index = state.get("current_entity_index", 0)
    entities = state.get("entities", [])
    entity = entities[entity_index]
    schema = state.get("template_schema", {})
    
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not found. Skipping QA check.")
        passed = True
        revision_notes = ""
    else:    
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        system_prompt = """
        You are an expert Presentation Editor and Quality Assurance agent.
        You will be given:
        1. The intended slide schema.
        2. The target entity name.
        3. The structured data populated for that entity.
        
        Your job is to act as a Quality Gate. You must check for:
        - Hallucinations: Does the data seem fake or completely unrelated to the target entity?
        - Missing Data: Did the structurer fail to populate a field?
        
        Output ONLY valid JSON with two keys:
        1. "passed": true if the data is acceptable, false if it needs revision.
        2. "revision_notes": A string containing explicit instructions for the Researcher or Structurer on what needs fixing (leave empty if passed).
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Entity: {entity}\n\nSchema:\n{schema}\n\nStructured Data to Evaluate:\n{structured_data}")
        ])
        
        parser = JsonOutputParser()
        chain = prompt | llm | parser
        
        print(f"Prompting LLM to evaluate Quality Gate for {entity}...")
        try:
            evaluation = chain.invoke({
                "entity": entity,
                "schema": json.dumps(schema, indent=2),
                "structured_data": json.dumps(structured_data, indent=2)
            })
            passed = evaluation.get("passed", False)
            revision_notes = evaluation.get("revision_notes", "")
        except Exception as e:
            print(f"Error evaluating data via LLM: {e}")
            passed = True
            revision_notes = ""
            
        # Programmatic Word Count Execution
        if passed:
            for field in schema.get("fields", []):
                target_id = field.get("shape_id")
                max_words = field.get("max_word_count", 9999)
                for mapped in structured_data.get("mapped_fields", []):
                    if mapped.get("shape_id") == target_id:
                        text_val = str(mapped.get("new_text", ""))
                        if len(text_val.split()) > max_words:
                            passed = False
                            revision_notes = f"PROGRAMMATIC FAIL: Field '{field['field_name']}' has {len(text_val.split())} words, which exceeds the absolute maximum of {max_words} words. Shorten it!"
         
    if not passed:
        print(f"Corrector spotted issues for {entity}. Requesting revision: {revision_notes}")
        return {
            "revision_notes": revision_notes
        }
        
    print(f"Data for {entity} passed the quality gate!")
    
    final_slides_data = state.get("final_slides_data", [])
    if final_slides_data is None:
        final_slides_data = []
        
    final_slides_data.append({
        "entity": entity,
        "data": structured_data
    })
    
    return {
        "final_slides_data": final_slides_data,
        "current_entity_index": entity_index + 1,
        "revision_notes": "" # Clear notes
    }
