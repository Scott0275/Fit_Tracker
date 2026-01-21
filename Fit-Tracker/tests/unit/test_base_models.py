"""
Unit tests for base model mixins.

Following strict TDD - these tests are written BEFORE implementation.
Tests will initially FAIL until we implement the base model mixins.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session

from src.fittrack.database import Base
from src.fittrack.models.base import SoftDeleteMixin, TimestampMixin


# Test models to verify mixin functionality
class TimestampModel(Base, TimestampMixin):
    """Sample model using TimestampMixin for testing."""

    __tablename__ = "timestamp_model"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class SoftDeleteModel(Base, SoftDeleteMixin):
    """Sample model using SoftDeleteMixin for testing."""

    __tablename__ = "soft_delete_model"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class CombinedModel(Base, TimestampMixin, SoftDeleteMixin):
    """Sample model using both mixins for testing."""

    __tablename__ = "combined_model"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


@pytest.mark.unit
class TestTimestampMixin:
    """Test TimestampMixin functionality."""

    def test_timestamp_mixin_has_required_columns(self):
        """
        RED: Test that TimestampMixin adds created_at and updated_at columns.

        This test will fail until we implement TimestampMixin.
        """
        model = TimestampModel()

        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

    def test_created_at_set_on_creation(self, db_session: Session):
        """
        RED: Test that created_at is automatically set when model is created.

        This test will fail until we implement auto-timestamp functionality.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        before_create = datetime.now(timezone.utc)
        model = TimestampModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)
        after_create = datetime.now(timezone.utc)

        # Check that created_at is set
        assert model.created_at is not None
        # Convert to aware datetime if needed for comparison (SQLite returns naive datetimes)
        created_at = (
            model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at
        )
        assert before_create <= created_at <= after_create

    def test_updated_at_set_on_creation(self, db_session: Session):
        """
        RED: Test that updated_at is automatically set when model is created.

        This test will fail until we implement auto-timestamp functionality.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        before_create = datetime.now(timezone.utc)
        model = TimestampModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)
        after_create = datetime.now(timezone.utc)

        # Check that updated_at is set
        assert model.updated_at is not None
        # Convert to aware datetime if needed for comparison (SQLite returns naive datetimes)
        updated_at = (
            model.updated_at.replace(tzinfo=timezone.utc)
            if model.updated_at.tzinfo is None
            else model.updated_at
        )
        assert before_create <= updated_at <= after_create

    def test_updated_at_changes_on_update(self, db_session: Session):
        """
        RED: Test that updated_at is automatically updated when model is modified.

        This test will fail until we implement auto-update functionality.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        model = TimestampModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        original_updated_at = model.updated_at

        # Wait a moment to ensure timestamp difference
        import time

        time.sleep(0.1)

        # Update the model
        model.name = "updated"
        db_session.commit()
        db_session.refresh(model)

        # Check that updated_at changed
        assert model.updated_at > original_updated_at

    def test_created_at_does_not_change_on_update(self, db_session: Session):
        """
        RED: Test that created_at remains unchanged when model is updated.

        This test will fail until we implement proper timestamp handling.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        model = TimestampModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        original_created_at = model.created_at

        # Update the model
        model.name = "updated"
        db_session.commit()
        db_session.refresh(model)

        # Check that created_at did NOT change
        assert model.created_at == original_created_at


@pytest.mark.unit
class TestSoftDeleteMixin:
    """Test SoftDeleteMixin functionality."""

    def test_soft_delete_mixin_has_required_columns(self):
        """
        RED: Test that SoftDeleteMixin adds deleted_at column.

        This test will fail until we implement SoftDeleteMixin.
        """
        model = SoftDeleteModel()

        assert hasattr(model, "deleted_at")

    def test_deleted_at_is_none_by_default(self, db_session: Session):
        """
        RED: Test that deleted_at is None for non-deleted records.

        This test will fail until we implement SoftDeleteMixin.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        model = SoftDeleteModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        # Check that deleted_at is None
        assert model.deleted_at is None

    def test_soft_delete_mixin_has_soft_delete_method(self):
        """
        RED: Test that SoftDeleteMixin provides a soft_delete() method.

        This test will fail until we implement soft_delete().
        """
        model = SoftDeleteModel()

        assert hasattr(model, "soft_delete")
        assert callable(model.soft_delete)

    def test_soft_delete_sets_deleted_at(self, db_session: Session):
        """
        RED: Test that soft_delete() sets the deleted_at timestamp.

        This test will fail until we implement soft_delete().
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        model = SoftDeleteModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        # Soft delete the model
        before_delete = datetime.now(timezone.utc)
        model.soft_delete()
        db_session.commit()
        db_session.refresh(model)
        after_delete = datetime.now(timezone.utc)

        # Check that deleted_at is set
        assert model.deleted_at is not None
        # Convert to aware datetime if needed for comparison (SQLite returns naive datetimes)
        deleted_at = (
            model.deleted_at.replace(tzinfo=timezone.utc)
            if model.deleted_at.tzinfo is None
            else model.deleted_at
        )
        assert before_delete <= deleted_at <= after_delete

    def test_soft_delete_mixin_has_is_deleted_property(self):
        """
        RED: Test that SoftDeleteMixin provides an is_deleted property.

        This test will fail until we implement is_deleted.
        """
        model = SoftDeleteModel()

        assert hasattr(model, "is_deleted")

    def test_is_deleted_returns_false_for_non_deleted(self, db_session: Session):
        """
        RED: Test that is_deleted returns False for non-deleted records.

        This test will fail until we implement is_deleted.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        model = SoftDeleteModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        # Check that is_deleted is False
        assert model.is_deleted is False

    def test_is_deleted_returns_true_after_soft_delete(self, db_session: Session):
        """
        RED: Test that is_deleted returns True after soft deletion.

        This test will fail until we implement is_deleted.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a new model instance
        model = SoftDeleteModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        # Soft delete the model
        model.soft_delete()
        db_session.commit()
        db_session.refresh(model)

        # Check that is_deleted is True
        assert model.is_deleted is True

    def test_soft_delete_mixin_has_restore_method(self):
        """
        RED: Test that SoftDeleteMixin provides a restore() method.

        This test will fail until we implement restore().
        """
        model = SoftDeleteModel()

        assert hasattr(model, "restore")
        assert callable(model.restore)

    def test_restore_clears_deleted_at(self, db_session: Session):
        """
        RED: Test that restore() clears the deleted_at timestamp.

        This test will fail until we implement restore().
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create and soft delete a model
        model = SoftDeleteModel(name="test")
        db_session.add(model)
        db_session.commit()
        model.soft_delete()
        db_session.commit()
        db_session.refresh(model)

        # Restore the model
        model.restore()
        db_session.commit()
        db_session.refresh(model)

        # Check that deleted_at is None
        assert model.deleted_at is None
        assert model.is_deleted is False


@pytest.mark.unit
class TestCombinedMixins:
    """Test using both TimestampMixin and SoftDeleteMixin together."""

    def test_combined_model_has_all_columns(self):
        """
        RED: Test that a model can use both mixins together.

        This test will fail until we implement both mixins.
        """
        model = CombinedModel()

        # From TimestampMixin
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

        # From SoftDeleteMixin
        assert hasattr(model, "deleted_at")
        assert hasattr(model, "soft_delete")
        assert hasattr(model, "is_deleted")
        assert hasattr(model, "restore")

    def test_timestamps_work_with_soft_delete(self, db_session: Session):
        """
        RED: Test that timestamps still work correctly with soft delete.

        This test will fail until we implement both mixins properly.
        """
        # Create all test tables
        Base.metadata.create_all(bind=db_session.get_bind())

        # Create a model
        model = CombinedModel(name="test")
        db_session.add(model)
        db_session.commit()
        db_session.refresh(model)

        original_created_at = model.created_at
        original_updated_at = model.updated_at

        # Soft delete should update updated_at but not created_at
        import time

        time.sleep(0.1)

        model.soft_delete()
        db_session.commit()
        db_session.refresh(model)

        assert model.created_at == original_created_at
        assert model.updated_at > original_updated_at
        assert model.is_deleted is True
