"""
Database configuration and connection management for FitTrack.

This module provides database engine creation, session management,
and the declarative base for ORM models.
"""

import os
from typing import Generator

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


class DatabaseConfig(BaseSettings):
    """
    Database configuration loaded from environment variables.

    Attributes:
        database_url: SQLAlchemy database URL
        echo: Whether to log SQL statements
        pool_size: Number of connections to keep in the pool
        max_overflow: Maximum number of connections to create beyond pool_size
        pool_timeout: Timeout in seconds before giving up on getting a connection
    """

    database_url: str = "sqlite:///./fittrack.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
_config = DatabaseConfig()

# Declarative base for ORM models
Base = declarative_base()

# Global engine instance (singleton)
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Get the SQLAlchemy database engine (singleton pattern).

    Returns:
        Engine: SQLAlchemy Engine instance

    Example:
        >>> engine = get_engine()
        >>> with engine.connect() as conn:
        ...     result = conn.execute(text("SELECT 1"))
    """
    global _engine

    if _engine is None:
        # Create engine based on configuration
        _engine = create_engine(
            _config.database_url,
            echo=_config.echo,
            pool_size=_config.pool_size,
            max_overflow=_config.max_overflow,
            pool_timeout=_config.pool_timeout,
        )

    return _engine


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection.

    Yields a database session and ensures it's closed after use.
    This is designed to be used with FastAPI's Depends().

    Yields:
        Session: SQLAlchemy Session instance

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/users")
        >>> def get_users(db: Session = Depends(get_db)):
        ...     return db.query(User).all()
    """
    engine = get_engine()

    # Bind the session factory to the engine
    SessionLocal.configure(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine: Engine | None = None) -> None:
    """
    Initialize the database by creating all tables.

    Args:
        engine: SQLAlchemy Engine instance. If None, uses the default engine.

    Example:
        >>> init_db()  # Creates all tables defined in Base metadata
    """
    if engine is None:
        engine = get_engine()

    # Import all models here to ensure they're registered with Base
    # This will be populated as we create models
    # from src.fittrack.models import user, activity, etc.

    Base.metadata.create_all(bind=engine)
