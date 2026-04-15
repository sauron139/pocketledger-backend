import csv
import io
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_returns_csv(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    for i in range(3):
        await auth_client.post("/api/v1/transactions/", json={
            "type": "expense",
            "amount": str(1000 + i * 500),
            "currency": "NGN",
            "category_id": category_id,
            "description": f"expense {i}",
            "transaction_date": "2026-04-15",
        }, headers={"Idempotency-Key": str(uuid.uuid4())})

    response = await auth_client.get("/api/v1/exports/transactions")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "pocketledger" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_csv_structure(auth_client: AsyncClient):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    await auth_client.post("/api/v1/transactions/", json={
        "type": "expense",
        "amount": "2500",
        "currency": "NGN",
        "category_id": category_id,
        "description": "test export row",
        "transaction_date": "2026-04-15",
    }, headers={"Idempotency-Key": str(uuid.uuid4())})

    response = await auth_client.get("/api/v1/exports/transactions")
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)

    assert len(rows) >= 1
    row = rows[0]
    assert "id" in row
    assert "date" in row
    assert "type" in row
    assert "category" in row
    assert "amount" in row
    assert "currency" in row
    assert row["currency"] == "NGN"


@pytest.mark.asyncio
async def test_export_filter_by_type(auth_client: AsyncClient):
    cat_expense = (await auth_client.get("/api/v1/categories/?type=expense")).json()["data"][0]["id"]
    cat_income = (await auth_client.get("/api/v1/categories/?type=income")).json()["data"][0]["id"]

    await auth_client.post("/api/v1/transactions/", json={
        "type": "expense",
        "amount": "1000",
        "currency": "NGN",
        "category_id": cat_expense,
        "transaction_date": "2026-04-15",
    }, headers={"Idempotency-Key": str(uuid.uuid4())})

    await auth_client.post("/api/v1/transactions/", json={
        "type": "income",
        "amount": "5000",
        "currency": "NGN",
        "category_id": cat_income,
        "transaction_date": "2026-04-15",
    }, headers={"Idempotency-Key": str(uuid.uuid4())})

    response = await auth_client.get("/api/v1/exports/transactions?type=expense")
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)

    assert all(row["type"] == "expense" for row in rows)