from __future__ import annotations

import json
import os
import urllib.request
import urllib.error


class OpenAIProviderError(RuntimeError):
    pass


class OpenAIProvider:
    """
    Минимальный облачный провайдер.
    На этапе подготовки НЕ используется автоматически.
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        self.model = os.environ.get("QUIET_LOGOS_MODEL", "gpt-4.1-mini").strip()
        self.timeout_s = int(os.environ.get("QUIET_LOGOS_TIMEOUT_S", "45"))
        self.max_output_tokens = int(os.environ.get("QUIET_LOGOS_MAX_OUTPUT_TOKENS", "700"))

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_html_fragment(self, *, system_prompt: str, user_text: str) -> str:
        if not self.api_key:
            raise OpenAIProviderError("OPENAI_API_KEY is not set")

        url = f"{self.base_url}/responses"
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_text}]},
            ],
            "max_output_tokens": self.max_output_tokens,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            raise OpenAIProviderError(f"HTTPError {e.code}: {msg}") from e
        except Exception as e:
            raise OpenAIProviderError(f"Request failed: {e}") from e

        obj = json.loads(body)
        text = obj.get("output_text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        out = obj.get("output", [])
        chunks: list[str] = []
        for item in out:
            for c in item.get("content", []):
                t = c.get("text")
                if isinstance(t, str):
                    chunks.append(t)

        result = "\n".join(chunks).strip()
        if not result:
            raise OpenAIProviderError("Empty response text")
        return result
