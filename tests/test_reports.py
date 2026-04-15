import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_comparison_report_structure(auth_client: AsyncClient):
    resp = await auth_client.get("/api/v1/reports/comparison?period=monthly")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert "current_period" in data
    assert "previous_period" in data
    assert "income" in data
    assert "expense" in data
    assert "net" in data

    for key in ["income", "expense", "net"]:
        assert "current" in data[key]
        assert "previous" in data[key]
        assert "absolute" in data[key]
        assert "percentage" in data[key]


@pytest.mark.asyncio
async def test_comparison_percentage_null_when_no_previous_data(auth_client: AsyncClient):
    resp = await auth_client.get("/api/v1/reports/comparison?period=monthly")
    data = resp.json()["data"]
    assert data["income"]["percentage"] is None
    assert data["expense"]["percentage"] is None