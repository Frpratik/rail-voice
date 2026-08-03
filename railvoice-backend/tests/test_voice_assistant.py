import pytest
from httpx import AsyncClient

from app.ai.voice_assistant import voice_assistant

API = "/api/v1"


def test_voice_assistant_hindi_detection():
    transcript = "बांद्रा स्टेशन पर प्लेटफार्म 1 के पास पानी का लीकेज है"
    res = voice_assistant.process_voice_input(transcript)

    assert res["detected_language"] == "hi"
    assert res["station_code"] == "BA"
    assert res["station_name"] == "Bandra"
    assert res["category_code"] == "facilities"


def test_voice_assistant_marathi_detection():
    transcript = "अंधेरी स्टेशन वर सरकता जिना बंद आहे"
    res = voice_assistant.process_voice_input(transcript)

    assert res["detected_language"] == "mr"
    assert res["station_code"] == "ADH"
    assert res["station_name"] == "Andheri"
    assert res["category_code"] == "lifts_escalators"


@pytest.mark.asyncio
async def test_voice_parse_endpoint(client: AsyncClient):
    payload = {"transcript": "बोरीवली स्टेशन प्लेटफार्म 2 पर कचरा जमा है"}
    res = await client.post(f"{API}/voice/parse", json=payload)

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["station_code"] == "BVI"
    assert data["detected_language"] in {"hi", "mr"}
    assert "Spoken grievance" in data["translated_summary"]


@pytest.mark.asyncio
async def test_voice_create_issue_endpoint(client: AsyncClient):
    payload = {"transcript": "दादर स्टेशन पर गर्दी और सुरक्षेचा प्रश्न आहे"}
    res = await client.post(f"{API}/voice/create-issue", json=payload)

    assert res.status_code == 201
    data = res.json()["data"]
    assert data["issue_id"] is not None
    assert data["station_code"] == "DDR"
    assert data["detected_language"] == "mr"
