"""Unit tests for authorization decorators and RBAC.

Following strict TDD - tests written FIRST.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from fastapi import HTTPException


class TestGetCurrentUser:
    """Test get_current_user dependency for extracting user from JWT."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Get current user should return user for valid token."""
        from fittrack.security.authorization import get_current_user
        from fittrack.security.authentication import create_access_token

        # Create valid token
        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user"
        )

        # Mock credentials object
        mock_credentials = Mock()
        mock_credentials.credentials = token

        # Mock database and user
        mock_user = Mock()
        mock_user.user_id = str(user_id)
        mock_user.email = "user@example.com"
        mock_user.role = "user"
        mock_user.status = "active"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Call dependency
        result = await get_current_user(credentials=mock_credentials, db=mock_db)

        assert result.user_id == str(user_id)
        assert result.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Get current user should raise 401 for invalid token."""
        from fittrack.security.authorization import get_current_user

        mock_credentials = Mock()
        mock_credentials.credentials = "invalid.token.here"

        mock_db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials, db=mock_db)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower() or "credentials" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Get current user should raise 401 if user no longer exists."""
        from fittrack.security.authorization import get_current_user
        from fittrack.security.authentication import create_access_token

        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user"
        )

        mock_credentials = Mock()
        mock_credentials.credentials = token

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials, db=mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_account(self):
        """Get current user should raise 403 if account is not active."""
        from fittrack.security.authorization import get_current_user
        from fittrack.security.authentication import create_access_token

        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user"
        )

        mock_credentials = Mock()
        mock_credentials.credentials = token

        mock_user = Mock()
        mock_user.user_id = str(user_id)
        mock_user.status = "suspended"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials, db=mock_db)

        assert exc_info.value.status_code == 403
        assert "suspended" in exc_info.value.detail.lower() or "inactive" in exc_info.value.detail.lower()


class TestRequireRole:
    """Test require_role decorator for role-based access control."""

    @pytest.mark.asyncio
    async def test_require_role_user_has_role(self):
        """Require role should allow access if user has required role."""
        from fittrack.security.authorization import require_role

        # Mock user with 'admin' role
        mock_user = Mock()
        mock_user.role = "admin"

        # Create dependency function
        check_admin = require_role("admin")

        # Should not raise exception
        result = await check_admin(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_role_user_lacks_role(self):
        """Require role should raise 403 if user lacks required role."""
        from fittrack.security.authorization import require_role

        # Mock user with 'user' role
        mock_user = Mock()
        mock_user.role = "user"

        # Create dependency function requiring 'admin'
        check_admin = require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await check_admin(current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "permission" in exc_info.value.detail.lower() or "forbidden" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_role_multiple_allowed_roles(self):
        """Require role should allow access if user has any of the allowed roles."""
        from fittrack.security.authorization import require_role

        # Mock user with 'premium' role
        mock_user = Mock()
        mock_user.role = "premium"

        # Create dependency function allowing 'premium' or 'admin'
        check_privileged = require_role("premium", "admin")

        result = await check_privileged(current_user=mock_user)
        assert result == mock_user


class TestGetCurrentAdmin:
    """Test get_current_admin dependency for admin-only access."""

    @pytest.mark.asyncio
    async def test_get_current_admin_is_admin(self):
        """Get current admin should return user if role is admin."""
        from fittrack.security.authorization import get_current_admin

        mock_user = Mock()
        mock_user.role = "admin"

        result = await get_current_admin(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_admin_is_not_admin(self):
        """Get current admin should raise 403 if user is not admin."""
        from fittrack.security.authorization import get_current_admin

        mock_user = Mock()
        mock_user.role = "user"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(current_user=mock_user)

        assert exc_info.value.status_code == 403
