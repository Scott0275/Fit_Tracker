"""Integration tests for protected endpoints requiring authentication.

Following strict TDD - tests written FIRST.
Tests verify that endpoints properly require authentication tokens.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from fittrack.database import Base
    from fittrack.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield engine

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
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """Create a test client with database override."""
    from fittrack.api.routes.v1.auth import router as auth_router
    from fittrack.api.routes.v1.users import router as users_router

    test_app = FastAPI()
    test_app.include_router(auth_router)
    test_app.include_router(users_router)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from fittrack.api.dependencies import get_db
    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()


@pytest.fixture
def authenticated_user(test_db):
    """Create an authenticated user and return user data."""
    from fittrack.models.user import User
    from fittrack.security.authentication import hash_password

    user = User(
        email="testuser@example.com",
        password_hash=hash_password("SecureP@ssw0rd123!"),
        status="active",
        role="user",
        email_verified=True,
        point_balance=500
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return {
        "user_id": user.user_id,
        "email": user.email,
        "password": "SecureP@ssw0rd123!"
    }


@pytest.fixture
def access_token(client, authenticated_user):
    """Get an access token for authenticated requests."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": authenticated_user["email"],
            "password": authenticated_user["password"]
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestGetCurrentUserProfile:
    """Test GET /api/v1/users/me endpoint - requires authentication."""

    def test_get_profile_without_token(self, client):
        """Get profile should return 401 without authentication token."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_profile_with_invalid_token(self, client):
        """Get profile should return 401 with invalid token."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_profile_with_valid_token(self, client, access_token, authenticated_user):
        """Get profile should return user data with valid token."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["email"]
        assert data["role"] == "user"
        assert data["point_balance"] == 500
        assert "password_hash" not in data  # Should not expose password hash

    def test_get_profile_includes_user_id(self, client, access_token):
        """Get profile should include user_id."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["user_id"] is not None


class TestUpdateUserProfile:
    """Test PUT /api/v1/users/me endpoint - requires authentication."""

    def test_update_profile_without_token(self, client):
        """Update profile should return 401 without authentication token."""
        response = client.put(
            "/api/v1/users/me",
            json={"point_balance": 1000}
        )

        assert response.status_code == 401

    def test_update_profile_with_valid_token(self, client, access_token):
        """Update profile should work with valid token (limited fields)."""
        # Note: Users should only be able to update certain fields
        # For now, just test that the endpoint is protected
        response = client.put(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )

        # Should return 200 or 422 (validation error), not 401
        assert response.status_code in [200, 422]


class TestGetUserPointBalance:
    """Test GET /api/v1/users/me/points endpoint - requires authentication."""

    def test_get_points_without_token(self, client):
        """Get points should return 401 without authentication token."""
        response = client.get("/api/v1/users/me/points")

        assert response.status_code == 401

    def test_get_points_with_valid_token(self, client, access_token):
        """Get points should return point balance with valid token."""
        response = client.get(
            "/api/v1/users/me/points",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "point_balance" in data
        assert data["point_balance"] == 500


class TestHealthEndpointsRemainPublic:
    """Test that health endpoints remain public (no auth required)."""

    def test_health_check_no_auth_required(self, client):
        """Health check should work without authentication."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_ready_check_no_auth_required(self, client):
        """Ready check should work without authentication."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
