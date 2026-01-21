"""Integration tests for authentication API endpoints.

Following strict TDD - tests written FIRST.
These tests use FastAPI TestClient to test the actual HTTP endpoints.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import date, timedelta


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite with StaticPool to persist across connections
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Keep the same connection
    )

    # Import Base and models
    from fittrack.database import Base
    from fittrack.models.user import User  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()  # Rollback any uncommitted changes
        db.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """Create a test client with database override."""
    from fittrack.api.routes.v1.auth import router as auth_router

    # Create a fresh FastAPI app for testing
    test_app = FastAPI()
    test_app.include_router(auth_router)

    # Create a session factory bound to test engine
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    # Override the get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from fittrack.api.dependencies import get_db
    test_app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(test_app) as test_client:
        yield test_client

    # Cleanup
    test_app.dependency_overrides.clear()


class TestRegisterEndpoint:
    """Test POST /api/v1/auth/register endpoint."""

    def test_register_success(self, client):
        """Register should create user and return success message."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecureP@ssw0rd123!",
                "date_of_birth": "1990-01-15",
                "state_of_residence": "TX"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data
        assert data["email"] == "newuser@example.com"
        assert "verify your email" in data["message"].lower()

    def test_register_duplicate_email(self, client):
        """Register should fail with 409 for duplicate email."""
        # First registration
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecureP@ssw0rd123!",
                "date_of_birth": "1990-01-15",
                "state_of_residence": "TX"
            }
        )

        # Second registration with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentP@ss456!",
                "date_of_birth": "1992-03-20",
                "state_of_residence": "CA"
            }
        )

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_register_weak_password(self, client):
        """Register should fail with 422 for weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",
                "date_of_birth": "1990-01-15",
                "state_of_residence": "TX"
            }
        )

        assert response.status_code == 422
        data = response.json()
        # Pydantic validation returns a list of errors
        assert isinstance(data["detail"], list)
        # Check that one of the errors is about password
        error_messages = str(data["detail"]).lower()
        assert "password" in error_messages

    def test_register_underage(self, client):
        """Register should fail with 400 for underage user."""
        # DOB that makes user 17 years old
        underage_dob = (date.today() - timedelta(days=17*365)).isoformat()

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "younguser@example.com",
                "password": "SecureP@ssw0rd123!",
                "date_of_birth": underage_dob,
                "state_of_residence": "TX"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "18" in data["detail"]

    def test_register_ineligible_state(self, client):
        """Register should fail with 400 for ineligible state."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecureP@ssw0rd123!",
                "date_of_birth": "1990-01-15",
                "state_of_residence": "NY"  # Ineligible state
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "not available" in data["detail"].lower() or "ny" in data["detail"].lower()

    def test_register_invalid_email(self, client):
        """Register should fail with 422 for invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecureP@ssw0rd123!",
                "date_of_birth": "1990-01-15",
                "state_of_residence": "TX"
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "email" in str(data).lower()


class TestLoginEndpoint:
    """Test POST /api/v1/auth/login endpoint."""

    def test_login_success(self, client, test_db):
        """Login should return access and refresh tokens for valid credentials."""
        # First register a user
        from fittrack.models.user import User
        from fittrack.security.authentication import hash_password

        user = User(
            email="loginuser@example.com",
            password_hash=hash_password("SecureP@ssw0rd123!"),
            status="active",
            role="user",
            email_verified=True
        )
        test_db.add(user)
        test_db.commit()

        # Now login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginuser@example.com",
                "password": "SecureP@ssw0rd123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "loginuser@example.com"

    def test_login_wrong_password(self, client, test_db):
        """Login should fail with 401 for wrong password."""
        # Register user
        from fittrack.models.user import User
        from fittrack.security.authentication import hash_password

        user = User(
            email="loginuser@example.com",
            password_hash=hash_password("SecureP@ssw0rd123!"),
            status="active",
            role="user",
            email_verified=True
        )
        test_db.add(user)
        test_db.commit()

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginuser@example.com",
                "password": "WrongPassword456!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_login_user_not_found(self, client):
        """Login should fail with 401 for non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecureP@ssw0rd123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_login_unverified_email(self, client, test_db):
        """Login should fail with 403 for unverified email."""
        from fittrack.models.user import User
        from fittrack.security.authentication import hash_password

        user = User(
            email="unverified@example.com",
            password_hash=hash_password("SecureP@ssw0rd123!"),
            status="pending",
            role="user",
            email_verified=False
        )
        test_db.add(user)
        test_db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "unverified@example.com",
                "password": "SecureP@ssw0rd123!"
            }
        )

        assert response.status_code == 403
        data = response.json()
        assert "verify" in data["detail"].lower() or "email" in data["detail"].lower()

    def test_login_suspended_account(self, client, test_db):
        """Login should fail with 403 for suspended account."""
        from fittrack.models.user import User
        from fittrack.security.authentication import hash_password

        user = User(
            email="suspended@example.com",
            password_hash=hash_password("SecureP@ssw0rd123!"),
            status="suspended",
            role="user",
            email_verified=True
        )
        test_db.add(user)
        test_db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "suspended@example.com",
                "password": "SecureP@ssw0rd123!"
            }
        )

        assert response.status_code == 403
        data = response.json()
        assert "suspended" in data["detail"].lower()


class TestRefreshEndpoint:
    """Test POST /api/v1/auth/refresh endpoint."""

    def test_refresh_success(self, client, test_db):
        """Refresh should return new access token for valid refresh token."""
        # Create user
        from fittrack.models.user import User
        from fittrack.security.authentication import hash_password, create_refresh_token
        from uuid import UUID

        user = User(
            email="refreshuser@example.com",
            password_hash=hash_password("SecureP@ssw0rd123!"),
            status="active",
            role="user",
            email_verified=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Create refresh token
        refresh_token = create_refresh_token(user_id=UUID(user.user_id))

        # Call refresh endpoint
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, client):
        """Refresh should fail with 401 for invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid.token.here"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()

    def test_refresh_user_not_found(self, client):
        """Refresh should fail with 401 if user no longer exists."""
        from fittrack.security.authentication import create_refresh_token
        from uuid import uuid4

        # Create token for non-existent user
        fake_user_id = uuid4()
        refresh_token = create_refresh_token(user_id=fake_user_id)

        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()
