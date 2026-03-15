import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), 'agent-backend', '.env'))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent-backend')))

from src.graph.graph import build_slide_agent_graph

def run_test():
    print("Initializing Slide Agent Graph...")
    app = build_slide_agent_graph()
    
    print("\n-----------------------\n")
    
    # -------------------------------------------------------------
    # Simulated User Input: 
    #   "I would like to create exactly the same slide for udemy, 
    #    just like the slide hat I gave you on coursera"
    # -------------------------------------------------------------
    
    # Mock initial state
    initial_state = {
        "template_path": "data/templates/Template .pptx",
        "entities": ["The Knowledge Academy", "Udemy"],
        "current_entity_index": 0,
        "template_schema": None,
        "research_data": None,
        "structured_data": None,
        "revision_notes": None,
        "final_slides_data": [],
        "messages": []
    }
    
    print("Running graph to generate Udemy slide...\n")
    
    # Run the graph
    app.invoke(initial_state)
    
    # The output will be saved as output_Udemy.pptx

if __name__ == "__main__":
    run_test()
