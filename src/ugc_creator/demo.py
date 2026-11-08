from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .core import UgcError, executable, run


COLORS = ["213547", "344e41", "6b705c", "a98467", "99582a", "432818", "3d405b", "1d3557"]
LABELS = ["ANTES", "ESPACIO", "PLAN", "PROCESO", "DETALLE", "ACABADO", "RESULTADO", "CTA"]


def create_demo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    originals = root / "assets" / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    ffmpeg = executable("ffmpeg")
    for index, (color, label) in enumerate(zip(COLORS, LABELS), 1):
        path = originals / f"demo-{index:02d}.png"
        if not path.exists():
            vf = f"drawbox=x=70:y=90:w=820:h=1100:color=white@0.10:t=fill,drawtext=text='{label}':fontcolor=white:fontsize=96:x=(w-text_w)/2:y=(h-text_h)/2"
            run([ffmpeg, "-y", "-f", "lavfi", "-i", f"color=c=0x{color}:s=1080x1440:d=1", "-frames:v", "1", "-vf", vf, str(path)])
    voice_dir = root / "assets" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    voice = voice_dir / "demo.wav"
    if not voice.exists():
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate=0; $s.SetOutputToWaveFile($args[0]); "
            "$s.Speak('Parecía imposible, hasta que cambiamos esto. Partimos de los activos reales. Ordenamos el problema y las prioridades. Cada decisión queda documentada. Mostramos el proceso sin inventar resultados. El montaje adapta ritmo, voz y mensaje. Creamos variantes para aprender qué funciona. Solicita tu valoración.'); $s.Dispose()"
        )
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script, str(voice)], capture_output=True, text=True)
        if result.returncode or not voice.exists():
            run([ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=25", "-af", "volume=0.02", str(voice)])
    data = {
        "schema_version": 1, "id": "demo-reforma", "kind": "reforma",
        "brief": {"audience": "Propietarios que quieren reformar", "offer": "valoración inicial", "zone": "Valencia", "cta": "Solicita tu valoración"},
        "brand": {"name": "UGC Creator Demo", "primary_color": "#213547", "disclosure": "Demostración con activos sintéticos"},
        "rights": {"status": "demo_only", "notes": "Activos sintéticos generados localmente; no publicar como caso real."},
        "voiceover": {"path": "assets/voice/demo.wav", "consent": "system_demo_voice"},
        "assets": [{"path": f"assets/originals/demo-{index:02d}.png", "role": "demo", "rights": "generated_locally"} for index in range(1, 9)],
    }
    (root / "project.yaml").write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return root

