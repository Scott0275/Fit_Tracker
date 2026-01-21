"""
User model for FitTrack application.

This module defines the User entity for authentication and account management.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from fittrack.database import Base
from fittrack.models.base import SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    User model representing an authenticated account.

    This is the central entity for all user-scoped operations. Each user has
    credentials, role, point balance, and relationships to profile, activities,
    and sweepstakes entries.

    Attributes:
        user_id: UUID primary key
        email: Unique email address (login credential)
        password_hash: Bcrypt hash of password (cost factor 12)
        email_verified: Boolean flag (False=pending, True=verified)
        email_verified_at: Timestamp when email was verified
        status: Account status (pending, active, suspended, banned)
        role: User role (user, premium, admin)
        premium_expires_at: Premium subscription expiration timestamp
        point_balance: Current spendable points (>= 0)
        last_login_at: Most recent login timestamp

    Business Rules:
        - Email must be verified before profile completion
        - Status must be 'active' to participate in drawings
        - Point balance cannot go negative (CHECK constraint)
        - Premium role requires premium_expires_at in future
        - Admin role bypasses eligibility restrictions

    State Transitions:
        - pending → active: Email verification completed
        - active → suspended: Admin action (ToS violation)
        - suspended → active: Admin review/appeal accepted
        - active → banned: Severe violation (permanent)
    """

    __tablename__ = "users"

    # Primary key (UUID)
    user_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Account status and role
    status = Column(
        String(20),
        CheckConstraint(
            "status IN ('pending', 'active', 'suspended', 'banned')",
            name="valid_user_status",
        ),
        default="pending",
        nullable=False,
    )
    role = Column(
        String(20),
        CheckConstraint(
            "role IN ('user', 'premium', 'admin')", name="valid_user_role"
        ),
        default="user",
        nullable=False,
    )

    # Premium subscription
    premium_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Points system
    point_balance = Column(
        Integer,
        CheckConstraint("point_balance >= 0", name="non_negative_points"),
        default=0,
        nullable=False,
    )

    # Activity tracking
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships (to be added when other models are implemented)
    # profile = relationship("Profile", back_populates="user", uselist=False)
    # tracker_connections = relationship("TrackerConnection", back_populates="user")
    # activities = relationship("Activity", back_populates="user")
    # point_transactions = relationship("PointTransaction", back_populates="user")
    # tickets = relationship("Ticket", back_populates="user")

    def verify_email(self) -> None:
        """
        Verify the user's email address.

        Sets email_verified to True, records verification timestamp,
        and updates account status to 'active'.

        Example:
            >>> user = db.query(User).filter_by(email="user@example.com").first()
            >>> user.verify_email()
            >>> db.commit()
        """
        self.email_verified = True
        self.email_verified_at = datetime.now(timezone.utc)
        if self.status == "pending":
            self.status = "active"

    @property
    def is_active(self) -> bool:
        """
        Check if the user account is active.

        Returns:
            bool: True if status is 'active', False otherwise

        Example:
            >>> if user.is_active:
            ...     print("User can access platform features")
        """
        return self.status == "active"

    @property
    def is_premium(self) -> bool:
        """
        Check if the user has an active premium subscription.

        A user is considered premium if:
        1. Their role is 'premium', AND
        2. premium_expires_at is in the future

        Returns:
            bool: True if premium subscription is active, False otherwise

        Example:
            >>> if user.is_premium:
            ...     print("User can access premium features")
        """
        if self.role != "premium":
            return False

        if self.premium_expires_at is None:
            return False

        # Ensure premium_expires_at is timezone-aware for comparison
        expires_at = (
            self.premium_expires_at.replace(tzinfo=timezone.utc)
            if self.premium_expires_at.tzinfo is None
            else self.premium_expires_at
        )

        return expires_at > datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """
        Return string representation of User.

        Returns:
            str: String representation showing email and status

        Example:
            >>> user = User(email="user@example.com", status="active")
            >>> print(user)
            <User(email='user@example.com', status='active')>
        """
        return f"<User(email='{self.email}', status='{self.status}')>"
