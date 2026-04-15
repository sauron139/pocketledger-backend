import pytest
from datetime import date
from httpx import AsyncClient
from app.scheduler import materialize_recurring_transactions


@pytest.mark.asyncio
async def test_recurring_transaction_materialization(auth_client: AsyncClient, db):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    today = date.today().isoformat()

    await auth_client.post("/api/v1/recurring/", json={
        "type": "expense",
        "amount": "5000",
        "currency": "NGN",
        "category_id": category_id,
        "frequency": "monthly",
        "next_run_date": today,
    })

    await materialize_recurring_transactions()

    resp = await auth_client.get("/api/v1/transactions/?source=recurring")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_recurring_idempotency(auth_client: AsyncClient, db):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    today = date.today().isoformat()

    await auth_client.post("/api/v1/recurring/", json={
        "type": "expense",
        "amount": "5000",
        "currency": "NGN",
        "category_id": category_id,
        "frequency": "monthly",
        "next_run_date": today,
    })

    await materialize_recurring_transactions()
    await materialize_recurring_transactions()

    resp = await auth_client.get("/api/v1/transactions/?source=recurring")
    total = resp.json()["data"]["total"]
    assert total == 1