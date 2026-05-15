from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaStatus:
    running: bool
    models: list[str]
    error: str | None = None


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def list_models(self, timeout: float = 2.5) -> OllamaStatus:
        request = urllib.request.Request(f"{self.base_url}/api/tags")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return OllamaStatus(False, [], str(exc))

        models = sorted(
            model.get("name", "")
            for model in payload.get("models", [])
            if isinstance(model, dict) and model.get("name")
        )
        return OllamaStatus(True, models, None)

    def chat(self, model: str, messages: list[dict[str, str]], timeout: float = 120.0) -> str:
        payload = json.dumps(
            {
                "model": model,
                "messages": messages,
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama chat failed: {exc}") from exc
        message = data.get("message", {})
        content = message.get("content", "") if isinstance(message, dict) else ""
        if not content.strip():
            raise RuntimeError("Ollama returned an empty answer.")
        return content.strip()

    def embed(self, model: str, inputs: list[str], timeout: float = 120.0) -> list[list[float]]:
        payload = json.dumps({"model": model, "input": inputs}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama embedding failed: {exc}") from exc

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list):
            raise RuntimeError("Ollama returned no embeddings.")
        return embeddings
