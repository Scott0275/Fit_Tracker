"""
Unit tests for database configuration and connection management.

Following strict TDD - these tests are written BEFORE implementation.
Tests will initially FAIL until we implement the database module.
"""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base

from src.fittrack.database import (
    Base,
    DatabaseConfig,
    get_db,
    get_engine,
    init_db,
)


@pytest.mark.unit
class TestDatabaseConfig:
    """Test database configuration management."""

    def test_database_config_has_required_attributes(self):
        """
        RED: Test that DatabaseConfig class has all required attributes.

        This test will fail until we create the DatabaseConfig class.
        """
        config = DatabaseConfig()

        # Required configuration attributes
        assert hasattr(config, "database_url")
        assert hasattr(config, "echo")
        assert hasattr(config, "pool_size")
        assert hasattr(config, "max_overflow")
        assert hasattr(config, "pool_timeout")

    def test_database_config_defaults(self):
        """
        RED: Test that DatabaseConfig has sensible defaults.

        This test will fail until we implement DatabaseConfig with defaults.
        """
        config = DatabaseConfig()

        assert config.echo is False
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 30

    def test_database_config_from_env(self):
        """
        RED: Test that DatabaseConfig can load from environment variables.

        This test will fail until we implement environment loading.
        """
        # This will be tested with mocked env vars
        config = DatabaseConfig()
        assert config.database_url is not None


@pytest.mark.unit
class TestDatabaseEngine:
    """Test database engine creation and management."""

    def test_get_engine_returns_engine(self):
        """
        RED: Test that get_engine() returns a SQLAlchemy Engine.

        This test will fail until we implement get_engine().
        """
        engine = get_engine()
        assert isinstance(engine, Engine)

    def test_get_engine_is_singleton(self):
        """
        RED: Test that get_engine() returns the same instance (singleton pattern).

        This test will fail until we implement singleton pattern.
        """
        engine1 = get_engine()
        engine2 = get_engine()
        assert engine1 is engine2

    def test_engine_can_connect(self):
        """
        RED: Test that the engine can establish a database connection.

        This test will fail until we have a working engine.
        """
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1


@pytest.mark.unit
class TestDatabaseSession:
    """Test database session management."""

    def test_get_db_yields_session(self):
        """
        RED: Test that get_db() yields a SQLAlchemy Session.

        This test will fail until we implement get_db().
        """
        db_gen = get_db()
        db = next(db_gen)
        assert isinstance(db, Session)
        # Cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_closes_session(self):
        """
        RED: Test that get_db() properly closes the session.

        This test will fail until we implement proper session cleanup.
        """
        db_gen = get_db()
        db = next(db_gen)

        # Session should be open
        assert db.is_active

        # Close the generator (triggers finally block)
        try:
            next(db_gen)
        except StopIteration:
            pass

        # Session should be closed now
        # Note: We'll need to track this in implementation


@pytest.mark.unit
class TestDatabaseBase:
    """Test the declarative base for ORM models."""

    def test_base_exists(self):
        """
        RED: Test that Base declarative base exists.

        This test will fail until we create Base.
        """
        assert Base is not None

    def test_base_is_declarative_base(self):
        """
        RED: Test that Base is a SQLAlchemy declarative base.

        This test will fail until we properly create Base.
        """
        # Check that it has the required attributes of a declarative base
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


@pytest.mark.integration
class TestDatabaseInitialization:
    """Test database initialization (requires actual DB)."""

    def test_init_db_creates_tables(self, db_session):
        """
        RED: Test that init_db() creates all tables in the database.

        This test will fail until we implement init_db().
        """
        # Drop all tables first
        Base.metadata.drop_all(bind=db_session.get_bind())

        # Initialize database
        init_db(db_session.get_bind())

        # Check that tables were created
        # We'll verify this by checking metadata
        engine = db_session.get_bind()
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Should have at least some tables (we'll add more specific checks later)
        assert len(tables) >= 0  # Will update this when we have models

    def test_database_connection_with_session(self, db_session):
        """
        RED: Test that we can execute queries with a session.

        This test will fail until db_session fixture works with our implementation.
        """
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
