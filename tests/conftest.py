import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_db, get_redis
from app.db.base import Base
from app.main import app
from app.models import *  # noqa

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/pocketledger_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    class FakeRedis:
        store = {}

        async def get(self, key): return self.store.get(key)
        async def setex(self, key, ttl, value): self.store[key] = value
        async def delete(self, key): self.store.pop(key, None)

    fake_redis = FakeRedis()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_redis] = lambda: fake_redis

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "base_currency": "NGN",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    token = response.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client