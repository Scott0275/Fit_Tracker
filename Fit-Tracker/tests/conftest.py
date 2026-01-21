"""
Pytest configuration and shared fixtures for all tests.

This module provides test fixtures for database sessions, test client,
and factory configurations following strict TDD principles.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import will be created later - placeholder for now
# from src.fittrack.database import Base, get_db
# from src.fittrack.main import app


# Test database URL - using SQLite for fast unit tests
TEST_DATABASE_URL = "sqlite:///./test.db"
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the event loop for the test session.

    This fixture ensures async tests can run properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def engine():
    """
    Create a test database engine.

    Uses SQLite in-memory database for fast test execution.
    Each test function gets a fresh database.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    # Base.metadata.create_all(bind=engine)  # Uncomment when Base is available

    yield engine

    # Drop all tables after test
    # Base.metadata.drop_all(bind=engine)  # Uncomment when Base is available
    engine.dispose()


@pytest.fixture(scope="function")
async def async_engine():
    """
    Create an async test database engine.

    Uses SQLite in-memory database for fast async test execution.
    """
    engine = create_async_engine(
        TEST_ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """
    Create a test database session.

    Each test function gets its own session that is rolled back
    after the test completes to ensure test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def async_db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async test database session.

    Each test function gets its own async session that is rolled back
    after the test completes to ensure test isolation.
    """
    async with async_engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection, expire_on_commit=False)

            yield session

            await session.close()
            await transaction.rollback()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with overridden database session.

    This fixture allows tests to make HTTP requests to the API
    with a test database session.
    """
    # Override the get_db dependency to use test session
    # def override_get_db():
    #     try:
    #         yield db_session
    #     finally:
    #         pass

    # app.dependency_overrides[get_db] = override_get_db

    # with TestClient(app) as test_client:
    #     yield test_client

    # app.dependency_overrides.clear()

    # Placeholder until app is created
    pass


@pytest.fixture(autouse=True)
def reset_db_state(db_session):
    """
    Automatically reset database state between tests.

    This fixture runs before each test to ensure clean state.
    """
    yield
    # Additional cleanup if needed


# Factory Boy configuration fixtures
@pytest.fixture(scope="function")
def factory_session(db_session):
    """
    Configure factory_boy to use the test database session.

    This allows factories to create test data in the test database.
    """
    # from tests.factories import set_session
    # set_session(db_session)
    return db_session


# Markers for test categorization (already defined in pyproject.toml)
# - @pytest.mark.unit: Fast, isolated unit tests
# - @pytest.mark.integration: Tests requiring database
# - @pytest.mark.e2e: Full stack end-to-end tests
# - @pytest.mark.slow: Long-running tests
