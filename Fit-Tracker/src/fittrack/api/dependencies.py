"""FastAPI dependencies for dependency injection.

This module provides common dependencies used across API endpoints:
- Database session management
- Current user extraction
- Authorization checks
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from fittrack.database import get_db as _get_db_generator
from fittrack.models.user import User
from fittrack.security.authorization import get_current_user as _get_current_user


# Re-export database dependency (it's already a generator)
get_db = _get_db_generator


# Re-export current user dependency
CurrentUser = Annotated[User, Depends(_get_current_user)]
