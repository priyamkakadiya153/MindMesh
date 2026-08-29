from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    DATABASE_URL_TEST,
    poolclass=StaticPool,
    future=True
)
TestingSessionLocal = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Patch AsyncSessionLocal before importing app
import app.core.database
app.core.database.AsyncSessionLocal = TestingSessionLocal

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from app.main import app

from app.core.database import get_db_session
from app.models.base import BaseEntity
import app.models as _app_models


import pytest_asyncio

# event_loop fixture removed to fix pytest-asyncio compatibility issues.


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True)
    except Exception:
        ac = AsyncClient(app=app, base_url="http://test", follow_redirects=True)
    async with ac:
        yield ac

    app.dependency_overrides.clear()

