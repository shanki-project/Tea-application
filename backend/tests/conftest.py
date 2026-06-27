"""Test fixtures.

Integration tests run against an in-memory SQLite DB (no MySQL needed for CI).
The MySQL-specific bits (InnoDB options, enum lengths) are ignored by SQLite, and
`native_enum=False` enums map to plain VARCHARs, so the same models work.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register all models on Base.metadata)
from app.core.database import Base, get_db
from app.crud import user as user_crud
from app.main import app
from app.models.enums import UserRole


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def super_admin(db_session):
    u = user_crud.create(
        db_session,
        name="Root",
        email="root@shankistea.com",
        password="password123",
        role=UserRole.super_admin,
    )
    db_session.commit()
    return u


def auth_header(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
