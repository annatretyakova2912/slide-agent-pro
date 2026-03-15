import sys
import os

# Add the agent-backend directory to the python path so the script can resolve module paths correctly 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent-backend')))
from src.services.python_pptx import export_slide_context_for_llm

template_path = "data/templates/Template .pptx"
output_path = "template_extraction_output.json"

if not os.path.exists(template_path):
    print(f"Error: Could not find {template_path}")
    sys.exit(1)

try:
    print(f"Extracting context from: {template_path}...")
    # Extracting the first slide (index 0)
    json_output = export_slide_context_for_llm(template_path, slide_index=0)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_output)
        
    print(f"Successfully extracted {len(json_output)} bytes of JSON data.")
    print(f"Output saved to: {output_path}")

except Exception as e:
    print(f"Extraction failed: {str(e)}")
    import traceback
    traceback.print_exc()

