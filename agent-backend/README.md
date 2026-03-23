# Slide Agent — backend

## Template-driven “Canva-like” decks

After **Strategist** and **Content Architect** (`copywriter_intent_matcher`) produce final copy and `structure_hint` per slide, the pipeline:

1. **Art Director** (`style_selector`) — session palette + fonts (design tokens).
2. **Template + layout orchestrator** (`layout_matcher`) — picks an uploaded `.pptx` master from `data/templates/catalog.json` (LLM-assisted), or falls back to simple boxes.
3. **Asset scout** — image prompts / icons (optional).
4. **Rendering orchestrator** — merges layout + assets + tokens for export.
5. **PPT compiler** (`ppt_compiler`) — **per slide**, if `template_pptx_path` is set and the file exists, clones that master and injects text + fonts/colors + overlap heuristics; otherwise uses a clean fallback box layout for that slide only (mixed decks supported).

Full workflow for authors: see **`data/templates/README.md`**.

### Register a template

From `agent-backend/`:

```bash
python3 scripts/ingest_template.py \
  --file ./your_timeline_master.pptx \
  --id my_timeline_v1 \
  --name "My timeline" \
  --hints timeline,process_steps \
  --description "Horizontal 4-step timeline with icons" \
  --slide-index 0
```

`structure_hints` must overlap values your Content Architect outputs (e.g. `timeline`, `comparison_2col`, `hero`).

### Run the pipeline

```bash
python3 run_pipeline.py --text "Your brief..." --slides 6 --output-dir outputs
```

API: `uvicorn api:app --reload` then open `http://localhost:8000`.
