import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_health_check_returns_ok() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_liveness_and_metrics_are_exposed() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        live_response = await client.get("/api/v1/health/live")
        metrics_response = await client.get("/metrics/")

    assert live_response.status_code == 200
    assert live_response.json() == {"status": "ok"}
    assert metrics_response.status_code == 200
    assert "space_dashboard_http_requests_total" in metrics_response.text
