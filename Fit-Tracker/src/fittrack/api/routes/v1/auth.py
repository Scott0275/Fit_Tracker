"""Authentication API endpoints.

This module provides HTTP endpoints for user authentication:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login with credentials
- POST /api/v1/auth/refresh - Refresh access token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from fittrack.api.dependencies import get_db
from fittrack.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    UserInfo,
)
from fittrack.services.auth_service import AuthService


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user account.

    Validates:
    - Email uniqueness
    - Password strength (12+ chars, uppercase, lowercase, digit, special)
    - Age >= 18 years
    - State eligibility (not NY, FL, RI)

    Returns:
        RegisterResponse: Registration result with user ID if successful

    Raises:
        HTTPException: 409 if email already exists
        HTTPException: 422 if password is weak
        HTTPException: 400 if user is underage or state is ineligible
    """
    auth_service = AuthService(db_session=db)

    result = auth_service.register_user(
        email=request.email,
        password=request.password,
        date_of_birth=request.date_of_birth,
        state_of_residence=request.state_of_residence
    )

    if not result["success"]:
        # Determine appropriate status code based on error
        if "already exists" in result["message"].lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result["message"]
            )
        elif "password" in result["message"].lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    # Commit the transaction
    db.commit()

    return RegisterResponse(**result)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access and refresh tokens.

    Validates:
    - User exists
    - Password is correct
    - Email is verified
    - Account is active (not suspended/banned)

    Returns:
        LoginResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: 401 if credentials are invalid or user not found
        HTTPException: 403 if email not verified or account suspended
    """
    auth_service = AuthService(db_session=db)

    result = auth_service.login(
        email=request.email,
        password=request.password
    )

    if not result["success"]:
        # Determine appropriate status code based on error
        if "invalid" in result["message"].lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["message"],
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["message"]
            )

    # Commit transaction (updates last_login_at)
    db.commit()

    # Convert user dict to UserInfo model
    user_info = UserInfo(**result["user"])

    return LoginResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=user_info
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """Generate new access token from refresh token.

    Returns:
        RefreshResponse: New access token

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    auth_service = AuthService(db_session=db)

    result = auth_service.refresh_access_token(request.refresh_token)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"}
        )

    return RefreshResponse(access_token=result["access_token"])
