import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_idempotency_key_required(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    response = await auth_client.post("/api/v1/transactions/", json={
        "type": "expense",
        "amount": "1000",
        "currency": "NGN",
        "category_id": category_id,
        "transaction_date": "2026-04-15",
    })
    assert response.status_code == 400
    assert "Idempotency-Key" in response.json()["message"]


@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    key = str(uuid.uuid4())
    payload = {
        "type": "expense",
        "amount": "1000",
        "currency": "NGN",
        "category_id": category_id,
        "transaction_date": "2026-04-15",
    }

    first = await auth_client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    second = await auth_client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert second.headers.get("X-Idempotent-Replayed") == "true"


@pytest.mark.asyncio
async def test_different_keys_create_different_transactions(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    payload = {
        "type": "expense",
        "amount": "1000",
        "currency": "NGN",
        "category_id": category_id,
        "transaction_date": "2026-04-15",
    }

    first = await auth_client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    second = await auth_client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )

    assert first.json()["data"]["id"] != second.json()["data"]["id"]