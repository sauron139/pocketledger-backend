import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import TransactionAuditLog


@pytest.mark.asyncio
async def test_transaction_update_creates_audit_log(auth_client: AsyncClient, db: AsyncSession):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    create_resp = await auth_client.post("/api/v1/transactions/", json={
        "type": "expense",
        "amount": "1000",
        "currency": "NGN",
        "category_id": category_id,
        "description": "original",
        "transaction_date": "2026-04-15",
    })
    tx_id = create_resp.json()["data"]["id"]

    await auth_client.patch(f"/api/v1/transactions/{tx_id}", json={
        "description": "updated",
    })

    result = await db.execute(
        select(TransactionAuditLog).where(
            TransactionAuditLog.transaction_id == tx_id
        )
    )
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].field == "description"
    assert logs[0].old_value == "original"
    assert logs[0].new_value == "updated"


@pytest.mark.asyncio
async def test_unchanged_fields_not_audited(auth_client: AsyncClient, db: AsyncSession):
    cat_resp = await auth_client.get("/api/v1/categories/?type=expense")
    category_id = cat_resp.json()["data"][0]["id"]

    create_resp = await auth_client.post("/api/v1/transactions/", json={
        "type": "expense",
        "amount": "1000",
        "currency": "NGN",
        "category_id": category_id,
        "description": "same",
        "transaction_date": "2026-04-15",
    })
    tx_id = create_resp.json()["data"]["id"]

    await auth_client.patch(f"/api/v1/transactions/{tx_id}", json={
        "description": "same",
    })

    result = await db.execute(
        select(TransactionAuditLog).where(
            TransactionAuditLog.transaction_id == tx_id
        )
    )
    logs = result.scalars().all()
    assert len(logs) == 0