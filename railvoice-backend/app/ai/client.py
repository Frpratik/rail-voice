"""Generative-AI client. Every feature goes through here, so the app runs unchanged when AI is off."""

from __future__ import annotations

import base64
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIUnavailable(Exception):
    """AI is off, failed, or declined. Callers fall back to the non-AI behaviour."""


@dataclass
class Image:
    data: bytes
    media_type: str


@dataclass
class Prompt:
    """One request: a task name (for logs and the fake), instructions, and the user content."""

    task: str
    system: str
    text: str
    images: list[Image] = field(default_factory=list)


class AIClient(Protocol):
    async def json(self, prompt: Prompt, schema: dict[str, Any]) -> dict[str, Any]: ...

    async def text(self, prompt: Prompt) -> str: ...


def _content(prompt: Prompt) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": image.media_type,
                "data": base64.standard_b64encode(image.data).decode("ascii"),
            },
        }
        for image in prompt.images
    ]
    blocks.append({"type": "text", "text": prompt.text})
    return blocks


class ClaudeClient:
    def __init__(self, api_key: str) -> None:
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key, timeout=settings.ai_timeout_seconds, max_retries=2
        )

    async def _create(self, prompt: Prompt, output_config: dict[str, Any], max_tokens: int):
        a = self._anthropic
        try:
            response = await self._client.beta.messages.create(
                model=settings.ai_model,
                max_tokens=max_tokens,
                system=prompt.system,
                messages=[{"role": "user", "content": _content(prompt)}],
                output_config=output_config,
                # On a safety decline, Anthropic re-runs the request on a suitable model.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except a.RateLimitError as exc:
            logger.warning("AI rate limited (%s)", prompt.task)
            raise AIUnavailable("AI is busy, please try again") from exc
        except a.APIStatusError as exc:
            logger.error("AI request failed (%s): %s %s", prompt.task, exc.status_code, exc.message)
            raise AIUnavailable("AI request failed") from exc
        except a.APIConnectionError as exc:
            logger.error("AI connection failed (%s)", prompt.task)
            raise AIUnavailable("AI is unreachable") from exc

        if response.stop_reason == "refusal":
            raise AIUnavailable("AI declined this request")
        if response.stop_reason == "max_tokens":
            raise AIUnavailable("AI response was cut off")
        text = "".join(block.text for block in response.content if block.type == "text")
        if not text.strip():
            raise AIUnavailable("AI returned nothing")
        return text

    async def json(self, prompt: Prompt, schema: dict[str, Any]) -> dict[str, Any]:
        text = await self._create(
            prompt,
            {"effort": settings.ai_effort, "format": {"type": "json_schema", "schema": schema}},
            max_tokens=4000,
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIUnavailable("AI returned malformed JSON") from exc

    async def text(self, prompt: Prompt) -> str:
        return await self._create(prompt, {"effort": settings.ai_effort}, max_tokens=4000)


class FakeClient:
    """Deterministic stand-in for tests and local demos. Never used in production."""

    def __init__(self) -> None:
        self.calls: list[Prompt] = []
        self.handlers: dict[str, Callable[[Prompt], Any]] = {}

    async def json(self, prompt: Prompt, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(prompt)
        handler = self.handlers.get(prompt.task) or FAKE_HANDLERS.get(prompt.task)
        if handler is None:
            raise AIUnavailable(f"No fake response for {prompt.task}")
        return handler(prompt)

    async def text(self, prompt: Prompt) -> str:
        self.calls.append(prompt)
        handler = self.handlers.get(prompt.task) or FAKE_HANDLERS.get(prompt.task)
        if handler is None:
            raise AIUnavailable(f"No fake response for {prompt.task}")
        return handler(prompt)


# Feature modules register their fake answers here.
FAKE_HANDLERS: dict[str, Callable[[Prompt], Any]] = {}

_override: AIClient | None = None
_cached: AIClient | None = None


def set_ai(client: AIClient | None) -> None:
    """Swap the client (tests). Pass None to go back to the configured one."""
    global _override
    _override = client


def get_ai() -> AIClient | None:
    global _cached
    if _override is not None:
        return _override
    provider = settings.ai_provider.strip().lower()
    if provider == "claude" and settings.anthropic_api_key:
        if not isinstance(_cached, ClaudeClient):
            _cached = ClaudeClient(settings.anthropic_api_key)
        return _cached
    if provider == "fake" and not settings.is_production:
        if not isinstance(_cached, FakeClient):
            _cached = FakeClient()
        return _cached
    return None


def require_ai() -> AIClient:
    client = get_ai()
    if client is None:
        raise AIUnavailable("AI features are turned off")
    return client


def ai_enabled() -> bool:
    return get_ai() is not None


def obj(properties: dict[str, Any]) -> dict[str, Any]:
    """JSON schema for an object whose fields are all required, as structured outputs expect."""
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
