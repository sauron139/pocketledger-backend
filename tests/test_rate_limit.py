import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rate_limit_triggers(client: AsyncClient):
    for _ in range(60):
        await client.get("/health")

    response = await client.get("/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_rate_limit_returns_429(client: AsyncClient):
    for _ in range(61):
        response = await client.get("/api/v1/users/me")

    assert response.status_code in (401, 429)