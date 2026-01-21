"""Authentication API schemas for request and response models."""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=12, description="User's password (min 12 characters)")
    date_of_birth: str = Field(..., description="Date of birth in ISO format (YYYY-MM-DD)")
    state_of_residence: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "password": "SecureP@ssw0rd123!",
                "date_of_birth": "1990-01-15",
                "state_of_residence": "TX"
            }]
        }
    }


class RegisterResponse(BaseModel):
    """Response model for user registration."""

    success: bool
    message: str
    user_id: str | None = None
    email: str | None = None


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "password": "SecureP@ssw0rd123!"
            }]
        }
    }


class UserInfo(BaseModel):
    """User information included in login response."""

    user_id: str
    email: str
    role: str
    point_balance: int


class LoginResponse(BaseModel):
    """Response model for user login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo


class RefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Valid refresh token")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
            }]
        }
    }


class RefreshResponse(BaseModel):
    """Response model for token refresh."""

    access_token: str
    token_type: str = "bearer"
