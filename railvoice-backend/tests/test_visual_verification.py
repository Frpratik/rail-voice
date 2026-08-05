import pytest
import io
from PIL import Image
from httpx import AsyncClient
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.issue import Issue

API = "/api/v1"

@pytest.mark.asyncio
async def test_resolve_issue_with_verification(client: AsyncClient):
    # Fetch an existing issue or create directly in DB
    async with async_session_factory() as db:
        res = await db.execute(select(Issue))
        issue = res.scalars().first()
        assert issue is not None, "An issue should exist in the seed DB"
        issue_id = str(issue.id)

    # Create dummy image in memory
    img = Image.new("RGB", (300, 300), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    # Call endpoint with multipart file
    response = await client.post(
        f"{API}/issues/{issue_id}/resolve-with-verification",
        files={"file": ("resolution_test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "verification_score" in data
    assert data["verification_score"] > 0
    assert "resolution_status" in data
