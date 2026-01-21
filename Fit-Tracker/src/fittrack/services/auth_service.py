"""Authentication service for user registration and login.

This module provides business logic for:
- User registration with validation (age, state eligibility)
- User login with credential verification
- Token management (access and refresh tokens)
"""
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from fittrack.models.user import User
from fittrack.security.authentication import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)


# Ineligible states per PRD (pending legal review)
INELIGIBLE_STATES = {"NY", "FL", "RI"}

# Minimum age requirement
MINIMUM_AGE = 18


class AuthService:
    """Authentication service for user management and login."""

    def __init__(self, db_session: Session):
        """Initialize auth service with database session.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def register_user(
        self,
        email: str,
        password: str,
        date_of_birth: str,
        state_of_residence: str
    ) -> dict[str, Any]:
        """Register a new user with validation.

        Validates:
        - Email uniqueness
        - Password strength (12+ chars, uppercase, lowercase, digit, special)
        - Age >= 18 years
        - State eligibility (not NY, FL, RI)

        Args:
            email: User's email address
            password: Plain text password
            date_of_birth: DOB in ISO format (YYYY-MM-DD)
            state_of_residence: Two-letter state code

        Returns:
            Dictionary with 'success' (bool), 'message' (str), and optional data

        Example:
            >>> service = AuthService(db_session)
            >>> result = service.register_user(
            ...     email="user@example.com",
            ...     password="SecureP@ssw0rd123!",
            ...     date_of_birth="1990-01-15",
            ...     state_of_residence="TX"
            ... )
            >>> result['success']
            True
        """
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            return {
                "success": False,
                "message": "Email address already exists"
            }

        # Validate password strength
        password_validation = validate_password_strength(password)
        if not password_validation["valid"]:
            return {
                "success": False,
                "message": password_validation["message"]
            }

        # Validate age (18+)
        dob = date.fromisoformat(date_of_birth)
        age = self._calculate_age(dob)
        if age < MINIMUM_AGE:
            return {
                "success": False,
                "message": f"You must be at least {MINIMUM_AGE} years old to register"
            }

        # Validate state eligibility
        if state_of_residence.upper() in INELIGIBLE_STATES:
            return {
                "success": False,
                "message": f"Registration is not available in {state_of_residence} at this time"
            }

        # Create user
        user = User(
            user_id=str(uuid4()),
            email=email,
            password_hash=hash_password(password),
            status="pending",
            role="user",
            email_verified=False,
            point_balance=0
        )

        self.db.add(user)
        # Note: Caller should commit the transaction

        return {
            "success": True,
            "message": "User registered successfully. Please verify your email.",
            "user_id": user.user_id,
            "email": user.email
        }

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user and return access and refresh tokens.

        Validates:
        - User exists
        - Password is correct
        - Email is verified
        - Account is active (not suspended/banned)

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            Dictionary with 'success' (bool), 'message' (str), and tokens if successful

        Example:
            >>> service = AuthService(db_session)
            >>> result = service.login(
            ...     email="user@example.com",
            ...     password="SecureP@ssw0rd123!"
            ... )
            >>> result['success']
            True
            >>> 'access_token' in result
            True
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            return {
                "success": False,
                "message": "Invalid email or password"
            }

        # Verify password
        if not verify_password(password, user.password_hash):
            return {
                "success": False,
                "message": "Invalid email or password"
            }

        # Check if email is verified
        if not user.email_verified:
            return {
                "success": False,
                "message": "Please verify your email address before logging in"
            }

        # Check account status
        if user.status == "suspended":
            return {
                "success": False,
                "message": "Your account has been suspended. Please contact support."
            }

        if user.status == "banned":
            return {
                "success": False,
                "message": "Your account has been banned."
            }

        if user.status != "active":
            return {
                "success": False,
                "message": "Your account is not active. Please verify your email."
            }

        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)

        # Generate tokens
        access_token = create_access_token(
            user_id=uuid4() if isinstance(user.user_id, str) else user.user_id,
            email=user.email,
            role=user.role
        )
        refresh_token = create_refresh_token(
            user_id=uuid4() if isinstance(user.user_id, str) else user.user_id
        )

        return {
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role,
                "point_balance": user.point_balance
            }
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary with 'success' (bool), 'message' (str), and new access_token

        Example:
            >>> service = AuthService(db_session)
            >>> result = service.refresh_access_token(refresh_token)
            >>> result['success']
            True
            >>> 'access_token' in result
            True
        """
        # Decode refresh token
        payload = decode_token(refresh_token)

        if payload is None:
            return {
                "success": False,
                "message": "Invalid or expired refresh token"
            }

        # Extract user_id from token
        user_id = payload.get("sub")

        if not user_id:
            return {
                "success": False,
                "message": "Invalid token payload"
            }

        # Find user
        user = self.db.query(User).filter(User.user_id == user_id).first()

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        # Check if user is still active
        if user.status != "active":
            return {
                "success": False,
                "message": "User account is not active"
            }

        # Generate new access token
        new_access_token = create_access_token(
            user_id=uuid4() if isinstance(user.user_id, str) else user.user_id,
            email=user.email,
            role=user.role
        )

        return {
            "success": True,
            "message": "Access token refreshed",
            "access_token": new_access_token
        }

    def _calculate_age(self, birth_date: date) -> int:
        """Calculate age from birth date.

        Args:
            birth_date: Date of birth

        Returns:
            Age in years

        Example:
            >>> from datetime import date
            >>> service = AuthService(None)
            >>> dob = date(1990, 1, 15)
            >>> service._calculate_age(dob) >= 18
            True
        """
        today = date.today()
        age = today.year - birth_date.year

        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age
