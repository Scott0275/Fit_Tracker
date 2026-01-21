"""
Base model mixins for FitTrack application.

This module provides common functionality that can be mixed into ORM models:
- TimestampMixin: Automatic created_at and updated_at timestamps
- SoftDeleteMixin: Soft delete functionality with deleted_at timestamp
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    Automatically sets created_at when the record is created and updates
    updated_at whenever the record is modified.

    Attributes:
        created_at: Timestamp when the record was created (UTC)
        updated_at: Timestamp when the record was last updated (UTC)
    """

    @declared_attr
    def created_at(cls):
        """Timestamp when the record was created."""
        return Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
        )

    @declared_attr
    def updated_at(cls):
        """Timestamp when the record was last updated."""
        return Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality.

    Provides deleted_at timestamp column and methods for soft deleting
    and restoring records instead of actually removing them from the database.

    Attributes:
        deleted_at: Timestamp when the record was soft deleted (None if not deleted)

    Methods:
        soft_delete(): Mark the record as deleted
        restore(): Restore a soft-deleted record
        is_deleted: Property that returns True if the record is soft deleted
    """

    @declared_attr
    def deleted_at(cls):
        """Timestamp when the record was soft deleted (None if not deleted)."""
        return Column(DateTime(timezone=True), nullable=True, default=None)

    def soft_delete(self) -> None:
        """
        Mark this record as deleted by setting deleted_at timestamp.

        This does not remove the record from the database; it only marks it
        as deleted. Use with a query filter to exclude deleted records.

        Example:
            >>> user = db.query(User).first()
            >>> user.soft_delete()
            >>> db.commit()
        """
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """
        Restore a soft-deleted record by clearing the deleted_at timestamp.

        Example:
            >>> user = db.query(User).first()
            >>> user.restore()
            >>> db.commit()
        """
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """
        Check if this record has been soft deleted.

        Returns:
            bool: True if the record is soft deleted, False otherwise

        Example:
            >>> user = db.query(User).first()
            >>> if user.is_deleted:
            ...     print("User was deleted")
        """
        return self.deleted_at is not None
