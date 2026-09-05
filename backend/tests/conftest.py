"""
Pytest configuration and fixtures for testing.
"""

import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient


# Use an in-memory SQLite database for testing
@pytest.fixture(scope="function")
def test_db():
    """Create a temporary SQLite database for testing."""
    # Create engine with in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a FastAPI test client with test database."""
    return TestClient(app)


@pytest.fixture
def admin_user(test_db):
    """Create a test admin user."""
    from app.models import AdminUser
    from app.security import hash_password
    
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("testpassword")
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    
    return admin


@pytest.fixture
def admin_token(client, admin_user):
    """Get a valid JWT token for the test admin user."""
    response = client.post(
        "/api/admin/login",
        json={"username": "testadmin", "password": "testpassword"}
    )
    return response.json()["access_token"]


@pytest.fixture
def sample_students(test_db):
    """Create sample students for testing."""
    from app.models import Student
    
    students = [
        Student(roll_number="24ME001", name="Rahul Kumar", branch="Mechanical", year=1),
        Student(roll_number="24ME002", name="Priya Singh", branch="Mechanical", year=1),
        Student(roll_number="24CS001", name="Amit Patel", branch="Computer Science", year=1),
        Student(roll_number="24CS002", name="Rahul Kumar", branch="Computer Science", year=1),  # Duplicate name
    ]
    
    for student in students:
        test_db.add(student)
    
    test_db.commit()
    
    # Refresh to get IDs
    for student in students:
        test_db.refresh(student)
    
    return students


@pytest.fixture
def sample_candidates(test_db):
    """Create sample candidates for testing."""
    from app.models import Candidate
    
    candidates = [
        Candidate(name="Candidate A", category="Mister Freshers", active=True),
        Candidate(name="Candidate B", category="Mister Freshers", active=True),
        Candidate(name="Candidate C", category="Miss Freshers", active=True),
        Candidate(name="Candidate D", category="Miss Freshers", active=False),  # Inactive
    ]
    
    for candidate in candidates:
        test_db.add(candidate)
    
    test_db.commit()
    
    for candidate in candidates:
        test_db.refresh(candidate)
    
    return candidates
