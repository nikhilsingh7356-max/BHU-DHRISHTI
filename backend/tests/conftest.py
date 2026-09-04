import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres123@localhost:5432/bhudrishti_test"

from app.models.models import (
    Base, Role, Profile, Permission, RolePermission, Department,
    State, District, Tehsil, Village,
)
from app.security.password import hash_password


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        role = Role(
            id=uuid.UUID("a0000000-0000-0000-0000-000000000001"),
            name="SUPER_ADMIN",
            description="Test super admin",
        )
        session.add(role)
        admin = Profile(
            email="superadmin@bhudrishti.gov.in",
            password_hash=hash_password("Super@123"),
            full_name="Test Super Admin",
            role_id=role.id,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
    return factory


@pytest.fixture
async def db(test_session_factory):
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def client(test_session_factory):
    from app.main import app
    from app.core.database import get_db

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=__import__("httpx").ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_token(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@bhudrishti.gov.in", "password": "Super@123"},
    )
    if response.status_code == 200:
        data = response.json()["data"]
        return data["access_token"]
    return None
