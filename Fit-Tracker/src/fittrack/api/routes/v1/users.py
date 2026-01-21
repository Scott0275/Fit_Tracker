"""User API endpoints - all require authentication.

This module provides HTTP endpoints for user profile management:
- GET /api/v1/users/me - Get current user profile
- PUT /api/v1/users/me - Update current user profile
- GET /api/v1/users/me/points - Get current user point balance

All endpoints require valid JWT authentication token.
"""
from fastapi import APIRouter, Depends, status

from fittrack.api.dependencies import CurrentUser
from fittrack.api.schemas.user import (
    PointBalanceResponse,
    UserResponse,
    UserUpdateRequest,
)
from fittrack.models.user import User


router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: CurrentUser
):
    """Get current authenticated user's profile.

    Requires valid JWT token in Authorization header.

    Returns:
        UserResponse: User profile data

    Raises:
        HTTPException: 401 if token is invalid or missing
        HTTPException: 403 if user account is not active

    Example:
        >>> headers = {"Authorization": "Bearer <access_token>"}
        >>> response = client.get("/api/v1/users/me", headers=headers)
        >>> response.status_code
        200
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        status=current_user.status,
        role=current_user.role,
        email_verified=current_user.email_verified,
        point_balance=current_user.point_balance,
        last_login_at=str(current_user.last_login_at) if current_user.last_login_at else None
    )


@router.put("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    request: UserUpdateRequest,
    current_user: CurrentUser
):
    """Update current authenticated user's profile.

    Requires valid JWT token in Authorization header.
    Only certain fields can be updated by users (most are system-managed).

    Args:
        request: Update request (currently no editable fields in MVP)
        current_user: Authenticated user from JWT token

    Returns:
        UserResponse: Updated user profile data

    Raises:
        HTTPException: 401 if token is invalid or missing
        HTTPException: 403 if user account is not active

    Note:
        In MVP, most user fields are system-managed. This endpoint
        is prepared for future user-editable fields (e.g., preferences).
    """
    # For now, just return the current user data
    # In future, update specific fields based on request
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        status=current_user.status,
        role=current_user.role,
        email_verified=current_user.email_verified,
        point_balance=current_user.point_balance,
        last_login_at=str(current_user.last_login_at) if current_user.last_login_at else None
    )


@router.get("/me/points", response_model=PointBalanceResponse, status_code=status.HTTP_200_OK)
async def get_current_user_points(
    current_user: CurrentUser
):
    """Get current authenticated user's point balance.

    Requires valid JWT token in Authorization header.

    Returns:
        PointBalanceResponse: Current point balance

    Raises:
        HTTPException: 401 if token is invalid or missing
        HTTPException: 403 if user account is not active

    Example:
        >>> headers = {"Authorization": "Bearer <access_token>"}
        >>> response = client.get("/api/v1/users/me/points", headers=headers)
        >>> response.json()
        {"user_id": "...", "point_balance": 500, "last_updated": "..."}
    """
    return PointBalanceResponse(
        user_id=current_user.user_id,
        point_balance=current_user.point_balance,
        last_updated=str(current_user.updated_at)
    )
