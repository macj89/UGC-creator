from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class ElevenLabsError(RuntimeError):
    pass


class ElevenLabsClient:
    base_url = "https://api.elevenlabs.io/v1"

    @property
    def ready(self) -> bool:
        return bool(os.environ.get("ELEVENLABS_API_KEY"))

    def _request(self, path: str, data: dict[str, Any] | None = None) -> tuple[bytes, str]:
        if not self.ready:
            raise ElevenLabsError("ELEVENLABS_API_KEY no está configurada")
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(self.base_url + path, data=body, headers={
            "xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            raise ElevenLabsError(f"ElevenLabs {exc.code}: {exc.read().decode(errors='replace')[:1000]}") from exc

    def voices(self) -> list[dict[str, str]]:
        body, _ = self._request("/voices")
        return [{"id": voice["voice_id"], "name": voice["name"]} for voice in json.loads(body)["voices"]]

    def text_to_speech(self, text: str, voice_id: str) -> bytes:
        body, _ = self._request(f"/text-to-speech/{voice_id}", {
            "text": text, "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
        })
        return body
