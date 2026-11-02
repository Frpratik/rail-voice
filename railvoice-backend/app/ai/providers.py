"""Free-tier AI providers (Groq, Google Gemini) and a chain that falls back between providers."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.ai.client import AIClient, AIUnavailable, Prompt
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 4000


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIUnavailable("AI returned malformed JSON") from exc
    if not isinstance(value, dict):
        raise AIUnavailable("AI returned the wrong shape")
    return value


def conform(value: Any, schema: dict[str, Any]) -> Any:
    """Fill in anything a less strict model left out, so feature code always gets every field."""
    kind = schema.get("type")
    if kind == "object":
        value = value if isinstance(value, dict) else {}
        return {k: conform(value.get(k), sub) for k, sub in schema.get("properties", {}).items()}
    if kind == "array":
        return [conform(v, schema.get("items", {})) for v in value] if isinstance(value, list) else []
    if "enum" in schema and value not in schema["enum"]:
        return schema["enum"][0]
    if kind == "string":
        return value if isinstance(value, str) else ("" if value is None else str(value))
    if kind == "boolean":
        return value if isinstance(value, bool) else str(value).lower() == "true"
    if kind == "integer":
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    return value


def _schema_note(schema: dict[str, Any]) -> str:
    return (
        "\n\nReply with only a JSON object (no other text) that matches this JSON schema exactly:\n"
        + json.dumps(schema)
    )


def _http_error(provider: str, prompt: Prompt, exc: Exception) -> AIUnavailable:
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 429:
            logger.warning("%s rate limited (%s)", provider, prompt.task)
            return AIUnavailable("AI is busy, please try again")
        logger.error("%s request failed (%s): %s %s", provider, prompt.task, code, exc.response.text[:300])
        return AIUnavailable("AI request failed")
    logger.error("%s unreachable (%s): %s", provider, prompt.task, type(exc).__name__)
    return AIUnavailable("AI is unreachable")


class GroqClient:
    """Groq's OpenAI-compatible API. Free tier: https://console.groq.com/keys"""

    name = "groq"
    supports_images = True
    url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str) -> None:
        self._http = httpx.AsyncClient(
            timeout=settings.ai_timeout_seconds, headers={"Authorization": f"Bearer {api_key}"}
        )

    def _body(self, prompt: Prompt, response_format: dict[str, Any] | None) -> dict[str, Any]:
        model = settings.groq_vision_model if prompt.images else settings.groq_model
        content: Any = prompt.text
        if prompt.images:
            content = [{"type": "text", "text": prompt.text}] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{i.media_type};base64,{base64.standard_b64encode(i.data).decode('ascii')}"
                    },
                }
                for i in prompt.images[:3]  # Groq's vision models take at most 3 images
            ]
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": content},
            ],
            "max_completion_tokens": MAX_OUTPUT_TOKENS,
        }
        if model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"
        if response_format:
            body["response_format"] = response_format
        return body

    async def _create(self, prompt: Prompt, response_format: dict[str, Any] | None) -> str:
        try:
            res = await self._http.post(self.url, json=self._body(prompt, response_format))
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise _http_error("Groq", prompt, exc) from exc
        choice = (res.json().get("choices") or [{}])[0]
        if choice.get("finish_reason") == "length":
            raise AIUnavailable("AI response was cut off")
        text = (choice.get("message") or {}).get("content") or ""
        if not text.strip():
            raise AIUnavailable("AI returned nothing")
        return text

    async def json(self, prompt: Prompt, schema: dict[str, Any]) -> dict[str, Any]:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": prompt.task, "strict": True, "schema": schema},
        }
        return conform(_parse_json(await self._create(prompt, response_format)), schema)

    async def text(self, prompt: Prompt) -> str:
        return await self._create(prompt, None)


class GeminiClient:
    """Google's Gemini API. Free tier: https://aistudio.google.com/apikey"""

    name = "gemini"
    supports_images = True
    base = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str) -> None:
        # The key goes in a header, never in the URL, so it can't end up in logs.
        self._http = httpx.AsyncClient(timeout=settings.ai_timeout_seconds, headers={"x-goog-api-key": api_key})

    async def _create(self, prompt: Prompt, extra_text: str, as_json: bool) -> str:
        parts: list[dict[str, Any]] = [
            {"inline_data": {"mime_type": i.media_type, "data": base64.standard_b64encode(i.data).decode("ascii")}}
            for i in prompt.images
        ]
        parts.append({"text": prompt.text + extra_text})
        config: dict[str, Any] = {"maxOutputTokens": MAX_OUTPUT_TOKENS}
        if as_json:
            config["responseMimeType"] = "application/json"
        body = {
            "systemInstruction": {"parts": [{"text": prompt.system}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": config,
        }
        try:
            res = await self._http.post(f"{self.base}/{settings.gemini_model}:generateContent", json=body)
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise _http_error("Gemini", prompt, exc) from exc
        data = res.json()
        if (data.get("promptFeedback") or {}).get("blockReason"):
            raise AIUnavailable("AI declined this request")
        candidate = (data.get("candidates") or [{}])[0]
        finish = candidate.get("finishReason")
        if finish == "MAX_TOKENS":
            raise AIUnavailable("AI response was cut off")
        if finish in {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "RECITATION"}:
            raise AIUnavailable("AI declined this request")
        text = "".join(
            p.get("text", "") for p in (candidate.get("content") or {}).get("parts", []) if not p.get("thought")
        )
        if not text.strip():
            raise AIUnavailable("AI returned nothing")
        return text

    async def json(self, prompt: Prompt, schema: dict[str, Any]) -> dict[str, Any]:
        return conform(_parse_json(await self._create(prompt, _schema_note(schema), True)), schema)

    async def text(self, prompt: Prompt) -> str:
        return await self._create(prompt, "", False)


class FallbackClient:
    """Tries each provider in order; a failure or rate limit moves on to the next."""

    def __init__(self, clients: list[AIClient]) -> None:
        self.clients = clients

    async def _run(self, prompt: Prompt, call) -> Any:
        last = AIUnavailable("No AI provider can handle this request")
        for client in self.clients:
            if prompt.images and not getattr(client, "supports_images", False):
                continue
            try:
                return await call(client)
            except AIUnavailable as exc:
                logger.warning("%s failed for %s (%s); trying the next provider", client.name, prompt.task, exc)
                last = exc
        raise last

    async def json(self, prompt: Prompt, schema: dict[str, Any]) -> dict[str, Any]:
        return await self._run(prompt, lambda c: c.json(prompt, schema))

    async def text(self, prompt: Prompt) -> str:
        return await self._run(prompt, lambda c: c.text(prompt))
