import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.dialects.sqlite import base as sqlite_base
from sqlmodel import SQLModel, Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import User
from app.security import hash_password
from app.context import RequestContext


# Use SQLite in-memory database for tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


# Handle TINYINT in SQLite by mapping it to INTEGER
def _tinyint_visit(self, type_, **kw):
    return "INTEGER"

sqlite_base.SQLiteTypeCompiler.visit_TINYINT = _tinyint_visit


@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client with test database."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user."""
    user = User(
        userEmail="test@example.com",
        userPassword=hash_password("password123"),
        userName="testuser",
        userLevel=1,
        firstName="Test",
        lastName="User",
        birthday=datetime(1990, 1, 1),
        country="US",
        state="CA",
        city="San Francisco",
        phoneNumber="415-555-0100",
        timeZone="America/Los_Angeles",
        createdIn=datetime.now(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(autouse=True)
def reset_request_context():
    """Reset RequestContext after each test."""
    yield
    RequestContext.reset()
