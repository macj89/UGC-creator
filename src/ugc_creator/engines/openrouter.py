from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class OpenRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterVideo:
    job_id: str
    content: bytes
    cost_usd: float
    model: str


class OpenRouterClient:
    base_url = "https://openrouter.ai/api/v1"

    @property
    def ready(self) -> bool:
        return bool(os.environ.get("OPENROUTER_API_KEY"))

    def _request(self, path: str, data: dict[str, Any] | None = None, timeout: float = 60) -> Any:
        if not self.ready:
            raise OpenRouterError("OPENROUTER_API_KEY no está configurada")
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(self.base_url + path, data=body, headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8765",
            "X-Title": "UGC Studio",
        })
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                return json.load(response) if "json" in content_type else response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterError(f"OpenRouter {exc.code}: {detail[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise OpenRouterError(f"OpenRouter no disponible: {exc}") from exc

    def health(self) -> dict[str, Any]:
        key = self._request("/key")
        models = self._request("/videos/models").get("data", [])
        return {
            "ready": True,
            "usage_usd": key.get("data", {}).get("usage", 0),
            "limit_usd": key.get("data", {}).get("limit"),
            "video_models": [{"id": model["id"], "name": model.get("name", model["id"]),
                              "durations": model.get("supported_durations", []), "aspect_ratios": model.get("supported_aspect_ratios", []),
                              "frame_images": model.get("supported_frame_images", []), "pricing": model.get("pricing_skus", {})}
                             for model in models],
        }

    def image_to_video(self, image: bytes, prompt: str, *, model: str = "kwaivgi/kling-v3.0-std",
                       duration: int = 5, aspect_ratio: str = "9:16", resolution: str = "720p",
                       generate_audio: bool = False, timeout: float = 1200) -> OpenRouterVideo:
        data_uri = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
        job = self._request("/videos", {
            "model": model, "prompt": prompt, "duration": duration, "aspect_ratio": aspect_ratio,
            "resolution": resolution, "generate_audio": generate_audio,
            "frame_images": [{"type": "image_url", "image_url": {"url": data_uri}, "frame_type": "first_frame"}],
        }, timeout=120)
        job_id = job["id"]
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self._request(f"/videos/{job_id}")
            if status.get("status") == "completed":
                content = self._request(f"/videos/{job_id}/content?index=0", timeout=300)
                return OpenRouterVideo(job_id, content, float(status.get("usage", {}).get("cost") or 0), model)
            if status.get("status") == "failed":
                raise OpenRouterError(f"Generación fallida: {status.get('error', status)}")
            time.sleep(5)
        raise OpenRouterError(f"OpenRouter agotó el tiempo de espera para {job_id}")
