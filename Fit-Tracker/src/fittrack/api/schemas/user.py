"""User API schemas for request and response models."""
from pydantic import BaseModel, Field
from typing import Optional


class UserResponse(BaseModel):
    """Response model for user profile."""

    user_id: str
    email: str
    status: str
    role: str
    email_verified: bool
    point_balance: int
    last_login_at: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "status": "active",
                "role": "user",
                "email_verified": True,
                "point_balance": 500,
                "last_login_at": "2026-01-14T10:30:00Z"
            }]
        }
    }


class UserUpdateRequest(BaseModel):
    """Request model for updating user profile (limited fields)."""

    # Users can only update certain fields
    # Most fields are managed by the system or admin
    pass  # For now, no user-editable fields in MVP


class PointBalanceResponse(BaseModel):
    """Response model for user point balance."""

    user_id: str
    point_balance: int
    last_updated: str

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "point_balance": 500,
                "last_updated": "2026-01-14T10:30:00Z"
            }]
        }
    }
