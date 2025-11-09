import pytest
from httpx import AsyncClient
from src.main import build_app

@pytest.mark.asyncio
async def test_analyze_endpoint_smoke():
    app = build_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        body = {"context":{"user_id":"u1","case_id":"c1"}, "meta":{}}
        r = await ac.post("/api/analyze", json=body)
        assert r.status_code == 200
        assert r.json()["success"] is True
