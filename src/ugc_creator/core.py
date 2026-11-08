from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

APP_VERSION = "0.1.0"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class UgcError(RuntimeError):
    pass


@dataclass(frozen=True)
class Probe:
    path: str
    kind: str
    width: int
    height: int
    duration: float
    sha256: str


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if result.returncode:
        raise UgcError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr[-3000:]}")
    return result


def executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise UgcError(f"Required executable not found: {name}")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_project(root: Path) -> dict[str, Any]:
    path = root / "project.yaml"
    if not path.exists():
        raise UgcError(f"Project file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = ["schema_version", "id", "brief", "brand", "assets"]
    missing = [key for key in required if key not in data]
    if missing:
        raise UgcError(f"Missing project keys: {', '.join(missing)}")
    if not 8 <= len(data["assets"]) <= 20:
        raise UgcError("The MVP project requires between 8 and 20 assets")
    return data


def probe(path: Path) -> Probe:
    suffix = path.suffix.lower()
    kind = "image" if suffix in IMAGE_EXTENSIONS else "video" if suffix in VIDEO_EXTENSIONS else "unknown"
    if kind == "unknown":
        raise UgcError(f"Unsupported asset: {path}")
    args = [executable("ffprobe"), "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)]
    data = json.loads(run(args).stdout)
    stream = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
    if not stream:
        raise UgcError(f"No video/image stream found: {path}")
    duration = float(stream.get("duration") or data.get("format", {}).get("duration") or 0)
    return Probe(str(path), kind, int(stream.get("width", 0)), int(stream.get("height", 0)), duration, sha256(path))


def inventory(project_root: Path) -> list[dict[str, Any]]:
    project = read_project(project_root)
    items = []
    for item in project["assets"]:
        path = (project_root / item["path"]).resolve()
        if not path.exists():
            raise UgcError(f"Asset not found: {path}")
        details = asdict(probe(path))
        details.update({key: value for key, value in item.items() if key != "path"})
        details["path"] = os.path.relpath(path, project_root).replace("\\", "/")
        items.append(details)
    write_json(project_root / "assets" / "inventory.json", {"schema_version": 1, "assets": items})
    return items


def concepts_for(project: dict[str, Any]) -> list[dict[str, Any]]:
    offer = project["brief"]["offer"]
    zone = project["brief"]["zone"]
    return [
        {"id": "transformation", "angle": "Historia y transformación", "hooks": [
            "Parecía imposible, hasta que cambiamos esto.",
            "Mira cómo transformamos este espacio paso a paso.",
            "De problema a resultado: el cambio se ve así."]},
        {"id": "utility", "angle": "Utilidad y criterio", "hooks": [
            "Tres decisiones que cambian por completo el resultado.",
            "Antes de empezar, revisa estos tres puntos.",
            "El error más caro suele ocurrir antes de la obra."]},
        {"id": "offer", "angle": "Oferta y acción", "hooks": [
            f"Si estás en {zone}, esto te interesa.",
            f"Así funciona {offer}.",
            "Tu proyecto puede empezar con una decisión sencilla."]},
    ]


def make_plan(project_root: Path, *, hook: str | None = None, cta: str | None = None, order: list[int] | None = None) -> dict[str, Any]:
    project = read_project(project_root)
    inv_path = project_root / "assets" / "inventory.json"
    assets = read_json(inv_path)["assets"] if inv_path.exists() else inventory(project_root)
    concepts = concepts_for(project)
    write_json(project_root / "creative" / "concepts.json", {"schema_version": 1, "concepts": concepts})
    selected_hook = hook or concepts[0]["hooks"][0]
    selected_cta = cta or project["brief"]["cta"]
    sequence = order or list(range(min(8, len(assets))))
    durations = [3.2, 3.0, 3.0, 3.2, 3.0, 3.0, 3.2, 3.4]
    captions = [
        selected_hook,
        "Partimos de los activos reales",
        "Ordenamos el problema y las prioridades",
        "Cada decisión queda documentada",
        "Mostramos el proceso sin inventar resultados",
        "El montaje adapta ritmo, voz y mensaje",
        "Creamos variantes para aprender qué funciona",
        selected_cta,
    ]
    shots = []
    cursor = 0.0
    for position, asset_index in enumerate(sequence):
        duration = durations[position]
        shots.append({
            "id": f"shot-{position + 1:02d}", "asset": assets[asset_index]["path"],
            "start": round(cursor, 3), "duration": duration, "caption": captions[position],
            "motion": "push_in" if position % 2 == 0 else "pull_out",
        })
        cursor += duration
    plan = {
        "schema_version": 1, "project_id": project["id"], "format": {"width": 1080, "height": 1920, "fps": 30},
        "hook": selected_hook, "cta": selected_cta, "duration": round(cursor, 3), "shots": shots,
        "voiceover": project.get("voiceover", {}).get("path"), "brand": project["brand"],
    }
    write_json(project_root / "timeline" / "master.json", plan)
    write_json(project_root / "creative" / "script.json", {"schema_version": 1, "lines": captions})
    return plan


def srt_timestamp(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(plan: dict[str, Any], path: Path) -> None:
    blocks = []
    for index, shot in enumerate(plan["shots"], 1):
        end = shot["start"] + shot["duration"]
        blocks.append(f"{index}\n{srt_timestamp(shot['start'])} --> {srt_timestamp(end)}\n{shot['caption']}\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(blocks), encoding="utf-8")


def ffmpeg_escape(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def render(project_root: Path, plan_path: Path | None = None, output_name: str = "master") -> Path:
    started = time.perf_counter()
    plan_path = plan_path or project_root / "timeline" / "master.json"
    plan = read_json(plan_path)
    cache = project_root / "assets" / "cache" / "segments"
    cache.mkdir(parents=True, exist_ok=True)
    ffmpeg = executable("ffmpeg")
    segment_paths = []
    for index, shot in enumerate(plan["shots"]):
        source = (project_root / shot["asset"]).resolve()
        cache_key = hashlib.sha256(json.dumps({
            "source": sha256(source), "duration": shot["duration"], "motion": shot.get("motion"),
            "width": plan["format"]["width"], "height": plan["format"]["height"], "fps": plan["format"]["fps"],
            "renderer": APP_VERSION,
        }, sort_keys=True).encode()).hexdigest()[:20]
        out = cache / f"{cache_key}.mp4"
        duration = float(shot["duration"])
        if out.exists() and out.stat().st_size > 0:
            segment_paths.append(out)
            continue
        details = probe(source)
        common_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p"
        if details.kind == "image":
            frames = round(duration * 30)
            zoom = "min(zoom+0.0007,1.08)" if shot.get("motion") == "push_in" else "if(eq(on,1),1.08,max(zoom-0.0007,1.0))"
            vf = f"{common_filter},zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30"
            args = [ffmpeg, "-y", "-loop", "1", "-i", str(source), "-t", str(duration), "-vf", vf]
        else:
            vf = common_filter
            args = [ffmpeg, "-y", "-stream_loop", "-1", "-i", str(source), "-t", str(duration), "-vf", vf]
        args += ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)]
        run(args)
        segment_paths.append(out)
    concat_file = cache / "concat.txt"
    concat_file.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segment_paths), encoding="utf-8")
    joined = cache / "joined.mp4"
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(joined)])
    subtitles = project_root / "renders" / f"{output_name}.srt"
    write_srt(plan, subtitles)
    output = project_root / "renders" / f"{output_name}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    style = "FontName=Arial,FontSize=8,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BackColour=&H98000000,BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginL=55,MarginR=55,MarginV=165"
    vf = f"subtitles='{ffmpeg_escape(subtitles)}':force_style='{style}'"
    voice = plan.get("voiceover")
    args = [ffmpeg, "-y", "-i", str(joined)]
    if voice and (project_root / voice).exists():
        args += ["-i", str((project_root / voice).resolve()), "-filter_complex", f"[0:v]{vf}[v];[1:a]apad,volume=1.0[a]", "-map", "[v]", "-map", "[a]", "-shortest"]
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "1:a", "-shortest"]
    encoder = "h264_nvenc" if "h264_nvenc" in run([ffmpeg, "-hide_banner", "-encoders"]).stdout else "libx264"
    args += ["-c:v", encoder, "-preset", "p4" if encoder == "h264_nvenc" else "medium", "-b:v", "8M", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    try:
        run(args)
    except UgcError:
        args[args.index(encoder)] = "libx264"
        preset_index = args.index("p4") if "p4" in args else -1
        if preset_index >= 0:
            args[preset_index] = "medium"
        run(args)
        encoder = "libx264"
    manifest = {
        "schema_version": 1, "app_version": APP_VERSION, "project_id": plan["project_id"], "variant": output_name,
        "created_at": datetime.now(timezone.utc).isoformat(), "timeline": os.path.relpath(plan_path, project_root).replace("\\", "/"),
        "timeline_sha256": sha256(plan_path), "output": os.path.relpath(output, project_root).replace("\\", "/"),
        "output_sha256": sha256(output), "encoder": encoder, "render_seconds": round(time.perf_counter() - started, 3),
        "assets": [{"path": shot["asset"], "sha256": sha256(project_root / shot["asset"])} for shot in plan["shots"]],
    }
    write_json(project_root / "manifests" / f"{output_name}.json", manifest)
    return output


VARIANTS = [
    ("hook-b", "Mira el resultado antes de conocer el proceso.", None, None),
    ("hook-c", "Tres decisiones hicieron posible este cambio.", None, None),
    ("cta-b", None, "Pide una valoración sin compromiso.", None),
    ("cta-c", None, "Escríbenos y revisamos tu caso.", None),
    ("reverse-middle", None, None, [0, 2, 1, 4, 3, 5, 6, 7]),
]


def make_variants(project_root: Path, *, do_render: bool = True) -> list[Path]:
    outputs = []
    variants_dir = project_root / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)
    for name, hook, cta, order in VARIANTS:
        plan = make_plan(project_root, hook=hook, cta=cta, order=order)
        path = variants_dir / f"{name}.json"
        write_json(path, plan)
        if do_render:
            outputs.append(render(project_root, path, name))
    make_plan(project_root)
    return outputs


def verify_video(path: Path) -> dict[str, Any]:
    data = json.loads(run([executable("ffprobe"), "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)]).stdout)
    video = next((stream for stream in data["streams"] if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in data["streams"] if stream.get("codec_type") == "audio"), None)
    duration = float(data["format"]["duration"])
    checks = {
        "exists": path.exists() and path.stat().st_size > 0, "width_1080": video and video.get("width") == 1080,
        "height_1920": video and video.get("height") == 1920, "duration_20_35": 20 <= duration <= 35,
        "has_audio": audio is not None, "has_video": video is not None,
    }
    return {"path": str(path), "duration": duration, "checks": checks, "passed": all(checks.values())}


def doctor() -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    encoders = run([ffmpeg, "-hide_banner", "-encoders"]).stdout if ffmpeg else ""
    result = {
        "python": sys.version.split()[0], "python_supported": (3, 12) <= sys.version_info[:2] < (3, 14),
        "ffmpeg": ffmpeg, "ffprobe": ffprobe, "nvenc": "h264_nvenc" in encoders,
        "nvidia_smi": shutil.which("nvidia-smi"), "models_installed_by_app": False,
    }
    result["ready"] = bool(result["python_supported"] and ffmpeg and ffprobe)
    return result
