"""Unit tests for authentication service.

Following strict TDD - tests written FIRST.
"""
import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4


class TestUserRegistration:
    """Test user registration flow with validation."""

    def test_register_user_success(self):
        """Register user should create user with hashed password."""
        from fittrack.services.auth_service import AuthService

        # Mock dependencies
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing user

        service = AuthService(db_session=mock_db)

        result = service.register_user(
            email="newuser@example.com",
            password="SecureP@ssw0rd123!",
            date_of_birth="1990-01-15",
            state_of_residence="TX"
        )

        assert result["success"] is True
        assert "user_id" in result
        assert result["email"] == "newuser@example.com"
        # Verify user was added to session
        mock_db.add.assert_called_once()

    def test_register_user_duplicate_email(self):
        """Register user should fail if email already exists."""
        from fittrack.services.auth_service import AuthService

        # Mock existing user
        existing_user = Mock()
        existing_user.email = "existing@example.com"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user

        service = AuthService(db_session=mock_db)

        result = service.register_user(
            email="existing@example.com",
            password="SecureP@ssw0rd123!",
            date_of_birth="1990-01-15",
            state_of_residence="TX"
        )

        assert result["success"] is False
        assert "already exists" in result["message"].lower()

    def test_register_user_weak_password(self):
        """Register user should fail if password is weak."""
        from fittrack.services.auth_service import AuthService

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing user

        service = AuthService(db_session=mock_db)

        result = service.register_user(
            email="newuser@example.com",
            password="weak",
            date_of_birth="1990-01-15",
            state_of_residence="TX"
        )

        assert result["success"] is False
        assert "password" in result["message"].lower()

    def test_register_user_underage(self):
        """Register user should fail if user is under 18."""
        from fittrack.services.auth_service import AuthService

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AuthService(db_session=mock_db)

        # DOB that makes user 17 years old
        from datetime import date, timedelta
        underage_dob = (date.today() - timedelta(days=17*365)).isoformat()

        result = service.register_user(
            email="younguser@example.com",
            password="SecureP@ssw0rd123!",
            date_of_birth=underage_dob,
            state_of_residence="TX"
        )

        assert result["success"] is False
        assert "18" in result["message"]

    def test_register_user_ineligible_state(self):
        """Register user should fail if state is ineligible."""
        from fittrack.services.auth_service import AuthService

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AuthService(db_session=mock_db)

        result = service.register_user(
            email="newuser@example.com",
            password="SecureP@ssw0rd123!",
            date_of_birth="1990-01-15",
            state_of_residence="NY"  # Ineligible state
        )

        assert result["success"] is False
        assert "not available" in result["message"].lower() or "ny" in result["message"].lower()


class TestUserLogin:
    """Test user login flow with credential validation."""

    def test_login_success(self):
        """Login should return tokens for valid credentials."""
        from fittrack.services.auth_service import AuthService
        from fittrack.security.authentication import hash_password

        # Mock user with hashed password
        mock_user = Mock()
        mock_user.user_id = str(uuid4())
        mock_user.email = "user@example.com"
        mock_user.password_hash = hash_password("SecureP@ssw0rd123!")
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.email_verified = True

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(db_session=mock_db)

        result = service.login(
            email="user@example.com",
            password="SecureP@ssw0rd123!"
        )

        assert result["success"] is True
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == "user@example.com"

    def test_login_wrong_password(self):
        """Login should fail with wrong password."""
        from fittrack.services.auth_service import AuthService
        from fittrack.security.authentication import hash_password

        mock_user = Mock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = hash_password("SecureP@ssw0rd123!")
        mock_user.status = "active"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(db_session=mock_db)

        result = service.login(
            email="user@example.com",
            password="WrongPassword123!"
        )

        assert result["success"] is False
        assert "invalid" in result["message"].lower()

    def test_login_user_not_found(self):
        """Login should fail if user doesn't exist."""
        from fittrack.services.auth_service import AuthService

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AuthService(db_session=mock_db)

        result = service.login(
            email="nonexistent@example.com",
            password="SecureP@ssw0rd123!"
        )

        assert result["success"] is False
        assert "invalid" in result["message"].lower()

    def test_login_suspended_account(self):
        """Login should fail if account is suspended."""
        from fittrack.services.auth_service import AuthService
        from fittrack.security.authentication import hash_password

        mock_user = Mock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = hash_password("SecureP@ssw0rd123!")
        mock_user.status = "suspended"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(db_session=mock_db)

        result = service.login(
            email="user@example.com",
            password="SecureP@ssw0rd123!"
        )

        assert result["success"] is False
        assert "suspended" in result["message"].lower()

    def test_login_unverified_email(self):
        """Login should fail if email is not verified."""
        from fittrack.services.auth_service import AuthService
        from fittrack.security.authentication import hash_password

        mock_user = Mock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = hash_password("SecureP@ssw0rd123!")
        mock_user.status = "pending"
        mock_user.email_verified = False

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(db_session=mock_db)

        result = service.login(
            email="user@example.com",
            password="SecureP@ssw0rd123!"
        )

        assert result["success"] is False
        assert "verify" in result["message"].lower() or "email" in result["message"].lower()


class TestTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_token_success(self):
        """Refresh should return new access token for valid refresh token."""
        from fittrack.services.auth_service import AuthService
        from fittrack.security.authentication import create_refresh_token

        user_id = uuid4()
        refresh_token = create_refresh_token(user_id=user_id)

        # Mock user
        mock_user = Mock()
        mock_user.user_id = str(user_id)
        mock_user.email = "user@example.com"
        mock_user.role = "user"
        mock_user.status = "active"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(db_session=mock_db)

        result = service.refresh_access_token(refresh_token)

        assert result["success"] is True
        assert "access_token" in result

    def test_refresh_token_invalid(self):
        """Refresh should fail with invalid token."""
        from fittrack.services.auth_service import AuthService

        mock_db = Mock()
        service = AuthService(db_session=mock_db)

        result = service.refresh_access_token("invalid.token.here")

        assert result["success"] is False
        assert "invalid" in result["message"].lower()

    def test_refresh_token_user_not_found(self):
        """Refresh should fail if user no longer exists."""
        from fittrack.services.auth_service import AuthService
        from fittrack.security.authentication import create_refresh_token

        user_id = uuid4()
        refresh_token = create_refresh_token(user_id=user_id)

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AuthService(db_session=mock_db)

        result = service.refresh_access_token(refresh_token)

        assert result["success"] is False
        assert "not found" in result["message"].lower() or "invalid" in result["message"].lower()
