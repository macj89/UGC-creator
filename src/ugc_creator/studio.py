from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Timer
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .engines.comfy import ComfyClient, ComfyError, ComfyOutput, flux_gguf_workflow
from .engines.elevenlabs import ElevenLabsClient, ElevenLabsError
from .engines.openrouter import OpenRouterClient, OpenRouterError

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "studio_static"
WORKFLOWS = ROOT / "workspace" / "studio" / "workflows"


def _load_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip()


_load_env()
COMFY_URL = os.environ.get("UGC_COMFY_URL", "http://127.0.0.1:8188")
JOBS: dict[str, dict[str, Any]] = {}
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ugc-comfy")


class WorkflowPayload(BaseModel):
    id: str
    name: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    settings: dict[str, Any] = {}


PRESETS = {
    "reforma-cinematic": {
        "name": "Reforma · Transformación cinematográfica",
        "description": "Antes/después con movimiento controlado, textura real y montaje de impacto.",
        "nodes": [
            ("brief", "Brief de campaña", "strategy", 70, 220),
            ("assets", "Activos reales", "input", 340, 100),
            ("director", "Director creativo", "ai", 340, 340),
            ("shot", "Diseño de plano", "creative", 640, 210),
            ("motion", "Keyframe · Flux local", "engine", 950, 90),
            ("look", "Look cinematográfico", "grade", 950, 330),
            ("hero", "Hero motion · OpenRouter", "video", 1260, 80),
            ("voice", "Voz UGC", "audio", 1260, 430),
            ("edit", "Montaje vertical", "edit", 1560, 190),
            ("qa", "Continuidad + QA", "quality", 1870, 190),
            ("export", "Master + variantes", "output", 2170, 190),
        ],
        "edges": [("brief", "director"), ("assets", "shot"), ("director", "shot"), ("shot", "motion"),
                  ("shot", "look"), ("motion", "hero"), ("hero", "edit"), ("look", "edit"), ("voice", "edit"),
                  ("edit", "qa"), ("qa", "export")],
    },
    "property-tour": {
        "name": "Inmobiliaria · Tour editorial",
        "description": "Recorrido premium con fidelidad espacial, voz y grafismo verificable.",
        "nodes": [
            ("listing", "Ficha verificada", "strategy", 80, 160), ("assets", "Fotos + clips", "input", 80, 390),
            ("sequence", "Narrativa espacial", "creative", 390, 250), ("camera", "Cámara virtual", "engine", 710, 120),
            ("look", "Luz natural", "grade", 710, 370), ("voice", "Voz multidioma", "audio", 1030, 470),
            ("edit", "Tour 9:16", "edit", 1040, 230), ("claims", "Claims + fidelidad", "quality", 1360, 230),
            ("export", "Pack de lanzamiento", "output", 1680, 230),
        ],
        "edges": [("listing", "sequence"), ("assets", "sequence"), ("sequence", "camera"), ("sequence", "look"),
                  ("camera", "edit"), ("look", "edit"), ("voice", "edit"), ("edit", "claims"), ("claims", "export")],
    },
    "ugc-selfie": {
        "name": "UGC · Selfie + B-roll",
        "description": "Presentador consentido, energía móvil y B-roll real con continuidad.",
        "nodes": [
            ("brief", "Hook + objeción", "strategy", 80, 220), ("identity", "Identidad consentida", "input", 380, 80),
            ("script", "Guion hablado", "ai", 380, 350), ("presenter", "Presentador UGC", "engine", 700, 80),
            ("broll", "B-roll real", "creative", 700, 350), ("voice", "Voz + lip-sync", "audio", 1010, 80),
            ("edit", "Montaje social", "edit", 1010, 350), ("qa", "Identidad + disclosure", "quality", 1320, 220),
            ("export", "Hooks A/B", "output", 1630, 220),
        ],
        "edges": [("brief", "script"), ("identity", "presenter"), ("script", "presenter"), ("script", "voice"),
                  ("presenter", "edit"), ("broll", "edit"), ("voice", "edit"), ("edit", "qa"), ("qa", "export")],
    },
}


DEFAULTS = {
    "strategy": {"audience": "Propietarios 35–55", "objective": "Leads cualificados", "duration": 28, "aspect": "9:16"},
    "input": {"source": "Activos reales", "rights": "Pendiente", "selection": "Manual + ranking"},
    "ai": {"model": "Adapter LLM", "concepts": 3, "hooks": 5, "tone": "Creíble, directo"},
    "creative": {"shotType": "Handheld premium", "lens": "35 mm", "framing": "Medium / detail", "continuity": 82},
    "engine": {"provider": "ComfyUI local", "model": "Flux.1 Dev GGUF Q4", "resolution": "512×768 draft", "steps": 20,
               "guidance": 3.5, "seed": 184762, "prompt": "cinematic documentary photograph of a premium Mediterranean apartment renovation, authentic materials, natural window light, subtle imperfections, handheld 35mm lens, realistic construction details, editorial color, no text",
               "negative": "plastic skin, waxy, CGI, illustration, text, watermark, distorted architecture", "camera": "Dolly in suave", "motion": 0.42, "status": "ready"},
    "video": {"provider": "OpenRouter", "model": "kwaivgi/kling-v3.0-std", "duration": "5 s", "resolution": "720p", "aspect": "9:16", "prompt": "subtle cinematic dolly in, physically plausible movement, preserve architecture and materials, natural handheld micro-motion", "audio": False, "status": "ready"},
    "grade": {"profile": "Natural filmic", "contrast": 0.16, "warmth": 0.08, "grain": 0.06, "highlightRollOff": 0.72},
    "audio": {"voice": "Voz consentida", "pace": 1.02, "emotion": "Conversacional", "music": "Minimal pulse", "ducking": -12},
    "edit": {"rhythm": "Hook rápido → desarrollo → CTA", "cutLength": 2.1, "captions": "Dynamic clean", "safeArea": True},
    "quality": {"identity": True, "claims": True, "artifacts": True, "continuity": True, "humanApproval": True},
    "output": {"codec": "H.264", "resolution": "1080×1920", "master": True, "variants": 6, "platform": "Meta / TikTok"},
}


def materialize(preset_id: str) -> dict[str, Any]:
    preset = PRESETS[preset_id]
    nodes = [{"id": node_id, "title": title, "type": kind, "x": x, "y": y, "params": dict(DEFAULTS[kind])}
             for node_id, title, kind, x, y in preset["nodes"]]
    edges = [{"id": f"{source}-{target}", "source": source, "target": target} for source, target in preset["edges"]]
    return {"id": preset_id, "name": preset["name"], "description": preset["description"], "nodes": nodes, "edges": edges,
            "settings": {"format": "9:16", "fps": 30, "quality": "draft"}}


def create_app() -> FastAPI:
    app = FastAPI(title="UGC Studio", version="0.2.0")
    WORKFLOWS.mkdir(parents=True, exist_ok=True)

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        try:
            comfy = ComfyClient(COMFY_URL).health()
        except ComfyError as exc:
            comfy = {"ready": False, "error": str(exc)}
        try:
            openrouter = OpenRouterClient().health()
        except OpenRouterError as exc:
            openrouter = {"ready": False, "error": str(exc), "video_models": []}
        eleven = ElevenLabsClient()
        try:
            voices = eleven.voices() if eleven.ready else []
            eleven_status = {"ready": eleven.ready, "voices": voices}
        except ElevenLabsError as exc:
            eleven_status = {"ready": False, "error": str(exc), "voices": []}
        return {"ready": True, "ffmpeg": bool(shutil.which("ffmpeg")), "gpu": bool(shutil.which("nvidia-smi")),
                "comfy": comfy, "openrouter": openrouter, "elevenlabs": eleven_status,
                "engines": {"image": "comfyui_flux_gguf" if comfy["ready"] else "offline",
                            "image_to_video": "openrouter" if openrouter["ready"] else "offline",
                            "talking_head": "not_configured", "voice": "elevenlabs" if eleven_status["ready"] else "system_demo"}}

    @app.get("/api/presets")
    def presets() -> list[dict[str, str]]:
        return [{"id": key, "name": value["name"], "description": value["description"]} for key, value in PRESETS.items()]

    @app.get("/api/presets/{preset_id}")
    def preset(preset_id: str) -> dict[str, Any]:
        if preset_id not in PRESETS:
            raise HTTPException(404, "Preset not found")
        return materialize(preset_id)

    @app.post("/api/workflows")
    def save(payload: WorkflowPayload) -> dict[str, str]:
        safe_id = "".join(char for char in payload.id if char.isalnum() or char in "-_")
        if not safe_id:
            raise HTTPException(400, "Invalid workflow id")
        path = WORKFLOWS / f"{safe_id}.json"
        path.write_text(json.dumps(payload.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "saved", "path": str(path)}

    @app.post("/api/workflows/{workflow_id}/run")
    def execute(workflow_id: str, payload: WorkflowPayload) -> dict[str, Any]:
        unavailable = [node["title"] for node in payload.nodes if node["type"] == "engine" and node.get("params", {}).get("status") == "offline"]
        if unavailable:
            return {"status": "needs_engine", "message": "Configura un motor visual para generar planos cinematográficos.", "nodes": unavailable,
                    "next": "Selecciona un adaptador local, GPU remota o API en el nodo Image → Video."}
        requested_id = payload.settings.get("run_node")
        requested = next((node for node in payload.nodes if node["id"] == requested_id), None) if requested_id else None
        engine = requested if requested and requested["type"] in {"engine", "video"} else next((node for node in payload.nodes if node["type"] == "engine"), None)
        if not engine:
            raise HTTPException(400, "Workflow has no generation engine")
        params = engine["params"]
        job_id = str(uuid.uuid4())
        if engine["type"] == "video":
            keyframe = next((job.get("output") for job in reversed(JOBS.values()) if job.get("status") == "completed" and job.get("kind") == "image"), None)
            if not keyframe:
                raise HTTPException(409, "Genera primero un keyframe con ComfyUI")
            JOBS[job_id] = {"id": job_id, "kind": "video", "status": "queued", "progress": 0, "message": "Esperando a OpenRouter"}
            EXECUTOR.submit(_run_openrouter_job, job_id, params, keyframe)
            return {"status": "queued", "job_id": job_id, "message": "Vídeo hero enviado a OpenRouter."}
        JOBS[job_id] = {"id": job_id, "kind": "image", "status": "queued", "progress": 0, "message": "Esperando a ComfyUI"}
        EXECUTOR.submit(_run_comfy_job, job_id, params)
        return {"status": "queued", "job_id": job_id, "message": "Generación local añadida a ComfyUI."}

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str) -> dict[str, Any]:
        if job_id not in JOBS:
            raise HTTPException(404, "Job not found")
        return {key: value for key, value in JOBS[job_id].items() if key != "output"}

    @app.get("/api/jobs/{job_id}/output")
    def job_output(job_id: str) -> Response:
        job = JOBS.get(job_id)
        if not job or job.get("status") != "completed" or "output" not in job:
            raise HTTPException(404, "Output not ready")
        return Response(job["output"], media_type="video/mp4" if job.get("kind") == "video" else "image/png")

    app.mount("/assets", StaticFiles(directory=STATIC), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/favicon.ico")
    def favicon() -> Response:
        return Response(status_code=204)

    return app


def _run_comfy_job(job_id: str, params: dict[str, Any]) -> None:
    job = JOBS[job_id]
    try:
        client = ComfyClient(COMFY_URL)
        client.health()
        job.update(status="running", progress=8, message="Cargando Flux GGUF")
        resolution = str(params.get("resolution", "512×768")).lower().replace("x", "×").split()[0]
        try:
            width, height = (int(value) for value in resolution.split("×"))
        except (ValueError, TypeError):
            width, height = 512, 768
        workflow = flux_gguf_workflow(str(params.get("prompt", "cinematic UGC photograph")), negative=str(params.get("negative", "")),
                                      width=width, height=height, steps=int(params.get("steps", 20)),
                                      guidance=float(params.get("guidance", 3.5)), seed=int(params.get("seed", 184762)),
                                      filename_prefix=f"ugc-studio/{job_id}")
        prompt_id = client.queue(workflow)
        job.update(prompt_id=prompt_id, progress=20, message="Generando imagen en RTX 4070")
        output = client.wait(prompt_id)
        job["output"] = client.image(output)
        job.update(status="completed", progress=100, message="Imagen lista", filename=output.filename)
    except Exception as exc:
        job.update(status="failed", message=str(exc), progress=0)


def _run_openrouter_job(job_id: str, params: dict[str, Any], keyframe: bytes) -> None:
    job = JOBS[job_id]
    try:
        duration = int(str(params.get("duration", "5")).split()[0])
        job.update(status="running", progress=15, message="Generando vídeo hero en OpenRouter")
        result = OpenRouterClient().image_to_video(
            keyframe, str(params.get("prompt", "subtle cinematic motion")), model=str(params.get("model", "kwaivgi/kling-v3.0-std")),
            duration=duration, aspect_ratio=str(params.get("aspect", "9:16")), resolution=str(params.get("resolution", "720p")),
            generate_audio=bool(params.get("audio", False)))
        job["output"] = result.content
        job.update(status="completed", progress=100, message=f"Vídeo listo · ${result.cost_usd:.3f}", cost_usd=result.cost_usd, model=result.model)
    except Exception as exc:
        job.update(status="failed", message=str(exc), progress=0)


app = create_app()


def main() -> int:
    parser = argparse.ArgumentParser(description="UGC Studio visual workflow editor")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not args.no_browser:
        Timer(1.1, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0
