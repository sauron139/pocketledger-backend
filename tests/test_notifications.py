import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_budget_threshold_notification(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    await auth_client.post("/api/v1/budgets/", json={
        "category_id": category_id,
        "amount": "10000",
        "currency": "NGN",
        "period": "monthly",
        "start_date": "2026-01-01",
        "is_recurring": True,
    })

    await auth_client.post("/api/v1/transactions/", json={
        "type": "expense",
        "amount": "8500",
        "currency": "NGN",
        "category_id": category_id,
        "transaction_date": "2026-04-15",
    })

    import asyncio
    await asyncio.sleep(0.1)

    resp = await auth_client.get("/api/v1/notifications/")
    assert resp.status_code == 200
    notifications = resp.json()["data"]
    thresholds = [n["threshold"] for n in notifications]
    assert 80 in thresholds
    assert 100 not in thresholds


@pytest.mark.asyncio
async def test_no_duplicate_notifications(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    await auth_client.post("/api/v1/budgets/", json={
        "category_id": category_id,
        "amount": "10000",
        "currency": "NGN",
        "period": "monthly",
        "start_date": "2026-01-01",
        "is_recurring": True,
    })

    for _ in range(3):
        await auth_client.post("/api/v1/transactions/", json={
            "type": "expense",
            "amount": "3500",
            "currency": "NGN",
            "category_id": category_id,
            "transaction_date": "2026-04-15",
        })

    import asyncio
    await asyncio.sleep(0.1)

    resp = await auth_client.get("/api/v1/notifications/")
    notifications = resp.json()["data"]
    threshold_100_count = sum(1 for n in notifications if n["threshold"] == 100)
    assert threshold_100_count == 1