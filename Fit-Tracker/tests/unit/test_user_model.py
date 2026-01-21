"""
Unit tests for User model.

Following strict TDD - these tests are written BEFORE implementation.
Tests will initially FAIL until we implement the User model.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.fittrack.database import Base
from src.fittrack.models.user import User


@pytest.mark.unit
class TestUserModel:
    """Test User model structure and constraints."""

    def test_user_model_exists(self):
        """
        RED: Test that User model is importable and exists.

        This test will fail until we create the User model.
        """
        assert User is not None

    def test_user_has_required_columns(self):
        """
        RED: Test that User model has all required columns.

        This test will fail until we implement all required columns.
        """
        user = User()

        # Required attributes
        assert hasattr(user, "user_id")
        assert hasattr(user, "email")
        assert hasattr(user, "password_hash")
        assert hasattr(user, "email_verified")
        assert hasattr(user, "email_verified_at")
        assert hasattr(user, "status")
        assert hasattr(user, "role")
        assert hasattr(user, "premium_expires_at")
        assert hasattr(user, "point_balance")
        assert hasattr(user, "last_login_at")

        # From mixins
        assert hasattr(user, "created_at")
        assert hasattr(user, "updated_at")
        assert hasattr(user, "deleted_at")

    def test_user_table_name(self):
        """
        RED: Test that User model has correct table name.

        This test will fail until we set __tablename__.
        """
        assert User.__tablename__ == "users"

    def test_user_id_is_primary_key(self, db_session: Session):
        """
        RED: Test that user_id is the primary key.

        This test will fail until we configure user_id as PK.
        """
        Base.metadata.create_all(bind=db_session.get_bind())
        inspector = inspect(db_session.get_bind())
        pk_columns = inspector.get_pk_constraint("users")["constrained_columns"]

        assert "user_id" in pk_columns

    def test_email_is_unique(self, db_session: Session):
        """
        RED: Test that email has UNIQUE constraint.

        This test will fail until we add UNIQUE constraint to email.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create first user
        user1 = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="user",
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create duplicate email - should fail
        user2 = User(
            email="test@example.com",
            password_hash="hash456",
            status="pending",
            role="user",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_is_required(self, db_session: Session):
        """
        RED: Test that email is NOT NULL.

        This test will fail until we set email as NOT NULL.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(password_hash="hash123", status="pending", role="user")
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_password_hash_is_required(self, db_session: Session):
        """
        RED: Test that password_hash is NOT NULL.

        This test will fail until we set password_hash as NOT NULL.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(email="test@example.com", status="pending", role="user")
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.unit
class TestUserDefaults:
    """Test User model default values."""

    def test_email_verified_defaults_to_false(self, db_session: Session):
        """
        RED: Test that email_verified defaults to False (0).

        This test will fail until we set the default.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="user",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.email_verified is False

    def test_status_defaults_to_pending(self, db_session: Session):
        """
        RED: Test that status defaults to 'pending'.

        This test will fail until we set the default.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(email="test@example.com", password_hash="hash123", role="user")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.status == "pending"

    def test_role_defaults_to_user(self, db_session: Session):
        """
        RED: Test that role defaults to 'user'.

        This test will fail until we set the default.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com", password_hash="hash123", status="pending"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role == "user"

    def test_point_balance_defaults_to_zero(self, db_session: Session):
        """
        RED: Test that point_balance defaults to 0.

        This test will fail until we set the default.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="user",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.point_balance == 0


@pytest.mark.unit
class TestUserValidation:
    """Test User model validation and constraints."""

    def test_status_must_be_valid_value(self, db_session: Session):
        """
        RED: Test that status must be one of: pending, active, suspended, banned.

        This test will fail until we add CHECK constraint.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="invalid_status",
            role="user",
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_role_must_be_valid_value(self, db_session: Session):
        """
        RED: Test that role must be one of: user, premium, admin.

        This test will fail until we add CHECK constraint.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="invalid_role",
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_point_balance_cannot_be_negative(self, db_session: Session):
        """
        RED: Test that point_balance cannot be negative.

        This test will fail until we add CHECK constraint.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="user",
            point_balance=-10,
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.unit
class TestUserMethods:
    """Test User model methods."""

    def test_user_has_verify_email_method(self):
        """
        RED: Test that User has verify_email() method.

        This test will fail until we implement the method.
        """
        user = User()
        assert hasattr(user, "verify_email")
        assert callable(user.verify_email)

    def test_verify_email_sets_email_verified_true(self, db_session: Session):
        """
        RED: Test that verify_email() sets email_verified to True.

        This test will fail until we implement verify_email().
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        # Verify email
        user.verify_email()
        db_session.commit()
        db_session.refresh(user)

        assert user.email_verified is True
        assert user.email_verified_at is not None

    def test_verify_email_updates_status_to_active(self, db_session: Session):
        """
        RED: Test that verify_email() updates status to 'active'.

        This test will fail until we implement status change in verify_email().
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="pending",
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        user.verify_email()
        db_session.commit()
        db_session.refresh(user)

        assert user.status == "active"

    def test_user_has_is_active_property(self):
        """
        RED: Test that User has is_active property.

        This test will fail until we implement is_active.
        """
        user = User()
        assert hasattr(user, "is_active")

    def test_is_active_returns_true_for_active_status(self, db_session: Session):
        """
        RED: Test that is_active returns True when status is 'active'.

        This test will fail until we implement is_active property.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="active",
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_active is True

    def test_is_active_returns_false_for_non_active_status(self, db_session: Session):
        """
        RED: Test that is_active returns False when status is not 'active'.

        This test will fail until we implement is_active property.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="suspended",
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_active is False

    def test_user_has_is_premium_property(self):
        """
        RED: Test that User has is_premium property.

        This test will fail until we implement is_premium.
        """
        user = User()
        assert hasattr(user, "is_premium")

    def test_is_premium_returns_true_for_premium_role_with_valid_expiration(
        self, db_session: Session
    ):
        """
        RED: Test that is_premium returns True for premium role with future expiration.

        This test will fail until we implement is_premium property.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="active",
            role="premium",
            premium_expires_at=future_date,
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_premium is True

    def test_is_premium_returns_false_for_expired_premium(self, db_session: Session):
        """
        RED: Test that is_premium returns False for expired premium subscription.

        This test will fail until we implement is_premium property.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="active",
            role="premium",
            premium_expires_at=past_date,
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_premium is False

    def test_is_premium_returns_false_for_non_premium_role(
        self, db_session: Session
    ):
        """
        RED: Test that is_premium returns False for non-premium roles.

        This test will fail until we implement is_premium property.
        """
        Base.metadata.create_all(bind=db_session.get_bind())

        user = User(
            email="test@example.com",
            password_hash="hash123",
            status="active",
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_premium is False


@pytest.mark.unit
class TestUserRepresentation:
    """Test User model string representation."""

    def test_user_has_repr(self):
        """
        RED: Test that User has __repr__ method.

        This test will fail until we implement __repr__.
        """
        user = User(email="test@example.com")
        repr_string = repr(user)

        assert "User" in repr_string
        assert "test@example.com" in repr_string
