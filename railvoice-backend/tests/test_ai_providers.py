"""Groq and Gemini clients and the fallback chain, against mocked HTTP."""

import json

import httpx
import pytest

from app.ai.client import AIUnavailable, FakeClient, Image, Prompt, obj
from app.ai.providers import FallbackClient, GeminiClient, GroqClient, conform

SCHEMA = obj({"title": {"type": "string"}, "ok": {"type": "boolean"}, "lang": {"type": "string", "enum": ["en", "hi"]}})


def _mock(client, handler):
    headers = client._http.headers
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler), headers=headers)
    return client


@pytest.mark.asyncio
async def test_groq_request_shape():
    sent = {}

    def handler(request: httpx.Request):
        sent["url"] = str(request.url)
        sent["auth"] = request.headers["authorization"]
        sent["body"] = json.loads(request.content)
        content = json.dumps({"title": "Lift broken", "ok": True, "lang": "hi"})
        return httpx.Response(200, json={"choices": [{"message": {"content": content}, "finish_reason": "stop"}]})

    client = _mock(GroqClient("gsk-test"), handler)
    result = await client.json(Prompt(task="t", system="sys", text="hello"), SCHEMA)
    assert result == {"title": "Lift broken", "ok": True, "lang": "hi"}
    assert sent["url"].startswith("https://api.groq.com/openai/v1/chat/completions")
    assert sent["auth"] == "Bearer gsk-test"
    body = sent["body"]
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["messages"][0] == {"role": "system", "content": "sys"}
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True

    await client.json(Prompt(task="t", system="s", text="x", images=[Image(b"jpg", "image/jpeg")] * 4), SCHEMA)
    body = sent["body"]
    assert body["model"] == "qwen/qwen3.8-27b"
    images = [p for p in body["messages"][1]["content"] if p["type"] == "image_url"]
    assert len(images) == 3 and images[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_groq_errors_become_unavailable():
    client = _mock(GroqClient("k"), lambda r: httpx.Response(429, json={"error": "rate"}))
    with pytest.raises(AIUnavailable, match="busy"):
        await client.json(Prompt(task="t", system="s", text="x"), SCHEMA)
    cut = _mock(GroqClient("k"), lambda r: httpx.Response(200, json={"choices": [{"message": {"content": "{"}, "finish_reason": "length"}]}))
    with pytest.raises(AIUnavailable, match="cut off"):
        await cut.json(Prompt(task="t", system="s", text="x"), SCHEMA)


@pytest.mark.asyncio
async def test_gemini_request_shape_and_conform():
    sent = {}

    def handler(request: httpx.Request):
        sent["url"] = str(request.url)
        sent["key"] = request.headers.get("x-goog-api-key")
        sent["body"] = json.loads(request.content)
        text = '```json\n{"title": "Bin full", "lang": "fr"}\n```'
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]})

    client = _mock(GeminiClient("AIza-test"), handler)
    result = await client.json(
        Prompt(task="t", system="sys", text="hello", images=[Image(b"png", "image/png")]), SCHEMA
    )
    # Missing and invalid fields are filled so feature code always gets the full shape.
    assert result == {"title": "Bin full", "ok": False, "lang": "en"}
    assert sent["url"].endswith("/models/gemini-3.8-flash:generateContent")
    assert "key=" not in sent["url"] and sent["key"] == "AIza-test"
    body = sent["body"]
    assert body["systemInstruction"]["parts"][0]["text"] == "sys"
    assert body["contents"][0]["parts"][0]["inline_data"]["mime_type"] == "image/png"
    assert "JSON schema" in body["contents"][0]["parts"][-1]["text"]
    assert body["generationConfig"]["responseMimeType"] == "application/json"


@pytest.mark.asyncio
async def test_gemini_block_is_unavailable():
    client = _mock(GeminiClient("k"), lambda r: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}}))
    with pytest.raises(AIUnavailable, match="declined"):
        await client.text(Prompt(task="t", system="s", text="x"))


@pytest.mark.asyncio
async def test_fallback_moves_to_next_provider():
    first = _mock(GroqClient("k"), lambda r: httpx.Response(503, text="down"))
    second = FakeClient()
    second.handlers["t"] = lambda p: {"title": "from backup", "ok": True, "lang": "en"}
    chain = FallbackClient([first, second])
    result = await chain.json(Prompt(task="t", system="s", text="x"), SCHEMA)
    assert result["title"] == "from backup"

    broken = FakeClient()
    broken.handlers["t"] = lambda p: (_ for _ in ()).throw(AIUnavailable("down"))
    with pytest.raises(AIUnavailable):
        await FallbackClient([first, broken]).json(Prompt(task="t", system="s", text="x"), SCHEMA)


def test_chain_built_from_settings(monkeypatch):
    from app.ai import client as ai_client
    from app.core.config import settings

    monkeypatch.setattr(settings, "ai_provider", "groq, gemini")
    monkeypatch.setattr(settings, "groq_api_key", "g")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert ai_client.provider_names() == ["groq"]  # a provider without a key is skipped
    monkeypatch.setattr(settings, "gemini_api_key", "m")
    assert ai_client.provider_names() == ["groq", "gemini"]
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert ai_client.get_ai() is None


def test_conform_nested():
    schema = obj({"items": {"type": "array", "items": obj({"n": {"type": "integer"}})}})
    assert conform({"items": [{"n": "3"}, {}]}, schema) == {"items": [{"n": 3}, {"n": 0}]}
    assert conform(None, schema) == {"items": []}
