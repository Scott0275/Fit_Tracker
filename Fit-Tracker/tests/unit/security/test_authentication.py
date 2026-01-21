"""Unit tests for authentication utilities (password hashing, JWT).

Following strict TDD - tests written FIRST.
"""
import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4


class TestPasswordHashing:
    """Test password hashing and verification with bcrypt."""

    def test_hash_password_returns_string(self):
        """Hash password should return a bcrypt hash string."""
        from fittrack.security.authentication import hash_password

        password = "SecureP@ssw0rd123!"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt identifier

    def test_hash_password_different_salts(self):
        """Same password should produce different hashes (different salts)."""
        from fittrack.security.authentication import hash_password

        password = "SecureP@ssw0rd123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Verify password should return True for correct password."""
        from fittrack.security.authentication import hash_password, verify_password

        password = "SecureP@ssw0rd123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify password should return False for incorrect password."""
        from fittrack.security.authentication import hash_password, verify_password

        password = "SecureP@ssw0rd123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_empty_string(self):
        """Hash password should handle empty string."""
        from fittrack.security.authentication import hash_password

        password = ""
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_password_strength_validation_too_short(self):
        """Password validation should reject passwords < 12 characters."""
        from fittrack.security.authentication import validate_password_strength

        result = validate_password_strength("Short1!")

        assert result["valid"] is False
        assert "at least 12 characters" in result["message"].lower()

    def test_password_strength_validation_missing_uppercase(self):
        """Password validation should require uppercase letter."""
        from fittrack.security.authentication import validate_password_strength

        result = validate_password_strength("nouppercase1!")

        assert result["valid"] is False
        assert "uppercase" in result["message"].lower()

    def test_password_strength_validation_missing_lowercase(self):
        """Password validation should require lowercase letter."""
        from fittrack.security.authentication import validate_password_strength

        result = validate_password_strength("NOLOWERCASE1!")

        assert result["valid"] is False
        assert "lowercase" in result["message"].lower()

    def test_password_strength_validation_missing_digit(self):
        """Password validation should require digit."""
        from fittrack.security.authentication import validate_password_strength

        result = validate_password_strength("NoDigitsHere!")

        assert result["valid"] is False
        assert "digit" in result["message"].lower()

    def test_password_strength_validation_missing_special(self):
        """Password validation should require special character."""
        from fittrack.security.authentication import validate_password_strength

        result = validate_password_strength("NoSpecial123")

        assert result["valid"] is False
        assert "special" in result["message"].lower()

    def test_password_strength_validation_valid(self):
        """Password validation should accept strong password."""
        from fittrack.security.authentication import validate_password_strength

        result = validate_password_strength("SecureP@ssw0rd123!")

        assert result["valid"] is True
        assert result["message"] == "Password is strong"


class TestJWTOperations:
    """Test JWT creation and validation with RS256."""

    def test_create_access_token_returns_string(self):
        """Create access token should return JWT string."""
        from fittrack.security.authentication import create_access_token

        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user"
        )

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_create_access_token_with_custom_expiration(self):
        """Create access token should accept custom expiration."""
        from fittrack.security.authentication import create_access_token

        user_id = uuid4()
        expires_delta = timedelta(minutes=10)

        token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user",
            expires_delta=expires_delta
        )

        assert isinstance(token, str)

    def test_decode_token_valid(self):
        """Decode token should return payload for valid token."""
        from fittrack.security.authentication import create_access_token, decode_token

        user_id = uuid4()
        email = "user@example.com"
        role = "user"

        token = create_access_token(user_id=user_id, email=email, role=role)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["role"] == role
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_token_expired(self):
        """Decode token should return None for expired token."""
        from fittrack.security.authentication import create_access_token, decode_token

        user_id = uuid4()
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)

        token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user",
            expires_delta=expires_delta
        )

        payload = decode_token(token)
        assert payload is None

    def test_decode_token_invalid_signature(self):
        """Decode token should return None for invalid signature."""
        from fittrack.security.authentication import decode_token

        # Malformed JWT
        invalid_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"

        payload = decode_token(invalid_token)
        assert payload is None

    def test_decode_token_malformed(self):
        """Decode token should return None for malformed token."""
        from fittrack.security.authentication import decode_token

        invalid_token = "not.a.valid.jwt"

        payload = decode_token(invalid_token)
        assert payload is None

    def test_create_refresh_token_returns_string(self):
        """Create refresh token should return JWT string."""
        from fittrack.security.authentication import create_refresh_token

        user_id = uuid4()
        token = create_refresh_token(user_id=user_id)

        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_refresh_token_has_longer_expiration(self):
        """Refresh token should have longer expiration than access token."""
        from fittrack.security.authentication import (
            create_access_token,
            create_refresh_token,
            decode_token
        )

        user_id = uuid4()

        access_token = create_access_token(
            user_id=user_id,
            email="user@example.com",
            role="user"
        )
        refresh_token = create_refresh_token(user_id=user_id)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert refresh_payload["exp"] > access_payload["exp"]
