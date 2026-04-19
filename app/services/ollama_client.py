import json
import re

import httpx

from app.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")

    def embed(self, text: str) -> list[float]:
        with httpx.Client(timeout=30.0) as client:
            embed_resp = client.post(
                f"{self.base_url}/api/embed",
                json={"model": settings.ollama_embed_model, "input": text},
            )
            if embed_resp.status_code == 200:
                data = embed_resp.json()
                if "embeddings" in data and data["embeddings"]:
                    return data["embeddings"][0]
                if "embedding" in data:
                    return data["embedding"]

            fallback_resp = client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": text},
            )
            fallback_resp.raise_for_status()
            data = fallback_resp.json()
            if "embedding" not in data:
                raise ValueError("Ollama embedding response tidak memiliki field embedding")
            return data["embedding"]

    def generate_json(self, prompt: str) -> str:
        payload = {
            "model": settings.ollama_llm_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        raw = data.get("response", "")
        raw = raw.strip()
        if not raw:
            raise ValueError("LLM output kosong")
        return raw


def parse_json_loose(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))
