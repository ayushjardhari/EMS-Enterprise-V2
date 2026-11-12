import os

# Never load the embedding model during unit tests.
os.environ.setdefault("AUTO_INDEX_ON_UPLOAD", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_db
from app.core.security import hash_password
from app.db.base import Base
import app.models  # noqa: F401 — registers all models on Base.metadata
from app.main import app
from app.models.department import Department
from app.models.employee import Employee
from app.models.job_role import JobRole
from app.models.user import User, UserRole

# SQLite in-memory for fast, isolated test runs — no Docker/Postgres required
# to exercise business logic and routing. StaticPool keeps a single shared
# connection alive for the engine's lifetime; without it, SQLite's
# ":memory:" database is recreated empty on every new connection, which
# breaks anything using more than one DB connection per test (as the real
# app + TestClient does).
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Not using TestClient as a context manager: that would run the app's
    # startup event (ensure_bucket_exists), which needs a live MinIO — out
    # of scope for these unit tests, which only exercise routing/business
    # logic against the in-memory SQLite database above.
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client, db_session):
    admin = User(email="admin@acmecorp.example", hashed_password=hash_password("Admin@123"), user_role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.commit()
    response = client.post("/api/v1/auth/login", json={"email": "admin@acmecorp.example", "password": "Admin@123"})
    return response.json()["access_token"]


@pytest.fixture()
def sample_department(db_session):
    department = Department(name="Engineering")
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


@pytest.fixture()
def sample_job_role(db_session):
    job_role = JobRole(title="Backend Developer")
    db_session.add(job_role)
    db_session.commit()
    db_session.refresh(job_role)
    return job_role
