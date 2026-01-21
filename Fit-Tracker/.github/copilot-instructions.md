# FitTrack AI Copilot Instructions

## Project Overview

**FitTrack** is a gamified fitness platform that rewards users with sweepstakes entries for physical activity. Users connect fitness trackers (Apple Health, Google Fit, Fitbit via Terra API), earn tier-adjusted points for activities, compete on demographic leaderboards, and enter daily/weekly/monthly/annual prize drawings.

**Architecture Pattern**: Layered modular monolith (Python 3.12+, FastAPI, SQLAlchemy, Oracle 26ai, Celery/Redis)

## Critical Architecture Concepts

### Layered Architecture
- **API Layer** (`src/fittrack/api/routes/v1/`): FastAPI routers with request/response schemas
- **Service Layer** (`src/fittrack/services/`): Business logic, workflows, domain rules (e.g., `AuthService`, point calculation, tier assignment)
- **Data Layer** (`src/fittrack/database/models/`, `src/fittrack/database/repositories/`): SQLAlchemy ORM models with mixins (TimestampMixin, SoftDeleteMixin), repository pattern CRUD
- **Integration Layer**: Terra API client for fitness tracker aggregation
- **Worker Layer**: Celery async tasks for 15-minute polling sync, leaderboard recalculation, drawing execution

### Oracle 26ai JSON Tables Strategy
- **Primary approach**: Use JSON columns for flexible/nested data (activity metrics, user goals, eligibility rules)
- **Hybrid columns**: JSON for nested data + traditional columns for frequently queried/indexed fields
- **JSON indexing**: Functional indexes on JSON paths using `JSON_VALUE()` for performance
- **Duality Views**: Expose JSON document-style API over relational tables (not yet implemented, future enhancement)
- **Pool configuration**: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=3600` in `database.py`

### Database Model Patterns
**All models must inherit from mixins**:
- `TimestampMixin`: Auto-sets `created_at` (UTC), `updated_at` (UTC, on_update)
- `SoftDeleteMixin`: Soft deletes via `deleted_at` timestamp; use `.soft_delete()` and `.restore()` methods
- Primary keys: `UUID` (RAW(16) in Oracle) for distributed compatibility
- All timestamps: `TIMESTAMP WITH TIME ZONE`, stored as UTC

**Example**: [User model](src/fittrack/models/user.py) inherits both mixins, soft deletes are standard practice

### Key Business Rules
- **Tier Assignment**: Based on age, sex, and fitness level; determines point earning multipliers (beginner 1.2x, intermediate 1.0x, advanced 0.9x)
- **Ineligible States**: NY, FL, RI (defined in `AuthService.INELIGIBLE_STATES`)
- **Minimum Age**: 18 years (enforced in registration, `AuthService.MINIMUM_AGE`)
- **Password Strength**: 12+ chars, uppercase, lowercase, digit, special char (validated in `validate_password_strength()`)
- **Activity Sync**: 15-minute polling interval (Celery worker, not yet implemented)

## Development Workflows

### Database Migrations
```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Descriptive message"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```
Migrations stored in `migrations/versions/`. Always test rollback (`alembic downgrade -1 && alembic upgrade head`)

### Testing Patterns
- **Test location**: Mirror source structure (e.g., service test at `tests/unit/services/test_auth_service.py`)
- **Fixtures**: Use `conftest.py` (session, function-scoped DB fixtures with rollback)
- **Database**: SQLite in-memory for unit/integration tests, rollback after each test
- **Mocking**: Use `pytest-mock` for external APIs (Terra, email, etc.)
- **Parametrization**: Use `@pytest.mark.parametrize` for multiple scenarios

Example test command: `pytest tests/ -v --cov=src/fittrack`

### Security Implementation
- **Password Hashing**: Use `hash_password()` (bcrypt, 12 rounds) from `security.authentication`
- **JWT Tokens**: Use `create_access_token()` and `create_refresh_token()` (RS256 with keys in `keys/` directory)
- **Token Expiry**: Access 30 min, Refresh 7 days
- **Endpoint Protection**: FastAPI `Depends(get_current_user)` dependency (not yet in auth.py, needs implementation)
- **Oracle TDE**: All PII encrypted at rest (OCI requirement, managed by Oracle)

## Code Patterns & Conventions

### Service Layer Pattern
```python
class EntityService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def operation(self, **params) -> dict[str, Any]:
        """Return {'success': bool, 'message': str, ...data}"""
        # validation
        # business logic
        # db operations (don't commit; let caller handle)
        return {"success": True, "message": "...", "id": "..."}
```
Services validate, orchestrate, return status dicts. **Controllers (routes) commit transactions**. See [AuthService](src/fittrack/services/auth_service.py).

### API Route Pattern
```python
@router.post("/endpoint", response_model=ResponseSchema)
async def endpoint_handler(request: RequestSchema, db: Session = Depends(get_db)):
    service = EntityService(db_session=db)
    result = service.operation(...)
    
    if not result["success"]:
        raise HTTPException(status_code=..., detail=result["message"])
    
    db.commit()  # Route commits, not service
    return ResponseSchema(**result)
```
Routes use dependency injection for DB session, handle HTTP status codes, manage transactions. See [auth.py routes](src/fittrack/api/routes/v1/auth.py).

### Error Handling
- Service methods return `{"success": False, "message": "..."}` for validation/business logic errors
- Routes translate to appropriate HTTP status codes (409 conflict, 422 unprocessable, 400 bad request, 401 unauthorized, 403 forbidden)
- No naked exceptions in services; use status dicts for control flow

### Pydantic Schemas
Stored in `src/fittrack/api/schemas/`. Create separate request/response classes:
```python
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: UUID
    email: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # For ORM mapping
```

## Key Files Reference

| File | Purpose |
|------|---------|
| [main.py](src/fittrack/main.py) | FastAPI app factory, CORS setup, lifespan events |
| [database.py](src/fittrack/database.py) | SQLAlchemy engine, session factory, config |
| [models/base.py](src/fittrack/models/base.py) | TimestampMixin, SoftDeleteMixin |
| [models/user.py](src/fittrack/models/user.py) | User, Profile ORM models |
| [api/dependencies.py](src/fittrack/api/dependencies.py) | `get_db`, `get_current_user` (TODO) dependencies |
| [api/routes/v1/auth.py](src/fittrack/api/routes/v1/auth.py) | Register, login endpoints |
| [services/auth_service.py](src/fittrack/services/auth_service.py) | Business logic for registration, login, token generation |
| [security/authentication.py](src/fittrack/security/authentication.py) | Password hashing, JWT operations |
| [conftest.py](tests/conftest.py) | Pytest fixtures (DB session, test client) |

## Common Tasks & Commands

### Running the Application
```bash
# Development with hot reload
uvicorn src.fittrack.main:app --reload --host 0.0.0.0 --port 8000

# With environment variables
export FITTRACK_DATABASE_URL="oracle://user:pass@host/db"
python -m uvicorn src.fittrack.main:app --reload
```

### Health Checks (once running)
- `GET /health` → `{"status": "ok", "service": "fittrack"}`
- `GET /health/ready` → Checks DB connectivity, returns 503 if down
- `GET /` → API info with links to docs

### Adding New Models
1. Create model class in `src/fittrack/models/{entity}.py`, inherit `TimestampMixin`, `SoftDeleteMixin`
2. Use UUID primary key, UTC timestamps
3. Import in `models/__init__.py`
4. Create migration: `alembic revision --autogenerate -m "Add {entity} table"`
5. Create repository in `src/fittrack/database/repositories/{entity}_repository.py` (future)

### Adding New API Endpoint
1. Create schema in `src/fittrack/api/schemas/{entity}.py`
2. Create route in `src/fittrack/api/routes/v1/{endpoint}.py`
3. Add service method in `src/fittrack/services/{entity}_service.py`
4. Include router in [main.py](src/fittrack/main.py): `app.include_router(router)`
5. Test with `pytest tests/integration/api/`

## Implementation Status & Gaps

**Completed (Checkpoint 1+)**:
- ✅ FastAPI app factory with lifespan, CORS
- ✅ SQLAlchemy setup with Oracle driver, connection pooling
- ✅ User model with TimestampMixin, SoftDeleteMixin
- ✅ Password hashing (bcrypt), JWT token creation
- ✅ Auth endpoints (register, login)
- ✅ Basic test fixtures

**TODO (Checkpoint 2+)**:
- ⚠️ Email verification workflow (needs Celery + email service)
- ⚠️ `get_current_user` dependency for protected endpoints (JWT validation)
- ⚠️ RBAC middleware (role-based access control)
- ⚠️ Repository pattern full implementation (currently embedded in services)
- ⚠️ Alembic migrations (models exist, migrations not created)
- ⚠️ Activity model with JSON metrics column
- ⚠️ Point calculation service with tier adjustments
- ⚠️ Leaderboard queries with caching (Redis)
- ⚠️ Drawing engine with CSPRNG winner selection
- ⚠️ Terra API integration and 15-min sync worker
- ⚠️ Comprehensive error handling and logging
- ⚠️ API documentation (auto-generated by FastAPI at `/docs`)

## Testing & Debugging Tips

- Run single test: `pytest tests/unit/test_user_model.py::test_name -v`
- Enable SQL logging: Set `echo=True` in DatabaseConfig
- Inspect JWT claims: Use JWT debugger at jwt.io or decode in Python with public key
- Test with curl: `curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"email":"...","password":"...",...}'`
- Mock external APIs in tests: Use `monkeypatch` fixture to replace service methods

## Key Decisions & Rationale

1. **Monolith vs Microservices**: Monolith for MVP speed. Future extraction candidates: sync worker, drawing engine (clear boundaries exist)
2. **Oracle JSON Tables**: Trade-off between flexibility (JSON) and relational integrity (structured columns). Functional indexes on JSON paths for performance
3. **Terra API**: Single integration point vs native app development (3-week savings justified)
4. **Batch Sync (15-min)**: Balances UX with API rate limits (~$0.10/user/month cost)
5. **Soft Deletes**: Audit trail preservation and potential user data recovery
6. **JWT RS256**: Asymmetric signing allows token verification without key sharing (important for distributed systems)

## When Stuck

- **Model changes**: Always generate migration, test rollback
- **Database errors**: Check pool config, connection timeouts, Oracle JSON syntax
- **Auth issues**: Verify JWT keys exist in `keys/`, check token expiry times
- **Service logic**: Services return status dicts, routes map to HTTP codes
- **Tests failing**: Ensure DB rollback between tests, check fixtures in conftest.py
- **Missing dependencies**: Check `pyproject.toml`, run `pip install -e ".[dev]"` after updates
