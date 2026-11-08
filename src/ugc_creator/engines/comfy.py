from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any


class ComfyError(RuntimeError):
    pass


@dataclass(frozen=True)
class ComfyOutput:
    prompt_id: str
    filename: str
    subfolder: str
    folder_type: str


class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _json(self, path: str, data: dict[str, Any] | None = None) -> Any:
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(self.base_url + path, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ComfyError(f"ComfyUI request failed: {exc}") from exc

    def health(self) -> dict[str, Any]:
        stats = self._json("/system_stats")
        device = (stats.get("devices") or [{}])[0]
        return {
            "ready": True,
            "version": stats.get("system", {}).get("comfyui_version"),
            "device": device.get("name"),
            "vram_total": device.get("vram_total"),
            "vram_free": device.get("vram_free"),
        }

    def queue(self, workflow: dict[str, Any]) -> str:
        prompt_id = str(uuid.uuid4())
        result = self._json("/prompt", {"prompt": workflow, "client_id": "ugc-studio", "prompt_id": prompt_id})
        if "error" in result:
            raise ComfyError(str(result["error"]))
        return result.get("prompt_id", prompt_id)

    def wait(self, prompt_id: str, timeout: float = 600, interval: float = 1.0) -> ComfyOutput:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            history = self._json(f"/history/{prompt_id}")
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    messages = status.get("messages", [])
                    raise ComfyError(f"ComfyUI execution failed: {messages[-1] if messages else status}")
                for output in entry.get("outputs", {}).values():
                    images = output.get("images", [])
                    if images:
                        image = images[0]
                        return ComfyOutput(prompt_id, image["filename"], image.get("subfolder", ""), image.get("type", "output"))
            time.sleep(interval)
        raise ComfyError(f"ComfyUI timed out after {timeout:.0f}s")

    def image(self, output: ComfyOutput) -> bytes:
        query = urllib.parse.urlencode({"filename": output.filename, "subfolder": output.subfolder, "type": output.folder_type})
        try:
            with urllib.request.urlopen(f"{self.base_url}/view?{query}", timeout=self.timeout) as response:
                return response.read()
        except urllib.error.URLError as exc:
            raise ComfyError(f"Could not fetch ComfyUI output: {exc}") from exc


def flux_gguf_workflow(
    prompt: str,
    *,
    negative: str = "plastic skin, waxy, CGI, illustration, text, watermark, distorted architecture, oversaturated",
    width: int = 512,
    height: int = 768,
    steps: int = 20,
    guidance: float = 3.5,
    seed: int = 184762,
    filename_prefix: str = "ugc-studio/flux",
) -> dict[str, Any]:
    return {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-dev-Q4_K_S.gguf"}},
        "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {
            "clip_name1": "clip_l.safetensors", "clip_name2": "t5-v1_1-xxl-encoder-Q5_K_M.gguf", "type": "flux"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncodeFlux", "inputs": {"clip": ["2", 0], "clip_l": prompt, "t5xxl": prompt, "guidance": guidance}},
        "5": {"class_type": "CLIPTextEncodeFlux", "inputs": {"clip": ["2", 0], "clip_l": negative, "t5xxl": negative, "guidance": 1.0}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
            "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0], "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]}},
    }
