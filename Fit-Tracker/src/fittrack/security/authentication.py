"""Authentication utilities: password hashing and JWT operations.

This module provides:
- Password hashing with bcrypt (cost factor 12)
- Password strength validation
- JWT creation and validation with RS256 signing
- Access and refresh token management
"""
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt


# Configuration
BCRYPT_ROUNDS = 12
JWT_ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Load RSA keys from files
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_PRIVATE_KEY_PATH = _PROJECT_ROOT / "keys" / "jwt_private_key.pem"
_PUBLIC_KEY_PATH = _PROJECT_ROOT / "keys" / "jwt_public_key.pem"

# Read keys at module load time
with open(_PRIVATE_KEY_PATH, "rb") as f:
    _PRIVATE_KEY = f.read()

with open(_PUBLIC_KEY_PATH, "rb") as f:
    _PUBLIC_KEY = f.read()


# Password Hashing Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hash string (starts with $2b$)

    Example:
        >>> hashed = hash_password("SecureP@ssw0rd123!")
        >>> hashed.startswith("$2b$")
        True
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to check against

    Returns:
        True if password matches hash, False otherwise

    Example:
        >>> hashed = hash_password("SecureP@ssw0rd123!")
        >>> verify_password("SecureP@ssw0rd123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def validate_password_strength(password: str) -> dict[str, Any]:
    """Validate password meets strength requirements.

    Requirements:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Dictionary with 'valid' (bool) and 'message' (str) keys

    Example:
        >>> result = validate_password_strength("SecureP@ssw0rd123!")
        >>> result['valid']
        True
        >>> result = validate_password_strength("weak")
        >>> result['valid']
        False
    """
    if len(password) < 12:
        return {
            "valid": False,
            "message": "Password must be at least 12 characters long"
        }

    if not re.search(r"[A-Z]", password):
        return {
            "valid": False,
            "message": "Password must contain at least one uppercase letter"
        }

    if not re.search(r"[a-z]", password):
        return {
            "valid": False,
            "message": "Password must contain at least one lowercase letter"
        }

    if not re.search(r"\d", password):
        return {
            "valid": False,
            "message": "Password must contain at least one digit"
        }

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return {
            "valid": False,
            "message": "Password must contain at least one special character"
        }

    return {
        "valid": True,
        "message": "Password is strong"
    }


# JWT Functions
def create_access_token(
    user_id: UUID,
    email: str,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token with RS256 signing.

    Args:
        user_id: User's UUID
        email: User's email address
        role: User's role (user, premium, admin)
        expires_delta: Optional custom expiration time (default: 30 minutes)

    Returns:
        JWT token string

    Example:
        >>> from uuid import uuid4
        >>> token = create_access_token(
        ...     user_id=uuid4(),
        ...     email="user@example.com",
        ...     role="user"
        ... )
        >>> len(token) > 0
        True
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "role": role,
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at
    }

    token = jwt.encode(payload, _PRIVATE_KEY, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: UUID) -> str:
    """Create a JWT refresh token with RS256 signing.

    Refresh tokens have longer expiration (7 days) and contain minimal data.

    Args:
        user_id: User's UUID

    Returns:
        JWT refresh token string

    Example:
        >>> from uuid import uuid4
        >>> token = create_refresh_token(user_id=uuid4())
        >>> len(token) > 0
        True
    """
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(payload, _PRIVATE_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Token payload dictionary if valid, None otherwise

    Example:
        >>> from uuid import uuid4
        >>> user_id = uuid4()
        >>> token = create_access_token(
        ...     user_id=user_id,
        ...     email="user@example.com",
        ...     role="user"
        ... )
        >>> payload = decode_token(token)
        >>> payload is not None
        True
        >>> payload['sub'] == str(user_id)
        True
    """
    try:
        payload = jwt.decode(token, _PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
