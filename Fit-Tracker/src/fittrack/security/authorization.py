"""Authorization utilities for role-based access control (RBAC).

This module provides:
- FastAPI dependencies for extracting and validating users from JWT tokens
- Role-based access control decorators
- Admin-only access dependencies
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from fittrack.models.user import User
from fittrack.security.authentication import decode_token


# Security scheme for Bearer token
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Session
) -> User:
    """FastAPI dependency to extract and validate current user from JWT token.

    Validates:
    - Token is valid and not expired
    - User exists in database
    - User account is active

    Args:
        credentials: HTTP Bearer token credentials from request header
        db: Database session

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found
        HTTPException: 403 if user account is not active

    Example:
        >>> from fastapi import APIRouter, Depends
        >>> router = APIRouter()
        >>>
        >>> @router.get("/profile")
        >>> async def get_profile(current_user: User = Depends(get_current_user)):
        ...     return {"email": current_user.email}
    """
    # Extract token from credentials
    token = credentials.credentials

    # Decode and validate token
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status}. Please contact support.",
        )

    return user


def require_role(*allowed_roles: str):
    """Create a dependency that requires user to have one of the specified roles.

    Args:
        *allowed_roles: Variable number of role strings (e.g., "admin", "premium")

    Returns:
        FastAPI dependency function

    Example:
        >>> from fastapi import APIRouter, Depends
        >>> router = APIRouter()
        >>>
        >>> @router.get("/admin/users")
        >>> async def list_users(user: User = Depends(require_role("admin"))):
        ...     return {"users": [...]}
        >>>
        >>> @router.get("/premium/content")
        >>> async def premium_content(
        ...     user: User = Depends(require_role("premium", "admin"))
        ... ):
        ...     return {"content": "..."}
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has required role."""
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """FastAPI dependency for admin-only endpoints.

    Convenience wrapper around require_role("admin").

    Args:
        current_user: Current authenticated user

    Returns:
        User object if user is admin

    Raises:
        HTTPException: 403 if user is not admin

    Example:
        >>> from fastapi import APIRouter, Depends
        >>> router = APIRouter()
        >>>
        >>> @router.post("/admin/drawings")
        >>> async def create_drawing(admin: User = Depends(get_current_admin)):
        ...     return {"message": "Drawing created"}
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
