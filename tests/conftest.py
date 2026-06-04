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
from app.models import User, Lookup, RealCompetition
from app.security import hash_password
from app.context import RequestContext
from app.constants import LookupNum


# Use file-based SQLite database for tests (in-memory doesn't work with TestClient)
import tempfile
import os
_temp_dir = tempfile.gettempdir()
_test_db_path = os.path.join(_temp_dir, "test_eff.db")
TEST_SQLALCHEMY_DATABASE_URL = f"sqlite:///{_test_db_path}"


# Handle TINYINT in SQLite by mapping it to INTEGER
def _tinyint_visit(self, type_, **kw):
    return "INTEGER"

sqlite_base.SQLiteTypeCompiler.visit_TINYINT = _tinyint_visit


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    # Remove old test database if it exists
    if _test_db_path.startswith("/"):
        db_path = _test_db_path
    else:
        db_path = _test_db_path

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass

    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()

    # Cleanup after test
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def test_lookups(test_db):
    """Create test lookup data."""
    # Add country codes
    test_db.add(Lookup(lookupNum=LookupNum.COUNTRY_CODE, position=1, lookupKey="US", lookupCode="USA", lookupText="United States"))
    test_db.add(Lookup(lookupNum=LookupNum.COUNTRY_CODE, position=2, lookupKey="GB", lookupCode="GBR", lookupText="United Kingdom"))
    test_db.add(Lookup(lookupNum=LookupNum.COUNTRY_CODE, position=3, lookupKey="CA", lookupCode="CAN", lookupText="Canada"))

    # Add state codes
    test_db.add(Lookup(lookupNum=LookupNum.STATE_CODE, position=1, lookupKey="CA", lookupCode="CA", lookupText="California"))
    test_db.add(Lookup(lookupNum=LookupNum.STATE_CODE, position=2, lookupKey="NY", lookupCode="NY", lookupText="New York"))
    test_db.add(Lookup(lookupNum=LookupNum.STATE_CODE, position=3, lookupKey="TX", lookupCode="TX", lookupText="Texas"))

    test_db.commit()


@pytest.fixture(scope="function")
def test_real_competition(test_db):
    """Create a test real competition."""
    comp = RealCompetition(
        realCompetitionUID="EPL",
        realCompetitionSYMID="EN_PR",
        realCompetitionName="English Premier League",
        realCompetitionCountry="England",
        realCompetitionSeasonId="2025",
        realCompetitionSeasonName="2025-26",
        realCompetitionFirstMatchDay=1,
        realCompetitionLastMatchDay=38,
        baseRealCompetitionID=3,
        useExtraRealCompetition=0,
        calcStandings=1,
        createdIn=datetime.now(),
    )
    test_db.add(comp)
    test_db.commit()
    test_db.refresh(comp)
    return comp


@pytest.fixture(scope="function")
def test_user(test_db, test_lookups):
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


@pytest.fixture(scope="function")
def test_client(test_db, test_lookups, test_user):
    """Create a test client with test database."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_request_context():
    """Reset RequestContext after each test."""
    yield
    RequestContext.reset()
