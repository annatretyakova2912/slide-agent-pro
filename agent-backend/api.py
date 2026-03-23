import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

# Make local src importable when running `python3 api.py`
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.graph.graph import build_graph
from src.services.ppt_compiler import compile_rendered_to_pptx

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="Slide Agent API", version="1.0.0")


class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Raw text/topic to turn into slides")
    slides: int = Field(default=7, ge=1, le=20, description="Desired number of slides")
    audience: str = Field(default="general", description="Audience context")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Slide Agent - Test UI</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }
    .wrap { max-width: 900px; margin: 40px auto; background: #111827; border-radius: 14px; padding: 24px; }
    h1 { margin-top: 0; }
    label { display: block; margin: 14px 0 6px; font-weight: 600; }
    textarea, input { width: 100%; box-sizing: border-box; border-radius: 10px; border: 1px solid #334155; background: #0b1220; color: #e2e8f0; padding: 12px; }
    textarea { min-height: 170px; resize: vertical; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    button { margin-top: 16px; background: #2563eb; color: white; border: 0; border-radius: 10px; padding: 12px 16px; cursor: pointer; font-weight: 700; }
    button:disabled { opacity: .65; cursor: wait; }
    .status { margin-top: 12px; color: #93c5fd; white-space: pre-wrap; }
    .hint { color: #94a3b8; font-size: 14px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Slide Agent - Génération PPT</h1>
    <p class="hint">Entre ton texte, clique sur Générer, puis le .pptx se télécharge automatiquement.</p>

    <label for="text">Texte source</label>
    <textarea id="text" placeholder="Colle ici un sujet, un brief ou un long texte..."></textarea>

    <div class="row">
      <div>
        <label for="slides">Nombre de slides</label>
        <input id="slides" type="number" min="1" max="20" value="7" />
      </div>
      <div>
        <label for="audience">Audience</label>
        <input id="audience" type="text" value="general" />
      </div>
    </div>

    <button id="generate">Generer la presentation</button>
    <div class="status" id="status"></div>
  </div>

  <script>
    const btn = document.getElementById("generate");
    const statusEl = document.getElementById("status");

    async function generate() {
      const text = document.getElementById("text").value.trim();
      const slides = Number(document.getElementById("slides").value || 7);
      const audience = document.getElementById("audience").value.trim() || "general";

      if (text.length < 5) {
        statusEl.textContent = "Ajoute un texte un peu plus long (min 5 caracteres).";
        return;
      }

      btn.disabled = true;
      statusEl.textContent = "Generation en cours...";

      try {
        const response = await fetch("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, slides, audience }),
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(err.detail || "Erreur serveur");
        }

        const blob = await response.blob();
        const disposition = response.headers.get("Content-Disposition") || "";
        const match = disposition.match(/filename="?([^"]+)"?/i);
        const filename = match ? match[1] : "presentation_generee.pptx";

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        statusEl.textContent = "Termine. Le fichier PPTX a ete telecharge.";
      } catch (err) {
        statusEl.textContent = "Echec: " + (err.message || String(err));
      } finally {
        btn.disabled = false;
      }
    }

    btn.addEventListener("click", generate);
  </script>
</body>
</html>
"""


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/generate")
def generate_presentation(payload: GenerateRequest) -> FileResponse:
    try:
        graph = build_graph()
        initial_state = {
            "user_input": payload.text,
            "topic": payload.text[:200],
            "audience": payload.audience,
            "desired_slide_count": payload.slides,
            "revision_count": 0,
            "max_revision_rounds": 2,
            "needs_revision": False,
            "next_action": "",
        }
        final_state = graph.invoke(initial_state)
        rendered = final_state.get("rendered_presentation")
        if not rendered:
            raise RuntimeError("No rendered_presentation found in graph output.")

        output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ppt_filename = f"generated_presentation_{timestamp}.pptx"
        json_filename = f"generated_presentation_{timestamp}.json"
        ppt_path = os.path.join(output_dir, ppt_filename)
        json_path = os.path.join(output_dir, json_filename)

        compile_rendered_to_pptx(rendered, ppt_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(final_state, f, ensure_ascii=False, indent=2)

        return FileResponse(
            ppt_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=ppt_filename,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/generate-json")
def generate_json(payload: GenerateRequest) -> JSONResponse:
    try:
        graph = build_graph()
        initial_state = {
            "user_input": payload.text,
            "topic": payload.text[:200],
            "audience": payload.audience,
            "desired_slide_count": payload.slides,
            "revision_count": 0,
            "max_revision_rounds": 2,
            "needs_revision": False,
            "next_action": "",
        }
        final_state = graph.invoke(initial_state)
        return JSONResponse(content=final_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

