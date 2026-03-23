import argparse
import json
import os
import sys
from datetime import datetime

# Allow importing from src without package installation
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.graph.graph import build_graph
from src.services.ppt_compiler import compile_rendered_to_pptx


def run(text: str, output_dir: str, slide_count: int, audience: str) -> str:
    graph = build_graph()
    initial_state = {
        "user_input": text,
        "topic": text[:200],
        "audience": audience,
        "desired_slide_count": slide_count,
        "revision_count": 0,
        "max_revision_rounds": 2,
        "needs_revision": False,
        "next_action": "",
    }
    final_state = graph.invoke(initial_state)
    rendered = final_state.get("rendered_presentation")
    if not rendered:
        raise RuntimeError("No rendered_presentation found in graph output.")

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ppt_path = os.path.join(output_dir, f"generated_presentation_{timestamp}.pptx")
    json_path = os.path.join(output_dir, f"generated_presentation_{timestamp}.json")

    compile_rendered_to_pptx(rendered, ppt_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_state, f, ensure_ascii=False, indent=2)

    return ppt_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the LangGraph slide pipeline and export a PPTX."
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Input text/topic to transform into a presentation.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory where PPTX/JSON results are saved.",
    )
    parser.add_argument(
        "--slides",
        type=int,
        default=7,
        help="Desired number of slides.",
    )
    parser.add_argument(
        "--audience",
        default="general",
        help="Target audience context.",
    )
    args = parser.parse_args()

    ppt_path = run(args.text, args.output_dir, args.slides, args.audience)
    print(f"Presentation generated: {ppt_path}")


if __name__ == "__main__":
    main()

