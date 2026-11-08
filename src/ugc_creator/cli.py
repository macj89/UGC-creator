from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import UgcError, doctor, inventory, make_plan, make_variants, render, verify_video, write_json
from .demo import create_demo


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="ugc-creator", description="UGC Creator MVP")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Comprueba el entorno sin instalar nada")
    demo = commands.add_parser("demo", help="Crea un proyecto de demostración ligero")
    demo.add_argument("project", type=Path)
    for name in ("inspect", "plan", "render", "variants", "verify", "all"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
    commands.choices["variants"].add_argument("--no-render", action="store_true")
    commands.choices["verify"].add_argument("--video", type=Path)
    return root


def emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(); emit(result); return 0 if result["ready"] else 1
        project = args.project.resolve()
        if args.command == "demo":
            emit({"project": str(create_demo(project))}); return 0
        if args.command == "inspect":
            emit({"assets": inventory(project)}); return 0
        if args.command == "plan":
            emit(make_plan(project)); return 0
        if args.command == "render":
            emit({"output": str(render(project))}); return 0
        if args.command == "variants":
            emit({"outputs": [str(path) for path in make_variants(project, do_render=not args.no_render)]}); return 0
        if args.command == "verify":
            video = args.video.resolve() if args.video else project / "renders" / "master.mp4"
            result = verify_video(video); write_json(project / "reviews" / f"{video.stem}.automatic.json", result); emit(result)
            return 0 if result["passed"] else 1
        if args.command == "all":
            inventory(project); make_plan(project); master = render(project); variants = make_variants(project)
            checks = [verify_video(path) for path in [master, *variants]]
            write_json(project / "reviews" / "batch.automatic.json", checks)
            emit({"master": str(master), "variants": [str(path) for path in variants], "checks": checks})
            return 0 if all(item["passed"] for item in checks) else 1
    except UgcError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0

