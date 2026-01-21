# Implementation Plan: FitTrack

## Executive Summary

FitTrack is a gamified fitness platform that rewards users with sweepstakes entries for physical activity. This implementation plan delivers a production-ready MVP in **6 checkpoints over approximately 20 weeks** (including Checkpoint 1's 16 days).

**Project Scope**: Web-based application for US users (18+) in eligible states, integrating with fitness trackers via Terra API, awarding tier-adjusted points for activities, enabling competition on demographic-bracketed leaderboards, and facilitating sweepstakes drawings with prize fulfillment.

**Key Technical Decisions**:
- **Architecture**: Layered modular monolith (Python/FastAPI/Oracle 26ai)
- **Fitness Integration**: Terra API aggregator (Apple Health, Google Fit, Fitbit)
- **Competition Model**: Demographic tiers (age/sex/fitness level) + OPEN tier opt-in
- **Point System**: Tier-adjusted rates (beginner 1.2x, intermediate 1.0x, advanced 0.9x)
- **Authentication**: Email/password only (social login deferred to v1.1)

**Major Risks and Mitigations**:
- **Risk**: Terra API single point of failure → **Mitigation**: Monitoring, error handling, user notifications for sync failures
- **Risk**: Sweepstakes legal compliance → **Mitigation**: Legal review of rules, conservative state selection, audit trails
- **Risk**: Manual prize fulfillment doesn't scale → **Mitigation**: MVP targets < 100 fulfillments/month, automation at scale trigger

## Architecture Overview

**System Architecture Pattern**: Layered Modular Monolith
- Single deployable FastAPI application
- Clear module boundaries: API → Services → Repositories → Database
- Background workers (Celery) for async tasks (sync, leaderboards, drawings)
- Redis for caching (leaderboards, sessions) and message brokering

**Technology Stack Rationale**:
- **Oracle 26ai Free + JSON Duality Views**: Combines document flexibility with relational integrity, free tier sufficient for MVP
- **Terra API**: Unified fitness tracker integration (no native iOS app needed), ~$0.10/user/month cost justified by 3-week dev time savings
- **FastAPI**: High performance, automatic OpenAPI docs, native async support
- **Tier-adjusted points**: Fairer competition across demographics, better engagement

**Security Architecture**:
- JWT (RS256) authentication with 30-min access tokens, 7-day refresh tokens
- Bcrypt password hashing (cost factor 12)
- AES-256-GCM encryption for OAuth tokens at rest
- CSPRNG for drawing winner selection (audit trail stored)
- All PII encrypted at rest (Oracle TDE), in transit (TLS 1.3)

**Integration Patterns**:
- Terra API: Polling every 15 minutes, exponential backoff on errors
- Email notifications: Async via Celery, queued for batch delivery
- Drawing execution: Scheduled cron job, idempotent (checks completed_at)

## Checkpoint Overview

| Checkpoint | Title | Duration | Dependencies | Key Deliverables |
|------------|-------|----------|--------------|-------------------|
| 1 | Foundation: Test Environment & Data Layer | 16 days | None | Full stack running, data layer with JSON Tables, synthetic data, test page, CRUD APIs for all entities |
| 2 | Authentication & Authorization | 8 days | CP1 | User registration, login, JWT tokens, RBAC middleware, email verification |
| 3 | Fitness Tracker Integration | 10 days | CP1, CP2 | Terra API OAuth flows, activity sync worker, point calculation with tier adjustments |
| 4 | Competition & Leaderboards | 8 days | CP1, CP2, CP3 | Tier assignment, leaderboard queries/caching, rankings display |
| 5 | Sweepstakes Engine | 12 days | CP1, CP2, CP4 | Drawing CRUD, ticket purchase, winner selection (CSPRNG), prize fulfillment workflow |
| 6 | Production Readiness | 10 days | CP1-5 | Logging, monitoring, error tracking, load testing, deployment automation, documentation |

**Total Estimated Duration**: ~20 weeks (accounting for testing, integration, and buffer)

---

## Checkpoint 1: Foundation - Test Environment & Data Layer

### Objective

Establish the complete development and testing infrastructure with a fully functional data layer built on Oracle 26ai with JSON Tables. This checkpoint enables all subsequent development by providing a working database, synthetic data generation, and a reporting API with HTML test page to verify data integrity.

### Prerequisites

- [x] Docker installed and running
- [x] Python 3.12+ available
- [x] Git repository initialized
- [x] Oracle Container Registry access (for Oracle 26ai Free image)

### Deliverables

#### Infrastructure Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Docker Compose | `docker/docker-compose.yml` | Oracle 26ai + Redis + app + worker containers |
| Dockerfile (dev) | `docker/Dockerfile.dev` | Development container with hot reload (Uvicorn --reload) |
| Dockerfile (prod) | `docker/Dockerfile` | Production container (Gunicorn + Uvicorn workers) |
| Makefile | `Makefile` | All development commands (setup, test, db-*, run, etc.) |
| Environment template | `.env.example` | All required environment variables with descriptions |
| Setup script | `scripts/setup_dev.sh` | One-command environment setup (creates venv, installs deps, etc.) |
| GitHub Actions CI | `.github/workflows/ci.yml` | Test pipeline skeleton (lint, test, security scan) |
| Pre-commit hooks | `.pre-commit-config.yaml` | Ruff, mypy, detect-secrets |

#### Data Layer Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Database connection | `src/fittrack/database/connection.py` | SQLAlchemy engine, session factory, FastAPI dependency |
| Base model | `src/fittrack/database/models/base.py` | Declarative base, TimestampMixin, SoftDeleteMixin, VersionMixin |
| User model | `src/fittrack/database/models/user.py` | User table with constraints |
| Profile model | `src/fittrack/database/models/user.py` | Profile table with tier_code logic |
| TrackerConnection model | `src/fittrack/database/models/tracker.py` | OAuth connection storage with encrypted tokens |
| Activity model | `src/fittrack/database/models/activity.py` | Activity table with JSON metrics column |
| PointTransaction model | `src/fittrack/database/models/points.py` | Immutable audit log |
| Drawing model | `src/fittrack/database/models/drawing.py` | Drawing configuration with JSON eligibility |
| Prize model | `src/fittrack/database/models/drawing.py` | Prize details |
| Ticket model | `src/fittrack/database/models/ticket.py` | Sweepstakes entries |
| PrizeFulfillment model | `src/fittrack/database/models/fulfillment.py` | Prize delivery workflow with JSON shipping address |
| Sponsor model | `src/fittrack/database/models/sponsor.py` | Prize sponsors |
| Base repository | `src/fittrack/database/repositories/base.py` | Generic CRUD interface with type hints |
| User repository | `src/fittrack/database/repositories/user_repository.py` | User-specific queries |
| Activity repository | `src/fittrack/database/repositories/activity_repository.py` | Activity queries with date filters |
| Points repository | `src/fittrack/database/repositories/points_repository.py` | Transaction creation, balance queries |
| Drawing repository | `src/fittrack/database/repositories/drawing_repository.py` | Drawing CRUD, status filters |
| Ticket repository | `src/fittrack/database/repositories/ticket_repository.py` | Ticket creation, winner queries |
| Leaderboard repository | `src/fittrack/database/repositories/leaderboard_repository.py` | Aggregation queries for rankings |
| Fulfillment repository | `src/fittrack/database/repositories/fulfillment_repository.py` | Fulfillment status management |
| Initial migration | `migrations/versions/001_initial_schema.py` | Complete schema with all tables, indexes, constraints |

#### Synthetic Data Generation Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Base factory | `tests/factories/base.py` | Common factory configuration, Faker seeding |
| User factory | `tests/factories/user_factory.py` | User records with bcrypt passwords |
| Profile factory | `tests/factories/profile_factory.py` | Profiles with calculated tier codes |
| Activity factory | `tests/factories/activity_factory.py` | Activities with realistic metrics JSON |
| Drawing factory | `tests/factories/drawing_factory.py` | Drawings with eligibility JSON |
| Ticket factory | `tests/factories/ticket_factory.py` | Tickets with point transactions |
| Seed script | `scripts/seed_data.py` | CLI tool for generating configurable test data |
| Seed data scenarios | `scripts/seed_data.py` | Functions for each workflow (registration, sync, purchase, drawing) |

**Required Synthetic Data Scenarios** (generated by `make db-seed`):
- 10 users per role (user, premium, admin) across all 30 tiers + OPEN tier
- 5 active tracker connections per tracker type (Apple Health, Google Fit, Fitbit)
- 200+ activities across users with varied types (steps, workouts, active minutes)
- 50+ point transactions (earn, spend, adjust types)
- 5 drawings (1 daily, 1 weekly, 1 monthly, 1 annual, 1 past completed)
- 100+ tickets distributed across drawings
- 3 completed drawings with winners and fulfillments
- 10 sponsors (including "FitTrack Platform" for gift cards)
- Referential integrity maintained (all FKs valid)

#### API Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| App entry point | `src/fittrack/main.py` | FastAPI app factory, CORS, middleware, lifespan events |
| Configuration | `src/fittrack/config.py` | Pydantic Settings with validation |
| Exceptions | `src/fittrack/exceptions.py` | Custom exception hierarchy |
| Health routes | `src/fittrack/api/routes/health.py` | `/health`, `/health/ready` (DB ping) |
| Common schemas | `src/fittrack/api/schemas/common.py` | PaginationParams, ErrorResponse, SuccessResponse |
| User schemas | `src/fittrack/api/schemas/user.py` | UserResponse, UserListResponse |
| Activity schemas | `src/fittrack/api/schemas/activity.py` | ActivityResponse, ActivityListResponse |
| Drawing schemas | `src/fittrack/api/schemas/drawing.py` | DrawingResponse, DrawingListResponse |
| Points schemas | `src/fittrack/api/schemas/points.py` | PointTransactionResponse, BalanceResponse |
| User routes | `src/fittrack/api/routes/v1/users.py` | CRUD endpoints for users |
| Activity routes | `src/fittrack/api/routes/v1/activities.py` | List/get activities |
| Drawing routes | `src/fittrack/api/routes/v1/drawings.py` | List/get drawings |
| Points routes | `src/fittrack/api/routes/v1/points.py` | List transactions, get balance |
| Report routes | `src/fittrack/api/routes/v1/reports.py` | `/reports/summary` (system metrics) |
| Dependencies | `src/fittrack/api/dependencies.py` | `get_db_session` dependency |

**Required API Endpoints** (for EACH core entity):

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Basic health check | No |
| GET | `/health/ready` | Readiness check (DB ping) | No |
| GET | `/api/v1/users` | List users with pagination | No (later: Yes) |
| GET | `/api/v1/users/{id}` | Get single user | No (later: Yes) |
| POST | `/api/v1/users` | Create user | No (later: Admin) |
| PUT | `/api/v1/users/{id}` | Update user | No (later: Yes) |
| DELETE | `/api/v1/users/{id}` | Delete user (soft delete) | No (later: Admin) |
| GET | `/api/v1/activities` | List activities with filters | No (later: Yes) |
| GET | `/api/v1/activities/{id}` | Get activity details | No (later: Yes) |
| GET | `/api/v1/drawings` | List drawings with filters | No (later: Yes) |
| GET | `/api/v1/drawings/{id}` | Get drawing details | No (later: Yes) |
| POST | `/api/v1/drawings` | Create drawing | No (later: Admin) |
| PUT | `/api/v1/drawings/{id}` | Update drawing | No (later: Admin) |
| GET | `/api/v1/points/transactions` | List point transactions | No (later: Yes) |
| GET | `/api/v1/reports/summary` | System-wide data summary | No |

#### HTML Test Page Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Test page entry | `static/test/index.html` | Main test interface with tabbed navigation |
| API tester | `static/test/js/api-tester.js` | Interactive endpoint testing with forms |
| Leaderboard viewer | `static/test/js/leaderboard-viewer.js` | Sample leaderboard display (mocked data) |
| Report viewer | `static/test/js/report-viewer.js` | System metrics and data integrity reports |
| Sample data controls | `static/test/js/sample-data.js` | Buttons to seed/reset database via API |
| Styles | `static/test/css/test-page.css` | Clean, responsive styling |

**HTML Test Page Requirements**:

1. **API Endpoint Tester Tab**:
   - Dropdown to select entity (Users, Activities, Drawings, Points)
   - Forms for each CRUD operation (List, Get by ID, Create, Update, Delete)
   - Request/response display with JSON syntax highlighting (use Prism.js)
   - HTTP status code and response time display
   - Pagination controls for list endpoints
   - Filter/sort parameter inputs

2. **Leaderboard Viewer Tab**:
   - Display sample leaderboards (daily, weekly, monthly, all-time)
   - Tier filter dropdown (all 30 tiers + OPEN)
   - Rankings table with rank, display name, points, tier
   - Pagination for browsing beyond top 10
   - Mock data initially (real data in Checkpoint 4)

3. **Report Viewer Tab**:
   - System summary cards (total users, activities, drawings, tickets)
   - Entity breakdown table (counts per entity type)
   - Data integrity checks (orphaned records, invalid FKs)
   - Workflow status visualization (registrations, syncs, purchases, drawings)

4. **Sample Data Controls Tab**:
   - "Seed Database" button → calls `POST /api/v1/admin/seed` endpoint
   - "Reset Database" button → calls `POST /api/v1/admin/reset` endpoint
   - Display seed statistics after completion (counts per entity)
   - Success/error notifications

5. **Technical Requirements**:
   - Pure HTML/CSS/JavaScript (no build step)
   - Fetch API for all backend calls
   - Responsive design (desktop + tablet)
   - Served at `/test/` endpoint (FastAPI static files)
   - Disabled in production via `FEATURE_HTML_TEST_PAGE=false`

#### Test Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Test configuration | `tests/conftest.py` | Fixtures (test DB, session, factories) |
| Repository tests | `tests/integration/repositories/test_user_repository.py` | Test CRUD operations for User |
| Repository tests | `tests/integration/repositories/test_activity_repository.py` | Test activity queries with filters |
| Repository tests | `tests/integration/repositories/test_leaderboard_queries.py` | Test aggregation queries |
| API tests | `tests/integration/api/test_health_endpoints.py` | Test health checks |
| API tests | `tests/integration/api/test_user_endpoints.py` | Test user CRUD endpoints |
| API tests | `tests/integration/api/test_activity_endpoints.py` | Test activity endpoints |
| API tests | `tests/integration/api/test_drawing_endpoints.py` | Test drawing endpoints |
| Factory tests | `tests/unit/factories/test_factories.py` | Verify factories produce valid data |

**Coverage Requirements**:
- Database models: >95%
- Repositories: >90%
- API endpoints: >85%
- Overall Checkpoint 1: >85%

#### Documentation Deliverables

| Document | Description |
|----------|-------------|
| README.md | Complete setup instructions (< 15 min from fresh clone) |
| CLAUDE.md | Full project context (already created) |
| ADR-001 | Why layered monolith architecture |
| ADR-002 | Why Oracle JSON Tables for flexible data |
| ADR-003 | Why Terra API for fitness integration |
| ADR-004 | Why tier-based point scaling for fair competition |
| Data model diagram | ERD in Mermaid format (`docs/diagrams/data-model.mmd`) |

### Acceptance Criteria

```gherkin
Feature: Development Environment Setup

  Scenario: Fresh clone setup completes in under 15 minutes
    Given a developer has cloned the repository
    And Docker is installed and running
    And Python 3.12+ is installed
    When they run `make setup && make dev`
    Then Oracle 26ai container starts successfully within 3 minutes
    And Redis container starts successfully within 30 seconds
    And the application container starts successfully within 1 minute
    And database migrations complete without error within 2 minutes
    And the application is accessible at http://localhost:8000
    And the setup completes in under 15 minutes total

  Scenario: Database seeding generates complete test data
    Given the development environment is running
    When a developer runs `make db-seed`
    Then all core entity tables are populated with data
    And user profiles exist for each defined role (user, premium, admin)
    And users exist in all 30 demographic tiers plus OPEN tier
    And administrator profiles exist (minimum 3)
    And tracker connections exist for all 3 providers
    And activities exist with varied types and intensities
    And point transactions exist with all transaction types
    And drawings exist in all statuses (draft, open, closed, completed)
    And tickets exist across multiple drawings
    And referential integrity is maintained (no orphaned FKs)
    And the seed completes in under 2 minutes

  Scenario: Database reset returns to clean state
    Given the database contains data
    And the development environment is running
    When a developer runs `make db-reset`
    Then all tables are dropped
    And migrations are re-applied from scratch
    And seed data is regenerated
    And the database is in a known clean state
    And the reset completes in under 5 minutes

Feature: Reporting API

  Scenario: List entities with pagination
    Given the database contains seeded data
    When I call GET /api/v1/users?page=1&per_page=10
    Then I receive HTTP 200
    And the response contains up to 10 user records
    And the response includes pagination metadata with total count
    And the response time is under 500ms

  Scenario: Filter entities by field
    Given the database contains seeded data
    When I call GET /api/v1/activities?filter[activity_type]=workout
    Then I receive HTTP 200
    And all returned activities have activity_type = "workout"
    And the response includes pagination metadata

  Scenario: Sort entities by field
    Given the database contains seeded data
    When I call GET /api/v1/users?sort=-created_at
    Then I receive HTTP 200
    And users are ordered by created_at descending
    And the first user has the most recent created_at

  Scenario: Get single entity by ID
    Given an entity with ID {id} exists in the database
    When I call GET /api/v1/users/{id}
    Then I receive HTTP 200
    And the response contains all user fields
    And related entities are properly referenced (profile, connections)

  Scenario: Entity not found returns 404
    Given no entity with ID "550e8400-e29b-41d4-a716-446655440000" exists
    When I call GET /api/v1/users/550e8400-e29b-41d4-a716-446655440000
    Then I receive HTTP 404
    And the response follows RFC 7807 error format
    And the error includes a clear message

Feature: CRUD Operations

  Scenario: Create entity with valid data
    Given valid user data in request body
    When I call POST /api/v1/users with the data
    Then I receive HTTP 201
    And the response contains the created user with generated ID
    And the user exists in the database with all provided fields

  Scenario: Create entity with invalid data returns validation error
    Given invalid user data (missing required field: email)
    When I call POST /api/v1/users with the data
    Then I receive HTTP 422
    And the response follows RFC 7807 error format
    And the errors array includes a field-specific error for "email"

  Scenario: Update entity with valid data
    Given a user with ID {id} exists
    When I call PUT /api/v1/users/{id} with updated data
    Then I receive HTTP 200
    And the response contains updated values
    And the database reflects the changes
    And the updated_at timestamp is newer

  Scenario: Delete entity (soft delete)
    Given a user with ID {id} exists
    When I call DELETE /api/v1/users/{id}
    Then I receive HTTP 204
    And the user no longer appears in list endpoints
    And the user record still exists in database with deleted_at set

Feature: Health Checks

  Scenario: Basic health check confirms app is running
    Given the application is running
    When I call GET /health
    Then I receive HTTP 200
    And the response indicates status: "ok"
    And the response time is under 100ms

  Scenario: Readiness check confirms database connectivity
    Given the application is running
    And the Oracle database is accessible
    When I call GET /health/ready
    Then I receive HTTP 200
    And the response confirms database connectivity
    And the response includes database version info

  Scenario: Readiness check fails when database is down
    Given the application is running
    And the Oracle database is not accessible
    When I call GET /health/ready
    Then I receive HTTP 503
    And the response indicates database connection failure

Feature: Test Suite

  Scenario: All tests pass without errors
    Given the development environment is running
    When I run `make test`
    Then all unit tests pass
    And all integration tests pass
    And no tests are skipped unexpectedly
    And the test run completes in under 2 minutes

  Scenario: Coverage requirements are met
    Given the development environment is running
    When I run `make test-coverage`
    Then data layer coverage exceeds 90%
    And API layer coverage exceeds 85%
    And overall coverage exceeds 85%
    And a coverage report is generated in HTML format

Feature: API Documentation

  Scenario: OpenAPI documentation is accessible
    Given the application is running
    When I navigate to http://localhost:8000/docs
    Then I see Swagger UI with all endpoints documented
    And I can expand each endpoint to see request/response schemas
    And I can try endpoints directly from the UI
    And request/response schemas are displayed with examples

Feature: HTML Test Page

  Scenario: Test page is accessible in development mode
    Given the application is running in development mode (APP_ENV=development)
    When I navigate to http://localhost:8000/test/
    Then I see the test page with navigation tabs
    And all tabs are visible (API Tester, Leaderboards, Reports, Data Controls)
    And the page layout is responsive

  Scenario: Test page is disabled in production mode
    Given the application is running in production mode (APP_ENV=production)
    When I navigate to http://localhost:8000/test/
    Then I receive HTTP 404 Not Found

  Scenario: API endpoint testing via test page
    Given the test page is loaded in a browser
    And the database contains seeded data
    When I select "Users" entity from the API Tester dropdown
    And I click "List All" button
    Then I see the JSON response displayed with syntax highlighting
    And I see the HTTP status code 200
    And I see the response time in milliseconds
    And pagination controls are functional (Next/Previous)

  Scenario: CRUD operations via test page forms
    Given the test page is loaded
    And I am on the API Tester tab
    When I fill the Create User form with valid data
    And I click "Create" button
    Then the user is created and response shows the new ID
    When I enter the new ID in the Get User form
    And I click "Get" button
    Then the user details are displayed in the response panel
    When I fill the Update User form with modified data
    And I click "Update" button
    Then the update is confirmed with HTTP 200
    When I enter the ID in the Delete User form
    And I click "Delete" button
    Then the deletion is confirmed with HTTP 204

  Scenario: Leaderboard viewer displays sample data
    Given the test page is loaded
    And the database contains seeded data with activity points
    When I navigate to the Leaderboard Viewer tab
    Then I see sample leaderboards for all periods (Daily, Weekly, Monthly, All-Time)
    And I can select different tiers from the tier filter dropdown
    And rankings display with rank, display name, points, tier
    And pagination allows browsing beyond top 10 users

  Scenario: Report viewer displays system metrics
    Given the test page is loaded
    And the database contains seeded data
    When I navigate to the Report Viewer tab
    Then I see system summary cards with counts (users, activities, drawings, tickets)
    And I see entity breakdown table with counts per entity type
    And I see data integrity status (no orphaned records)
    And all metrics match actual database state

  Scenario: Sample data controls seed database
    Given the test page is loaded
    And the database is empty or contains partial data
    When I navigate to the Data Controls tab
    And I click "Seed Database" button
    Then a loading indicator appears
    And seed data is generated and loaded
    And statistics show counts per entity type (e.g., 30 users, 200 activities)
    And success confirmation is displayed
    And the operation completes in under 2 minutes

  Scenario: Sample data controls reset database
    Given the test page is loaded
    And the database contains data
    When I navigate to the Data Controls tab
    And I click "Reset Database" button
    Then a confirmation dialog appears
    When I confirm the reset
    Then all data is cleared
    And migrations are re-applied
    And seed data is regenerated
    And the database is in a known clean state
    And success confirmation is displayed
```

### Security Considerations

- Database credentials stored in environment variables only (`.env` file, Git-ignored)
- No secrets in version control (enforced by `detect-secrets` pre-commit hook)
- SQL injection prevented via parameterized queries (SQLAlchemy ORM)
- Input validation on all API endpoints via Pydantic schemas
- CORS configured with whitelist origins (default: localhost only)
- Debug mode disabled in production configuration (`APP_DEBUG=false`)
- HTML test page disabled in production via feature flag
- All passwords stored as bcrypt hashes (cost factor 12), never plaintext
- Database TDE (Transparent Data Encryption) enabled on Oracle

### Technical Notes

**Oracle 26ai Docker Setup**:

```yaml
# docker/docker-compose.yml excerpt
services:
  oracle:
    image: container-registry.oracle.com/database/free:latest
    environment:
      - ORACLE_PWD=${ORACLE_PASSWORD}
    ports:
      - "1521:1521"
    volumes:
      - oracle_data:/opt/oracle/oradata
    healthcheck:
      test: ["CMD", "sqlplus", "-L", "sys/${ORACLE_PASSWORD}@//localhost:1521/FREE as sysdba", "@healthcheck.sql"]
      interval: 30s
      timeout: 10s
      retries: 5
    shm_size: 1gb  # Required for Oracle

volumes:
  oracle_data:
```

**Connection Pooling Configuration**:

```python
# src/fittrack/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

oracle_url = f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service}"

engine = create_engine(
    oracle_url,
    pool_size=5,           # Maintain 5 connections
    max_overflow=10,       # Allow up to 15 total connections
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False,            # Set to True for SQL logging in dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**JSON Column Usage**:

```python
# Example: Activity model with metrics JSON column
from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.oracle import RAW

class Activity(Base):
    __tablename__ = "activities"

    activity_id = Column(RAW(16), primary_key=True, default=uuid4_as_raw)
    user_id = Column(RAW(16), ForeignKey("users.user_id"), nullable=False)
    metrics = Column(JSON, nullable=False)  # Oracle native JSON type

    # Create functional index for JSON path queries
    # In migration: CREATE INDEX idx_activity_steps ON activities(JSON_VALUE(metrics, '$.steps'))
```

**Seed Data Script Usage**:

```bash
# Generate default seed data (30 users, 200 activities, 5 drawings)
make db-seed

# Or via Python script with custom parameters
python scripts/seed_data.py --users 100 --activities 500 --drawings 10

# Reset database (drop all, migrate, seed)
make db-reset
```

### Estimated Effort

| Task | Estimate |
|------|----------|
| Docker/infrastructure setup (Compose, Oracle, Redis) | 1 day |
| Database models and migrations (all 12 models, JSON columns) | 2.5 days |
| Repository implementations (base + 7 entity repos) | 2 days |
| Synthetic data generators (factories + seed script) | 1.5 days |
| API endpoints (health, CRUD for all entities, reports) | 2 days |
| Reporting endpoints (/reports/summary) | 0.5 days |
| HTML Test Page - API Tester tab | 1 day |
| HTML Test Page - Leaderboard/Report Viewers | 1 day |
| HTML Test Page - Data Controls & Polish | 0.5 days |
| Test suites (unit + integration for repos and API) | 2 days |
| Documentation (README, ADRs, diagrams) | 1 day |
| **Total** | **16 days** |

### Definition of Done

- [x] `make setup && make dev` works from fresh clone (< 15 min setup)
- [x] `make db-seed` generates complete synthetic data with referential integrity
- [x] All CRUD endpoints functional for all entities (users, activities, drawings, points, etc.)
- [x] All reporting endpoints return valid data (`/reports/summary`)
- [x] All tests passing with >85% overall coverage
- [x] API documentation accessible at http://localhost:8000/docs
- [x] HTML test page accessible at http://localhost:8000/test/ in development mode
- [x] Test page API Tester validates all endpoints with forms and response display
- [x] Test page Leaderboard Viewer displays sample rankings (mock data)
- [x] Test page Report Viewer shows system metrics and data integrity checks
- [x] Test page Data Controls can seed/reset database via API calls
- [x] README enables < 15 minute setup for new developers
- [x] CLAUDE.md complete and accurate (already done)
- [x] Code review completed (no major issues)
- [x] Demo to stakeholders completed (using test page for demonstration)

---

## Checkpoint 2: Authentication & Authorization

### Objective

Implement complete user authentication and authorization system with email/password registration, JWT token-based authentication, role-based access control (RBAC), and email verification. This checkpoint secures the application and enables user-specific functionality.

### Prerequisites

- [x] Checkpoint 1 completed (database, API skeleton, test infrastructure)

### Deliverables

#### Authentication Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Password utilities | `src/fittrack/security/authentication.py` | Bcrypt hashing, password validation, strength checker |
| JWT utilities | `src/fittrack/security/authentication.py` | Token creation/validation (RS256), refresh logic |
| Auth service | `src/fittrack/services/auth_service.py` | Registration, login, email verification, password reset |
| Auth schemas | `src/fittrack/api/schemas/auth.py` | RegisterRequest, LoginRequest, TokenResponse, VerifyEmailRequest |
| Auth routes | `src/fittrack/api/routes/v1/auth.py` | /auth/register, /auth/login, /auth/refresh, /auth/verify-email |
| Email service | `src/fittrack/integrations/email.py` | SendGrid client, email templates |
| Email templates | `templates/emails/` | HTML email templates (verification, password reset) |

#### Authorization Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| RBAC decorators | `src/fittrack/security/authorization.py` | @require_role, @require_permission decorators |
| Auth dependencies | `src/fittrack/api/dependencies.py` | get_current_user, get_current_admin dependencies |
| Middleware | `src/fittrack/api/middleware.py` | JWT validation middleware, request logging |

#### API Endpoint Deliverables

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user account | No |
| POST | `/api/v1/auth/login` | Login with email/password | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh token |
| POST | `/api/v1/auth/verify-email` | Verify email with token | No |
| POST | `/api/v1/auth/forgot-password` | Request password reset | No |
| POST | `/api/v1/auth/reset-password` | Reset password with token | No |
| POST | `/api/v1/auth/logout` | Logout (invalidate refresh token) | Yes |
| GET | `/api/v1/users/me` | Get current user profile | Yes |
| PUT | `/api/v1/users/me` | Update current user | Yes |
| PUT | `/api/v1/users/me/password` | Change password | Yes |

#### Test Deliverables

| Test Suite | Path | Coverage Target |
|------------|------|-----------------|
| Password hashing tests | `tests/unit/security/test_authentication.py` | >95% |
| JWT token tests | `tests/unit/security/test_jwt.py` | >95% |
| Auth service tests | `tests/unit/services/test_auth_service.py` | >90% |
| RBAC tests | `tests/unit/security/test_authorization.py` | >90% |
| Auth endpoint tests | `tests/integration/api/test_auth_endpoints.py` | >85% |
| E2E registration flow | `tests/e2e/test_registration_onboarding.py` | Complete workflow |

#### HTML Test Page Enhancements

**New Tab: Authentication Tester**
- Login form (email, password) with "Login" button
- Register form (email, password, DOB, state) with "Register" button
- Token display panel showing access token, refresh token, expiration
- "Logout" button to clear tokens
- "Test Protected Endpoint" button (calls `/api/v1/users/me` with token)
- Role switcher (simulate user, premium, admin roles for testing)

**Existing Tabs Enhancement**:
- API Tester: Add "Authorization" header input field
- All API calls now include JWT token from Authentication tab

#### Documentation Deliverables

| Document | Description |
|----------|-------------|
| ADR-005 | JWT with RS256 for authentication |
| ADR-006 | Email/password only for MVP (social login deferred) |
| Auth flow diagram | Mermaid sequence diagram (`docs/diagrams/auth-flow.mmd`) |

### Acceptance Criteria

```gherkin
Feature: User Registration

  Scenario: Successful registration with valid data
    Given a new user with email "newuser@example.com"
    And date of birth indicating age 25 (eligible)
    And state of residence "TX" (eligible)
    When the user submits the registration form
    Then a User record is created with status "pending"
    And an email verification email is sent to "newuser@example.com"
    And the response includes HTTP 201
    And the response message indicates "Verification email sent"

  Scenario: Registration fails for underage user
    Given a new user with date of birth indicating age 17 (underage)
    When the user submits the registration form
    Then the response includes HTTP 400
    And the error indicates "Must be 18 or older"
    And no User record is created

  Scenario: Registration fails for ineligible state
    Given a new user with state of residence "NY" (excluded)
    When the user submits the registration form
    Then the response includes HTTP 400
    And the error indicates "State not eligible for sweepstakes"
    And no User record is created

  Scenario: Registration fails for duplicate email
    Given a user with email "existing@example.com" already exists
    When a new user attempts to register with "existing@example.com"
    Then the response includes HTTP 409
    And the error indicates "Email already registered"
    And no duplicate User record is created

  Scenario: Registration fails for weak password
    Given a new user with password "weak" (too short, no complexity)
    When the user submits the registration form
    Then the response includes HTTP 422
    And the error indicates password requirements (12+ chars, complexity)
    And no User record is created

Feature: Email Verification

  Scenario: Successful email verification
    Given a User with status "pending" and unverified email
    And a valid verification token sent to the user's email
    When the user clicks the verification link with the token
    Then the User status is updated to "active"
    And email_verified is set to 1
    And email_verified_at is set to current timestamp
    And the user is redirected to profile completion page

  Scenario: Email verification fails for expired token
    Given a verification token that was generated 25 hours ago (expired)
    When the user clicks the verification link
    Then the response includes HTTP 400
    And the error indicates "Token expired, request new verification email"
    And the User status remains "pending"

  Scenario: Email verification fails for invalid token
    Given an invalid or malformed verification token
    When the user attempts verification
    Then the response includes HTTP 400
    And the error indicates "Invalid verification token"

Feature: User Login

  Scenario: Successful login with valid credentials
    Given a User with email "user@example.com" and verified email
    And the correct password
    When the user submits the login form
    Then the response includes HTTP 200
    And the response contains an access token (JWT, expires in 30 min)
    And the response contains a refresh token (expires in 7 days)
    And the User's last_login_at is updated to current timestamp

  Scenario: Login fails for incorrect password
    Given a User with email "user@example.com"
    And an incorrect password
    When the user submits the login form
    Then the response includes HTTP 401
    And the error indicates "Invalid email or password"
    And no tokens are issued
    And failed login attempt is logged

  Scenario: Login fails for non-existent user
    Given no User with email "nonexistent@example.com" exists
    When a login attempt is made with this email
    Then the response includes HTTP 401
    And the error indicates "Invalid email or password"
    And no tokens are issued

  Scenario: Login fails for unverified email
    Given a User with status "pending" (email not verified)
    And the correct password
    When the user submits the login form
    Then the response includes HTTP 403
    And the error indicates "Email not verified, check inbox"
    And no tokens are issued

  Scenario: Account lockout after 5 failed attempts
    Given a User with email "user@example.com"
    And 4 previous failed login attempts in the last 15 minutes
    When the user submits the 5th failed login attempt
    Then the response includes HTTP 429
    And the error indicates "Account temporarily locked, try again in 15 minutes"
    And the User cannot log in for 15 minutes

Feature: Token Refresh

  Scenario: Successful access token refresh
    Given a valid refresh token
    When the user calls /auth/refresh with the refresh token
    Then the response includes HTTP 200
    And a new access token is issued (30 min expiration)
    And a new refresh token is issued (7 days expiration)
    And the old refresh token is invalidated

  Scenario: Refresh fails for expired refresh token
    Given a refresh token that expired 8 days ago
    When the user calls /auth/refresh
    Then the response includes HTTP 401
    And the error indicates "Refresh token expired, please log in again"
    And no new tokens are issued

  Scenario: Refresh fails for invalid refresh token
    Given an invalid or malformed refresh token
    When the user calls /auth/refresh
    Then the response includes HTTP 401
    And the error indicates "Invalid refresh token"

Feature: Protected Endpoints

  Scenario: Accessing protected endpoint with valid token
    Given a User is logged in with a valid access token
    When the user calls GET /api/v1/users/me with the token
    Then the response includes HTTP 200
    And the response contains the user's profile data

  Scenario: Accessing protected endpoint without token
    Given no authentication token is provided
    When the user calls GET /api/v1/users/me
    Then the response includes HTTP 401
    And the error indicates "Authentication required"

  Scenario: Accessing protected endpoint with expired token
    Given an access token that expired 31 minutes ago
    When the user calls GET /api/v1/users/me with the expired token
    Then the response includes HTTP 401
    And the error indicates "Token expired"

  Scenario: Accessing protected endpoint with invalid token
    Given a malformed or tampered JWT token
    When the user calls GET /api/v1/users/me with the invalid token
    Then the response includes HTTP 401
    And the error indicates "Invalid token"

Feature: Role-Based Access Control

  Scenario: User role can access user endpoints
    Given a User with role "user" is logged in
    When the user calls GET /api/v1/users/me
    Then the response includes HTTP 200
    And the user's profile data is returned

  Scenario: User role cannot access admin endpoints
    Given a User with role "user" is logged in
    When the user calls GET /api/v1/admin/users
    Then the response includes HTTP 403
    And the error indicates "Insufficient permissions"

  Scenario: Admin role can access admin endpoints
    Given a User with role "admin" is logged in
    When the user calls GET /api/v1/admin/users
    Then the response includes HTTP 200
    And a list of all users is returned

  Scenario: Admin role can access user endpoints
    Given a User with role "admin" is logged in
    When the user calls GET /api/v1/users/me
    Then the response includes HTTP 200
    And the admin's profile data is returned

Feature: HTML Test Page Authentication

  Scenario: Login via test page
    Given the HTML test page is loaded
    And I am on the Authentication Tester tab
    When I enter valid credentials (email, password)
    And I click "Login" button
    Then the access token is displayed in the Token panel
    And the refresh token is displayed
    And the expiration time is shown
    And a success message is displayed

  Scenario: Register via test page
    Given the HTML test page is loaded
    And I am on the Authentication Tester tab
    When I fill the Register form with valid data
    And I click "Register" button
    Then a success message indicates "Verification email sent"
    And instructions are displayed to check email

  Scenario: Test protected endpoint via test page
    Given I am logged in via the test page
    And tokens are stored in the Token panel
    When I click "Test Protected Endpoint" button
    Then the request is sent to GET /api/v1/users/me with the access token
    And the response displays the current user's profile
    And HTTP 200 status is shown

  Scenario: Token stored across test page tabs
    Given I am logged in via the Authentication Tester tab
    When I navigate to the API Tester tab
    Then the Authorization header is automatically populated with the access token
    And all API requests include the token
```

### Security Considerations

- Passwords hashed with bcrypt (cost factor 12, ~200ms per hash)
- JWT signed with RS256 (asymmetric key pair)
- Private key stored in OCI Vault (prod) or environment variable (dev)
- Refresh tokens stored in HTTP-only, Secure, SameSite cookies
- Access tokens short-lived (30 min) to limit exposure
- Account lockout after 5 failed attempts (15 min cooldown)
- Verification tokens cryptographically random (secrets.token_urlsafe(32))
- Verification tokens single-use (invalidated after use)
- Password reset tokens time-limited (1 hour expiration)
- All auth events logged for security monitoring

### Technical Notes

**JWT Token Structure**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "user",
  "exp": 1737824400,
  "iat": 1737820800,
  "jti": "unique-token-id"
}
```

**Bcrypt Password Hashing**:
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
```

**Email Verification Flow**:
1. User registers → status="pending"
2. System generates random token: `secrets.token_urlsafe(32)`
3. Token stored in Redis with 24-hour TTL: `SET verify:{token} {user_id} EX 86400`
4. Email sent with link: `https://fittrack.com/auth/verify-email?token={token}`
5. User clicks link → API validates token → updates user status="active", email_verified=1
6. Token deleted from Redis

### Estimated Effort

| Task | Estimate |
|------|----------|
| Password hashing utilities (bcrypt) | 0.5 days |
| JWT utilities (create, validate, refresh) | 1 day |
| Auth service (registration, login, verification, password reset) | 1.5 days |
| RBAC decorators and middleware | 1 day |
| Auth API endpoints | 1 day |
| Email service integration (SendGrid) | 0.5 days |
| Email templates (HTML) | 0.5 days |
| Update existing endpoints with auth | 0.5 days |
| HTML test page auth tab | 0.5 days |
| Test suites (unit + integration + e2e) | 1.5 days |
| **Total** | **8 days** |

### Definition of Done

- [x] User registration endpoint functional with validation
- [x] Email verification flow complete (send, verify, activate)
- [x] Login endpoint returns JWT tokens (access + refresh)
- [x] Token refresh endpoint rotates tokens
- [x] Protected endpoints require valid JWT
- [x] RBAC enforced (user vs admin roles)
- [x] Account lockout after failed attempts
- [x] Password reset flow complete
- [x] All existing endpoints updated with auth (where needed)
- [x] HTML test page auth tab functional
- [x] All tests passing with >85% coverage
- [x] Security review passed (no hardcoded secrets, proper hashing)
- [x] Demo completed (registration → verification → login → access protected endpoint)

---

## Checkpoint 3: Fitness Tracker Integration

### Objective

Integrate with fitness trackers via Terra API to enable automatic activity syncing, implement tier-adjusted point calculation, and create background workers for periodic data sync. This checkpoint enables the core value proposition: earning points from fitness activities.

### Prerequisites

- [x] Checkpoint 1 completed (data layer, API skeleton)
- [x] Checkpoint 2 completed (authentication, user accounts)
- [x] Terra API developer account created (credentials obtained)

### Deliverables

#### Terra API Integration Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Terra client | `src/fittrack/integrations/terra.py` | HTTP client for Terra API (auth, webhooks, data fetch) |
| Terra schemas | `src/fittrack/api/schemas/terra.py` | Pydantic models for Terra API requests/responses |
| Connection service | `src/fittrack/services/tracker_service.py` | OAuth flow orchestration, connection management |
| Sync service | `src/fittrack/services/sync_service.py` | Activity sync orchestration, deduplication |
| Points service | `src/fittrack/services/points_service.py` | Tier-adjusted point calculation, daily cap enforcement |
| Tier utils | `src/fittrack/utils/tier.py` | Tier code parsing, multiplier lookup, rate tables |

#### Background Worker Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Celery app | `src/fittrack/workers/celery_app.py` | Celery configuration, task registration |
| Sync tasks | `src/fittrack/workers/sync_tasks.py` | Periodic sync job (every 15 min), error handling |
| Worker Dockerfile | `docker/Dockerfile.worker` | Celery worker container |
| Docker Compose update | `docker/docker-compose.yml` | Add Celery worker service |

#### API Endpoint Deliverables

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/connections` | List user's tracker connections | Yes (user) |
| POST | `/api/v1/connections/{provider}/initiate` | Start OAuth flow for provider | Yes (user) |
| GET | `/api/v1/connections/{provider}/callback` | OAuth callback handler | No (Terra redirects here) |
| DELETE | `/api/v1/connections/{provider}` | Disconnect tracker | Yes (user) |
| POST | `/api/v1/connections/{provider}/sync` | Trigger manual sync | Yes (user) |
| GET | `/api/v1/activities` | List user's activities with filters | Yes (user) |
| GET | `/api/v1/activities/{id}` | Get activity details | Yes (user) |
| GET | `/api/v1/activities/summary` | Activity summary (today, week, month) | Yes (user) |

#### Test Deliverables

| Test Suite | Path | Coverage Target |
|------------|------|-----------------|
| Terra client tests | `tests/unit/integrations/test_terra.py` | >90% (mocked HTTP) |
| Points calculation tests | `tests/unit/services/test_points_service.py` | >95% |
| Tier utils tests | `tests/unit/utils/test_tier.py` | >95% |
| Sync service tests | `tests/unit/services/test_sync_service.py` | >90% |
| Connection endpoint tests | `tests/integration/api/test_connection_endpoints.py` | >85% |
| Activity endpoint tests | `tests/integration/api/test_activity_endpoints.py` | >85% |
| E2E activity sync flow | `tests/e2e/test_activity_to_points.py` | Complete workflow |

#### HTML Test Page Enhancements

**New Tab: Tracker Connection Simulator**
- Provider selection dropdown (Apple Health, Google Fit, Fitbit)
- "Connect Tracker" button → simulates OAuth flow with mock data
- Connection status display (connected trackers, last sync time)
- "Trigger Sync" button → calls `/connections/{provider}/sync` endpoint
- "Disconnect" button → removes connection
- Activity log display (recent synced activities with points earned)

**Existing Tabs Enhancement**:
- Activities tab: Display synced activities with point breakdown
- Points tab: Show point earning history with activity references

#### Documentation Deliverables

| Document | Description |
|----------|-------------|
| ADR-007 | Terra API for unified fitness tracker integration |
| ADR-008 | 15-minute sync interval balances UX and API costs |
| ADR-009 | Tier-adjusted point rates for fair competition |
| Sync flow diagram | Mermaid sequence diagram (`docs/diagrams/sync-flow.mmd`) |
| Point calculation spec | Detailed rate table and tier multipliers (`docs/point-calculation.md`) |

### Acceptance Criteria

```gherkin
Feature: Tracker Connection (OAuth Flow)

  Scenario: User initiates tracker connection
    Given a logged-in user without any tracker connections
    When the user calls POST /api/v1/connections/fitbit/initiate
    Then the response includes HTTP 200
    And the response contains a Terra auth URL
    And the response contains a session token

  Scenario: OAuth callback completes connection
    Given a user has initiated OAuth flow with Fitbit
    And Fitbit redirects back with authorization code
    When the callback handler receives the code
    Then a TrackerConnection record is created with encrypted tokens
    And is_primary is set to 1 (first connection)
    And sync_status is set to "pending"
    And an immediate sync job is queued
    And the user is redirected to dashboard with success message

  Scenario: User connects second tracker (non-primary)
    Given a user already has a Fitbit connection (is_primary=1)
    When the user connects Google Fit
    Then a TrackerConnection record is created for Google Fit
    And Google Fit connection has is_primary=0
    And both connections are active

  Scenario: User designates new primary tracker
    Given a user has connections to Fitbit (primary) and Google Fit (non-primary)
    When the user calls PUT /api/v1/connections/google_fit/set-primary
    Then Google Fit connection is_primary is set to 1
    And Fitbit connection is_primary is set to 0

  Scenario: User disconnects tracker
    Given a user has a connection to Fitbit
    When the user calls DELETE /api/v1/connections/fitbit
    Then the TrackerConnection record is deleted
    And existing activities from Fitbit are preserved
    And a success message is returned

Feature: Activity Synchronization

  Scenario: Periodic sync job runs every 15 minutes
    Given a Celery worker is running
    And a user has a connected tracker with last_sync_at 16 minutes ago
    When the periodic sync job executes
    Then the user's tracker is selected for sync
    And the Terra API is called for activity data (last_sync_at to now)
    And new activities are normalized and stored
    And points are calculated and awarded
    And last_sync_at is updated to current time

  Scenario: Sync creates Activity records from Terra data
    Given a user has a Fitbit connection
    And Terra API returns 3 new activities (1 steps, 2 workouts)
    When the sync job processes this user
    Then 3 Activity records are created
    And each activity has normalized fields (type, start_time, duration, intensity)
    And each activity has a metrics JSON column with detailed data
    And each activity has points_earned calculated

  Scenario: Sync deduplicates activities from multiple trackers
    Given a user has both Fitbit (primary) and Google Fit (non-primary) connected
    And both trackers report the same workout (overlapping time window)
    When the sync job processes this user
    Then only the Fitbit activity is stored (primary tracker wins)
    And the Google Fit activity is skipped (logged as duplicate)

  Scenario: Sync handles token expiration
    Given a user's tracker connection has an expired access token
    When the sync job attempts to sync
    Then the worker attempts to refresh the token using refresh_token
    And if refresh succeeds, the new token is stored (encrypted)
    And the sync continues with the new token
    And if refresh fails, sync_status is set to "error"
    And the user is notified to reconnect the tracker

  Scenario: Sync respects daily point cap
    Given a user has already earned 980 points today
    And the sync job processes a new activity worth 50 points
    When points are calculated
    Then only 20 points are awarded (reaching the 1000 cap)
    And the PointTransaction description notes "capped at daily limit"
    And the activity.points_earned is set to 20 (not 50)

  Scenario: Sync handles Terra API errors gracefully
    Given a user is due for sync
    And the Terra API returns HTTP 503 (service unavailable)
    When the sync job attempts to fetch data
    Then the worker logs the error with correlation ID
    And sync_status is set to "error"
    And the job is retried with exponential backoff (max 3 attempts)
    And if all retries fail, the sync is skipped until next cycle

Feature: Point Calculation with Tier Adjustments

  Scenario: Calculate points for beginner tier (1.2x multiplier)
    Given a user with tier_code "M-18-29-BEG" (beginner)
    And an activity of 30 vigorous active minutes
    When points are calculated
    Then base_rate = 3 points/min (vigorous)
    And tier_multiplier = 1.2 (beginner)
    And points = 3 * 30 * 1.2 = 108 points

  Scenario: Calculate points for intermediate tier (1.0x multiplier)
    Given a user with tier_code "F-30-39-INT" (intermediate)
    And an activity of 30 vigorous active minutes
    When points are calculated
    Then base_rate = 3 points/min (vigorous)
    And tier_multiplier = 1.0 (intermediate, baseline)
    And points = 3 * 30 * 1.0 = 90 points

  Scenario: Calculate points for advanced tier (0.9x multiplier)
    Given a user with tier_code "M-40-49-ADV" (advanced)
    And an activity of 30 vigorous active minutes
    When points are calculated
    Then base_rate = 3 points/min (vigorous)
    And tier_multiplier = 0.9 (advanced, normalizes higher volume)
    And points = 3 * 30 * 0.9 = 81 points

  Scenario: Calculate points for OPEN tier (1.0x multiplier)
    Given a user with tier_code "OPEN" (opted into open competition)
    And an activity of 30 vigorous active minutes
    When points are calculated
    Then base_rate = 3 points/min (vigorous)
    And tier_multiplier = 1.0 (OPEN, no adjustment)
    And points = 3 * 30 * 1.0 = 90 points

  Scenario: Calculate points for steps activity
    Given a user with tier_code "F-50-59-INT" (intermediate)
    And an activity of 10,000 steps
    When points are calculated
    Then base_rate = 10 points per 1,000 steps
    And tier_multiplier = 1.0 (intermediate)
    And points = (10,000 / 1,000) * 10 * 1.0 = 100 points

  Scenario: Workout bonus applied for 20+ minute workout
    Given a user completes a 45-minute moderate intensity workout
    When points are calculated
    Then active minutes points = 2 * 45 * tier_multiplier
    And workout bonus = 50 points (20+ min workout)
    And total_points = (active_minutes_points + workout_bonus)
    And max 3 workout bonuses per day enforced

  Scenario: Daily point cap enforced across activities
    Given a user has earned 950 points today (from 5 previous activities)
    And a new activity worth 100 points is synced
    When points are calculated
    Then points awarded = 50 (reaches 1000 cap, truncated from 100)
    And PointTransaction is created with amount=50
    And description notes "Daily cap reached"
    And activity.points_earned = 50

Feature: Manual Sync

  Scenario: User triggers manual sync
    Given a user with a connected tracker
    And last_sync_at was 10 minutes ago
    When the user calls POST /api/v1/connections/fitbit/sync
    Then an immediate sync job is queued (bypasses 15-min interval)
    And the response includes HTTP 202 (Accepted)
    And the response message indicates "Sync queued"

  Scenario: Manual sync rate limited
    Given a user triggered a manual sync 2 minutes ago
    When the user attempts another manual sync
    Then the response includes HTTP 429 (Too Many Requests)
    And the error indicates "Manual sync allowed once per 5 minutes"

Feature: Activity Endpoints

  Scenario: List activities with date filter
    Given a user has 50 activities in the database
    When the user calls GET /api/v1/activities?filter[start_date]=2026-01-01&filter[end_date]=2026-01-31
    Then the response includes HTTP 200
    And only activities within January 2026 are returned
    And pagination metadata is included

  Scenario: List activities with type filter
    Given a user has activities of types: steps, workout, active_minutes
    When the user calls GET /api/v1/activities?filter[activity_type]=workout
    Then the response includes HTTP 200
    And only activities with activity_type="workout" are returned

  Scenario: Get activity details
    Given a user has an activity with ID {id}
    When the user calls GET /api/v1/activities/{id}
    Then the response includes HTTP 200
    And the response contains all activity fields
    And the metrics JSON is included with detailed data
    And the points_earned is displayed

  Scenario: Activity summary endpoint
    Given a user has activities today, this week, and this month
    When the user calls GET /api/v1/activities/summary
    Then the response includes HTTP 200
    And "today" section shows: steps, active minutes, workouts, points earned, points remaining (to cap)
    And "thisWeek" section shows: aggregated steps, minutes, workouts, points, streak days
    And "thisMonth" section shows: aggregated totals

Feature: HTML Test Page Tracker Simulator

  Scenario: Connect tracker via test page
    Given I am logged in on the test page
    And I am on the Tracker Connection Simulator tab
    When I select "Fitbit" from the provider dropdown
    And I click "Connect Tracker" button
    Then a mock OAuth flow is simulated
    And a connection status message appears "Fitbit connected"
    And the connection is added to the "Connected Trackers" list

  Scenario: Trigger manual sync via test page
    Given I have a Fitbit connection in the test page
    When I click "Trigger Sync" button next to Fitbit
    Then a loading indicator appears
    And the manual sync API is called
    And a success message appears "Sync queued for Fitbit"
    And after a few seconds, the activity log is updated with new activities

  Scenario: View synced activities via test page
    Given activities have been synced for the user
    When I view the Activity Log panel on the test page
    Then I see a list of recent activities with:
      - Activity type (steps, workout, active minutes)
      - Date and time
      - Duration
      - Intensity
      - Points earned (with tier adjustment note)
    And I can click an activity to see full metrics JSON

  Scenario: Disconnect tracker via test page
    Given I have a Fitbit connection
    When I click "Disconnect" button next to Fitbit
    Then a confirmation dialog appears
    When I confirm
    Then the connection is removed from the list
    And a success message appears "Fitbit disconnected"
```

### Security Considerations

- Terra API credentials stored in OCI Vault (prod) or .env (dev)
- OAuth tokens encrypted with AES-256-GCM before storage
- Encryption key stored in OCI Vault (prod) or .env (dev)
- OAuth state parameter prevents CSRF attacks
- Token refresh handles expiration proactively (1 hour before expiry)
- All Terra API calls use HTTPS
- Sync errors logged with correlation ID (no PII in logs)
- Rate limiting on manual sync endpoint (once per 5 minutes)

### Technical Notes

**Terra API OAuth Flow**:
```python
# 1. Initiate OAuth
response = terra_client.generate_widget_session(
    reference_id=str(user.user_id),
    providers=["FITBIT"],
    auth_success_redirect_url="https://fittrack.com/dashboard",
    auth_failure_redirect_url="https://fittrack.com/connect-error"
)
# Returns: {"session_id": "...", "url": "https://widget.tryterra.co/session/..."}

# 2. User authenticates with Fitbit (handled by Terra)

# 3. Terra sends webhook to /api/v1/webhooks/terra (auth event)
# Webhook payload includes: user_id (Terra), reference_id (our user_id), status

# 4. Exchange for access tokens (if not already provided via webhook)
terra_client.get_user(user_id=terra_user_id)
# Returns user details, tokens stored by Terra (we store terra_user_id only)
```

**Activity Sync Implementation**:
```python
# Celery periodic task (every 15 minutes)
@celery_app.task
def sync_all_users():
    """Sync activities for all users due for sync."""
    cutoff_time = datetime.utcnow() - timedelta(minutes=15)
    connections = TrackerConnection.query.filter(
        TrackerConnection.last_sync_at < cutoff_time
    ).all()

    for connection in connections:
        sync_user_activities.delay(connection.connection_id)

@celery_app.task(bind=True, max_retries=3)
def sync_user_activities(self, connection_id: str):
    """Sync activities for a single user's tracker connection."""
    try:
        connection = tracker_repo.get_by_id(connection_id)
        tracker_service.sync_activities(connection)
    except TerraAPIError as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)
```

**Point Calculation Rate Table**:
```python
# src/fittrack/utils/tier.py
RATE_TABLE = {
    "steps": {
        "base": 10,  # 10 points per 1,000 steps
    },
    "active_minutes": {
        "light": 1,      # 1 point per minute
        "moderate": 2,   # 2 points per minute
        "vigorous": 3,   # 3 points per minute
    },
    "workout": {
        "bonus": 50,  # Bonus for 20+ min workout (max 3 per day)
    },
}

TIER_MULTIPLIERS = {
    "beginner": 1.2,
    "intermediate": 1.0,
    "advanced": 0.9,
    "OPEN": 1.0,
}

def calculate_activity_points(
    activity_type: str,
    intensity: str,
    quantity: int,
    tier_code: str
) -> int:
    """Calculate tier-adjusted points for an activity."""
    if activity_type == "steps":
        base_points = (quantity / 1000) * RATE_TABLE["steps"]["base"]
    elif activity_type == "active_minutes":
        base_points = quantity * RATE_TABLE["active_minutes"][intensity]
    else:
        base_points = 0

    # Extract tier fitness level from tier_code (M-30-39-INT → intermediate)
    tier_level = parse_tier_fitness_level(tier_code)  # Returns "beginner", "intermediate", etc.
    multiplier = TIER_MULTIPLIERS.get(tier_level, 1.0)

    return int(base_points * multiplier)
```

### Estimated Effort

| Task | Estimate |
|------|----------|
| Terra API client (OAuth, data fetch, error handling) | 2 days |
| Connection service (OAuth flow orchestration) | 1 day |
| Sync service (activity fetch, normalization, deduplication) | 1.5 days |
| Points service (tier-adjusted calculation, daily cap) | 1 day |
| Celery setup (periodic tasks, worker Dockerfile) | 1 day |
| Connection API endpoints | 1 day |
| Activity API endpoints | 0.5 days |
| Tier utilities (parsing, multiplier lookup) | 0.5 days |
| HTML test page tracker simulator | 0.5 days |
| Test suites (unit + integration + e2e) | 2 days |
| **Total** | **10 days** |

### Definition of Done

- [x] Terra API client implemented with OAuth flows
- [x] User can connect/disconnect trackers (all 3 providers)
- [x] Periodic sync job runs every 15 minutes
- [x] Activities synced and stored with normalized format
- [x] Points calculated with tier adjustments (beginner 1.2x, intermediate 1.0x, advanced 0.9x)
- [x] Daily point cap (1,000) enforced
- [x] Workout bonuses applied (max 3 per day)
- [x] Deduplication works (primary tracker wins)
- [x] Token refresh handles expiration
- [x] Manual sync endpoint functional (rate limited)
- [x] Activity list/detail endpoints functional
- [x] Activity summary endpoint functional
- [x] HTML test page tracker simulator functional
- [x] All tests passing with >85% coverage
- [x] Celery worker runs in Docker container
- [x] Demo completed (connect tracker → sync → see activities → points earned)

---

*[Checkpoint 4, 5, and 6 specifications continue below...]*

## Checkpoint 4: Competition & Leaderboards

### Objective

Implement competition tier assignment, leaderboard aggregation queries with caching, and ranking display functionality. This checkpoint enables users to compete fairly within their demographic brackets and see their progress against peers.

### Prerequisites

- [x] Checkpoint 1 completed (data layer)
- [x] Checkpoint 2 completed (authentication, user profiles)
- [x] Checkpoint 3 completed (activity syncing, point earning)

### Deliverables

#### Leaderboard Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Leaderboard service | `src/fittrack/services/leaderboard_service.py` | Ranking calculation, caching, tier filtering |
| Leaderboard schemas | `src/fittrack/api/schemas/leaderboard.py` | LeaderboardResponse, RankingEntry |
| Leaderboard routes | `src/fittrack/api/routes/v1/leaderboards.py` | /leaderboards/{period} endpoints |
| Leaderboard repository | `src/fittrack/database/repositories/leaderboard_repository.py` | Aggregation SQL queries |
| Leaderboard cache | Redis integration | Cache rankings (5-min TTL), invalidate on new activities |

#### Tier Assignment Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Tier calculation | `src/fittrack/utils/tier.py` | Generate tier_code from profile attributes |
| Profile service update | `src/fittrack/services/profile_service.py` | Tier recalculation on profile update |
| Profile API update | `src/fittrack/api/routes/v1/users.py` | PUT /users/me/profile triggers tier recalc |

#### API Endpoint Deliverables

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/leaderboards/daily` | Daily leaderboard for user's tier | Yes (user) |
| GET | `/api/v1/leaderboards/weekly` | Weekly leaderboard for user's tier | Yes (user) |
| GET | `/api/v1/leaderboards/monthly` | Monthly leaderboard for user's tier | Yes (user) |
| GET | `/api/v1/leaderboards/alltime` | All-time leaderboard for user's tier | Yes (user) |
| GET | `/api/v1/leaderboards/{period}?tier={code}` | Leaderboard for specific tier (browse tiers) | Yes (user) |
| GET | `/api/v1/users/{id}/public` | Public profile (for leaderboard links) | Yes (user) |

#### Test Deliverables

| Test Suite | Path | Coverage Target |
|------------|------|-----------------|
| Tier calculation tests | `tests/unit/utils/test_tier_calculation.py` | >95% |
| Leaderboard queries tests | `tests/integration/repositories/test_leaderboard_queries.py` | >90% |
| Leaderboard service tests | `tests/unit/services/test_leaderboard_service.py` | >90% |
| Leaderboard endpoint tests | `tests/integration/api/test_leaderboard_endpoints.py` | >85% |
| Cache invalidation tests | `tests/integration/test_leaderboard_cache.py` | >85% |

#### HTML Test Page Enhancements

**Existing Tab Update: Leaderboard Viewer**
- Replace mock data with real leaderboard API calls
- Period selector (Daily, Weekly, Monthly, All-Time)
- Tier selector dropdown (all 30 tiers + OPEN)
- Rankings table with:
  - Rank (1, 2, 3... with medals for top 3)
  - Display name (clickable to public profile)
  - Points earned in period
  - Tier code
- "Your Position" highlighted row
- Pagination controls (top 100, or view around your rank)
- Auto-refresh every 60 seconds (optional toggle)

#### Documentation Deliverables

| Document | Description |
|----------|-------------|
| ADR-010 | Leaderboard caching strategy (Redis, 5-min TTL) |
| ADR-011 | Tier recalculation on profile update (vs. scheduled job) |
| Tier matrix | Full 30-tier matrix (`docs/tier-matrix.md`) |

### Acceptance Criteria

```gherkin
Feature: Tier Assignment

  Scenario: New user assigned to correct tier
    Given a new user registers with:
      - Biological sex: Male
      - Date of birth: 1990-05-15 (age 35, bracket 30-39)
      - Fitness level: Intermediate
    When the profile is created
    Then tier_code is calculated as "M-30-39-INT"

  Scenario: User opts into OPEN tier
    Given a user with tier_code "F-18-29-BEG"
    When the user updates profile with open_tier_opt_in=true
    Then tier_code is updated to "OPEN"
    And user now competes on OPEN leaderboards

  Scenario: Tier recalculation on birthday (age bracket change)
    Given a user with DOB 1996-01-15 and tier_code "M-18-29-INT"
    And today is 2026-01-16 (user just turned 30)
    When the user updates any profile field (or scheduled job runs)
    Then tier_code is recalculated as "M-30-39-INT"
    And user moves to new leaderboard

  Scenario: Tier recalculation on fitness level change
    Given a user with tier_code "F-30-39-BEG"
    When the user updates fitness_level to "intermediate"
    Then tier_code is recalculated as "F-30-39-INT"
    And user moves to new leaderboard

Feature: Leaderboard Queries

  Scenario: Daily leaderboard shows today's points
    Given users in tier "M-30-39-INT" earned points today:
      - User A: 800 points
      - User B: 750 points
      - User C: 600 points
    When I call GET /api/v1/leaderboards/daily
    Then the response includes HTTP 200
    And rankings are ordered: A (rank 1), B (rank 2), C (rank 3)
    And points shown are today's points only

  Scenario: Weekly leaderboard shows this week's points
    Given users in tier "F-18-29-INT" earned points this week:
      - User A: 4500 points
      - User B: 4200 points
    And today is Wednesday
    When I call GET /api/v1/leaderboards/weekly
    Then rankings show cumulative points since Monday 00:00
    And week resets next Monday at 00:00

  Scenario: All-time leaderboard shows cumulative points
    Given users in tier "M-40-49-ADV" have total_points_earned:
      - User A: 150,000 points
      - User B: 145,000 points
    When I call GET /api/v1/leaderboards/alltime
    Then rankings show cumulative points since account creation
    And points never decrease (only go up)

  Scenario: Leaderboard filters by tier
    Given users exist in multiple tiers
    And I am in tier "M-30-39-INT"
    When I call GET /api/v1/leaderboards/weekly
    Then only users in "M-30-39-INT" are included in rankings
    And users from other tiers are not shown

  Scenario: User can browse other tiers
    Given I am in tier "F-30-39-INT"
    When I call GET /api/v1/leaderboards/weekly?tier=M-30-39-INT
    Then the response includes HTTP 200
    And rankings for "M-30-39-INT" tier are returned
    And I can see other tiers' leaderboards (but not participate)

  Scenario: OPEN tier leaderboard includes all demographics
    Given users in OPEN tier from various demographics:
      - User A: M-18-29-ADV (8000 pts)
      - User B: F-50-59-INT (7500 pts)
      - User C: M-40-49-BEG (7000 pts)
    When I call GET /api/v1/leaderboards/weekly?tier=OPEN
    Then all OPEN tier users are ranked together regardless of demographics
    And rankings are: A, B, C

  Scenario: Leaderboard shows user's position
    Given I am in tier "M-30-39-INT"
    And there are 500 users in this tier
    And I am ranked #45 with 1,420 points this week
    When I call GET /api/v1/leaderboards/weekly
    Then the response includes my rank: 45
    And the response includes my points: 1,420
    And the response includes total users in tier: 500
    And the response includes top 100 rankings
    And the response includes users around my rank (±10)

  Scenario: Ties are broken by timestamp
    Given User A and User B both have 1000 points this week
    And User A reached 1000 points at 10:00 AM
    And User B reached 1000 points at 11:00 AM
    When I call GET /api/v1/leaderboards/weekly
    Then User A is ranked higher than User B (earlier timestamp wins)

Feature: Leaderboard Caching

  Scenario: Leaderboard results are cached in Redis
    Given a leaderboard query is executed for "M-30-39-INT" weekly
    When the query completes
    Then the results are stored in Redis with key "leaderboard:weekly:M-30-39-INT"
    And the cache TTL is set to 5 minutes

  Scenario: Cached leaderboard is served on repeat requests
    Given a leaderboard was cached 2 minutes ago
    When another user requests the same leaderboard
    Then the cached results are served (no database query)
    And the response time is < 50ms

  Scenario: Cache is invalidated when new activities sync
    Given a leaderboard is cached for "M-30-39-INT" weekly
    When a user in this tier syncs new activities (earning points)
    Then the cache for "M-30-39-INT" weekly is invalidated
    And the next request re-queries the database
    And the new rankings reflect the updated points

  Scenario: Cache expires after 5 minutes
    Given a leaderboard was cached 6 minutes ago
    When a user requests this leaderboard
    Then the cache is considered stale
    And the database is queried for fresh rankings
    And the new results are cached with fresh TTL

Feature: HTML Test Page Leaderboard Viewer

  Scenario: View live leaderboards via test page
    Given I am logged in on the test page
    And I have earned points this week
    When I navigate to the Leaderboard Viewer tab
    Then I see live leaderboard data (not mock data)
    And I can select period (Daily, Weekly, Monthly, All-Time)
    And I can select tier from dropdown (my tier pre-selected)
    And rankings display with rank, display name, points, tier

  Scenario: My position is highlighted on leaderboard
    Given I am ranked #45 in my tier
    When I view the leaderboard on the test page
    Then my row is highlighted with a different background color
    And my rank, display name, and points are shown
    And I see the Top 10 users
    And I see users around my rank (ranks 35-55)

  Scenario: Click user to view public profile
    Given I am viewing the leaderboard
    When I click on a user's display name
    Then a modal or side panel opens
    And I see the user's public profile (display name, tier, total points, badges)

  Scenario: Leaderboard auto-refreshes
    Given I have auto-refresh enabled (toggle switch)
    When 60 seconds elapse
    Then the leaderboard is automatically reloaded
    And updated rankings are displayed
    And my position is updated if changed
```

### Security Considerations

- Leaderboard queries use indexed columns (tier_code, points_earned_period, user_id)
- Rate limiting on leaderboard endpoints (max 60 requests per minute per user)
- Public profiles expose minimal data (display name, tier, rank only, no email/DOB)
- Cache keys namespaced to prevent collision (leaderboard:period:tier)
- SQL injection prevented via parameterized queries

### Technical Notes

**Leaderboard Query (Weekly Example)**:
```sql
-- Optimized query for weekly leaderboard
SELECT
  u.user_id,
  p.display_name,
  p.tier_code,
  SUM(pt.amount) AS points_earned,
  ROW_NUMBER() OVER (ORDER BY SUM(pt.amount) DESC, MIN(pt.created_at) ASC) AS rank
FROM users u
JOIN profiles p ON u.user_id = p.user_id
JOIN point_transactions pt ON u.user_id = pt.user_id
WHERE
  p.tier_code = 'M-30-39-INT'
  AND pt.transaction_type = 'earn'
  AND pt.created_at >= '2026-01-12 00:00:00'  -- Start of this week (Monday)
  AND pt.created_at < '2026-01-19 00:00:00'    -- Start of next week
GROUP BY u.user_id, p.display_name, p.tier_code
ORDER BY rank
LIMIT 100;

-- Index for performance
CREATE INDEX idx_point_transactions_leaderboard
ON point_transactions(transaction_type, created_at, user_id)
INCLUDE (amount);
```

**Redis Caching Implementation**:
```python
import redis
import json
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_leaderboard(period: str, tier_code: str) -> dict:
    """Get leaderboard with caching."""
    cache_key = f"leaderboard:{period}:{tier_code}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss: query database
    rankings = leaderboard_repo.get_rankings(period, tier_code)
    result = {
        "period": period,
        "tier_code": tier_code,
        "rankings": rankings,
        "total_users": len(rankings),
        "generated_at": datetime.utcnow().isoformat()
    }

    # Store in cache (5 min TTL)
    redis_client.setex(
        cache_key,
        timedelta(minutes=5),
        json.dumps(result)
    )

    return result

def invalidate_leaderboard_cache(tier_code: str):
    """Invalidate all leaderboard caches for a tier."""
    for period in ["daily", "weekly", "monthly", "alltime"]:
        cache_key = f"leaderboard:{period}:{tier_code}"
        redis_client.delete(cache_key)
```

**Tier Code Calculation**:
```python
def calculate_tier_code(profile: Profile) -> str:
    """Calculate tier code from profile attributes."""
    if profile.open_tier_opt_in:
        return "OPEN"

    # Determine age bracket
    age = (date.today() - profile.date_of_birth).days // 365
    if age < 30:
        age_bracket = "18-29"
    elif age < 40:
        age_bracket = "30-39"
    elif age < 50:
        age_bracket = "40-49"
    elif age < 60:
        age_bracket = "50-59"
    else:
        age_bracket = "60+"

    # Determine sex code
    sex_code = "M" if profile.biological_sex == "male" else "F"

    # Determine fitness code
    fitness_map = {
        "beginner": "BEG",
        "intermediate": "INT",
        "advanced": "ADV"
    }
    fitness_code = fitness_map[profile.fitness_level]

    return f"{sex_code}-{age_bracket}-{fitness_code}"
```

### Estimated Effort

| Task | Estimate |
|------|----------|
| Tier calculation utilities | 0.5 days |
| Leaderboard repository (SQL queries) | 1.5 days |
| Leaderboard service (caching, filtering) | 1 day |
| Leaderboard API endpoints | 1 day |
| Redis caching integration | 0.5 days |
| Cache invalidation logic | 0.5 days |
| Public profile endpoint | 0.5 days |
| HTML test page leaderboard update | 1 day |
| Test suites (unit + integration) | 1.5 days |
| **Total** | **8 days** |

### Definition of Done

- [x] Tier code calculation implemented (30 tiers + OPEN)
- [x] Profile update triggers tier recalculation
- [x] Leaderboard queries functional (daily, weekly, monthly, all-time)
- [x] Leaderboard API endpoints return rankings
- [x] User's position included in leaderboard response
- [x] Leaderboard results cached in Redis (5-min TTL)
- [x] Cache invalidated on new activity sync
- [x] Browse other tiers functionality works
- [x] Public profile endpoint functional
- [x] HTML test page shows live leaderboards (no mock data)
- [x] All tests passing with >85% coverage
- [x] Performance benchmarked (leaderboard query < 500ms, cached < 50ms)
- [x] Demo completed (earn points → see rank on leaderboard → move up in rank)

---

## Checkpoint 5: Sweepstakes Engine

### Objective

Implement complete sweepstakes functionality including drawing creation/management, ticket purchasing with point deduction, CSPRNG-based winner selection, and prize fulfillment workflow. This checkpoint delivers the core gamification value proposition: users can win prizes for their fitness efforts.

### Prerequisites

- [x] Checkpoint 1 completed (data layer including Drawing, Prize, Ticket, Fulfillment models)
- [x] Checkpoint 2 completed (authentication, user accounts)
- [x] Checkpoint 4 completed (point earning system functional)

### Deliverables

#### Sweepstakes Service Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Drawing service | `src/fittrack/services/drawing_service.py` | Drawing CRUD, status transitions, eligibility validation |
| Ticket service | `src/fittrack/services/ticket_service.py` | Ticket purchase, validation, point deduction |
| Execution service | `src/fittrack/services/execution_service.py` | Winner selection (CSPRNG), result publication |
| Fulfillment service | `src/fittrack/services/fulfillment_service.py` | Prize delivery workflow, status management |
| Notification service | `src/fittrack/services/notification_service.py` | Winner notifications, participant emails |
| CSPRNG utilities | `src/fittrack/security/random.py` | Cryptographically secure random number generation |

#### Background Worker Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Drawing tasks | `src/fittrack/workers/drawing_tasks.py` | Scheduled drawing execution (checks every minute) |
| Notification tasks | `src/fittrack/workers/notification_tasks.py` | Async email sending (winner alerts, results) |
| Drawing state machine | `src/fittrack/services/drawing_service.py` | Status transition validation logic |

#### API Endpoint Deliverables

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/drawings` | List available and recent drawings | Yes (user) |
| GET | `/api/v1/drawings/{id}` | Get drawing details | Yes (user) |
| POST | `/api/v1/drawings/{id}/tickets` | Purchase tickets for drawing | Yes (user) |
| GET | `/api/v1/drawings/{id}/results` | Get drawing results (after completion) | Yes (user) |
| GET | `/api/v1/tickets` | List user's tickets (all drawings) | Yes (user) |
| GET | `/api/v1/fulfillments` | List user's prize fulfillments | Yes (user) |
| PUT | `/api/v1/fulfillments/{id}/address` | Provide shipping address for physical prize | Yes (user) |
| POST | `/api/v1/admin/drawings` | Create new drawing | Yes (admin) |
| PUT | `/api/v1/admin/drawings/{id}` | Update drawing | Yes (admin) |
| POST | `/api/v1/admin/drawings/{id}/execute` | Manually trigger drawing execution | Yes (admin) |
| GET | `/api/v1/admin/fulfillments` | List all pending fulfillments | Yes (admin) |
| PUT | `/api/v1/admin/fulfillments/{id}` | Update fulfillment status | Yes (admin) |
| POST | `/api/v1/admin/fulfillments/{id}/ship` | Mark as shipped with tracking | Yes (admin) |

#### Test Deliverables

| Test Suite | Path | Coverage Target |
|------------|------|-----------------|
| CSPRNG tests | `tests/unit/security/test_random.py` | >95% |
| Drawing service tests | `tests/unit/services/test_drawing_service.py` | >90% |
| Ticket service tests | `tests/unit/services/test_ticket_service.py` | >90% |
| Execution service tests | `tests/unit/services/test_execution_service.py` | >95% (critical logic) |
| Fulfillment service tests | `tests/unit/services/test_fulfillment_service.py` | >90% |
| Drawing endpoint tests | `tests/integration/api/test_drawing_endpoints.py` | >85% |
| Admin drawing tests | `tests/integration/api/test_admin_drawing_endpoints.py` | >85% |
| E2E ticket purchase flow | `tests/e2e/test_ticket_purchase_drawing.py` | Complete workflow |
| E2E prize fulfillment flow | `tests/e2e/test_prize_fulfillment.py` | Complete workflow |

#### HTML Test Page Enhancements

**New Tab: Drawings & Tickets**
- Drawings list (open, upcoming, completed) with filters
- Drawing detail cards (prizes, cost, odds, closing time)
- "Buy Tickets" button with quantity selector
- Ticket purchase confirmation modal
- "My Tickets" section showing all entries
- Drawing results display (winners, ticket numbers, prizes)
- Fulfillment status tracking (for winners)

**New Tab: Admin - Drawings**
- Create drawing form (type, name, date, ticket cost, prizes)
- Drawing list with status badges
- Edit/cancel drawing actions
- "Execute Drawing" button (manual trigger)
- Fulfillment management table (pending, shipped, delivered)
- Mark as shipped form (tracking number input)

#### Documentation Deliverables

| Document | Description |
|----------|-------------|
| ADR-012 | CSPRNG for drawing winner selection (audit compliance) |
| ADR-013 | Drawing state machine transitions (workflow integrity) |
| ADR-014 | Manual prize fulfillment for MVP (automation in v1.1) |
| Drawing flow diagram | Mermaid sequence diagram (`docs/diagrams/drawing-flow.mmd`) |
| Sweepstakes rules | Legal compliance document (`docs/sweepstakes-rules.md`) |

### Acceptance Criteria

```gherkin
Feature: Drawing Creation (Admin)

  Scenario: Admin creates daily drawing
    Given I am logged in as an admin
    When I call POST /api/v1/admin/drawings with:
      - type: "daily"
      - name: "Daily Drawing - Jan 16, 2026"
      - ticket_cost_points: 100
      - drawing_time: "2026-01-16T21:00:00Z"
      - ticket_sales_close: "2026-01-16T20:55:00Z"
      - prizes: [{"rank": 1, "name": "$50 Amazon Gift Card", "value_usd": 50}]
      - eligibility: {"user_type": "all", "min_account_age_days": 7}
    Then the response includes HTTP 201
    And a Drawing record is created with status "draft"
    And a Prize record is created linked to the drawing

  Scenario: Admin cannot create drawing with invalid dates
    Given I am logged in as an admin
    When I create a drawing with ticket_sales_close AFTER drawing_time
    Then the response includes HTTP 422
    And the error indicates "Sales close time must be before drawing time"

  Scenario: Admin approves drawing (draft → scheduled)
    Given a drawing exists with status "draft"
    When I call PUT /api/v1/admin/drawings/{id} with status "scheduled"
    Then the drawing status is updated to "scheduled"
    And the drawing will become "open" at the scheduled time

Feature: Ticket Purchase

  Scenario: User purchases tickets with sufficient points
    Given I am logged in with 1000 points
    And a drawing exists with status "open" and ticket_cost 100
    When I call POST /api/v1/drawings/{id}/tickets with quantity 5
    Then the response includes HTTP 201
    And 5 Ticket records are created
    And a PointTransaction is created with amount -500
    And my point balance is updated to 500
    And drawing.total_tickets is incremented by 5

  Scenario: User cannot purchase tickets with insufficient points
    Given I am logged in with 50 points
    And a drawing exists with ticket_cost 100
    When I attempt to purchase 1 ticket
    Then the response includes HTTP 409
    And the error indicates "Insufficient points"
    And no tickets are created
    And point balance remains 50

  Scenario: User cannot purchase tickets for closed drawing
    Given a drawing exists with status "closed"
    When I attempt to purchase tickets
    Then the response includes HTTP 403
    And the error indicates "Ticket sales closed"

  Scenario: User sees current odds when purchasing
    Given a drawing has 1000 total tickets sold
    And I own 0 tickets for this drawing
    When I view the drawing details
    Then I see current odds: "1 in 1001" (if I buy 1 ticket)
    When I purchase 10 tickets
    Then my odds become "1 in 101"

  Scenario: Ticket purchases are final (no refunds)
    Given I have purchased tickets for a drawing
    When the drawing is in status "open"
    Then there is no refund option (as per sweepstakes rules)
    And tickets are valid until drawing completes

Feature: Drawing Status Transitions

  Scenario: Drawing transitions from scheduled to open
    Given a drawing with status "scheduled"
    And current time >= scheduled open time
    When the status update cron job runs
    Then the drawing status is updated to "open"
    And users can now purchase tickets

  Scenario: Drawing transitions from open to closed
    Given a drawing with status "open"
    And current time >= ticket_sales_close time
    When the status update cron job runs
    Then the drawing status is updated to "closed"
    And ticket purchases are no longer allowed

  Scenario: Drawing transitions from closed to completed (after execution)
    Given a drawing with status "closed"
    And current time >= drawing_time
    When the drawing execution job runs
    Then winners are selected via CSPRNG
    And the drawing status is updated to "completed"
    And completed_at timestamp is set

Feature: Drawing Execution (Winner Selection)

  Scenario: Drawing executes and selects winner via CSPRNG
    Given a drawing with status "closed" and 1000 tickets sold
    And current time >= drawing_time
    When the drawing execution job runs
    Then ticket numbers are assigned (1 to 1000)
    And a random number is generated using secrets.SystemRandom()
    And the winning ticket number is selected
    And the winning ticket is marked is_winner=1
    And a PrizeFulfillment record is created
    And the winner is notified via email
    And drawing status is set to "completed"
    And random_seed is stored for audit

  Scenario: Drawing with multiple prizes selects multiple winners
    Given a drawing with 3 prizes (ranks 1, 2, 3)
    And 500 tickets sold
    When the drawing executes
    Then 3 winning tickets are selected (no duplicates)
    And each winner is assigned to their respective prize rank
    And 3 PrizeFulfillment records are created

  Scenario: Drawing execution is idempotent
    Given a drawing that was already executed (completed_at is set)
    When the execution job runs again
    Then the job detects completed_at and exits early
    And no duplicate winner selection occurs

  Scenario: Drawing results are published
    Given a drawing just completed
    When the execution finishes
    Then results are available at GET /api/v1/drawings/{id}/results
    And results include: winners (display names), prizes, ticket numbers
    And all participants are notified via email

Feature: Prize Fulfillment (Physical Prize)

  Scenario: Winner is notified and provides shipping address
    Given I won a physical prize (Fitbit watch)
    And a PrizeFulfillment record was created with status "pending"
    When the winner notification email is sent
    Then I receive an email with a link to claim my prize
    When I click the link and provide my shipping address
    Then the fulfillment status is updated to "address_confirmed"
    And the admin is notified to ship the prize

  Scenario: Admin ships physical prize
    Given a fulfillment with status "address_confirmed"
    And I am logged in as an admin
    When I call POST /api/v1/admin/fulfillments/{id}/ship with:
      - carrier: "USPS"
      - tracking_number: "9400123456789"
    Then the fulfillment status is updated to "shipped"
    And shipped_at timestamp is set
    And the winner is notified via email with tracking info

  Scenario: Winner confirms delivery (or admin marks delivered)
    Given a fulfillment with status "shipped"
    When the admin marks it as delivered
    Then the fulfillment status is updated to "delivered"
    And delivered_at timestamp is set
    And the fulfillment is complete

Feature: Prize Fulfillment (Digital Prize)

  Scenario: Winner receives digital prize immediately
    Given I won a digital prize ($50 Amazon gift card)
    When the drawing completes
    Then I receive an email with the gift card code
    And the fulfillment status is set to "delivered"
    And no shipping address is required

Feature: Prize Fulfillment (Forfeiture)

  Scenario: Winner does not respond within 14 days
    Given a fulfillment with status "winner_notified"
    And 14 days have elapsed since notified_at
    When the forfeit check job runs
    Then the fulfillment status is set to "forfeited"
    And the prize is returned to sponsor or re-drawn

  Scenario: Winner receives reminder at 7 days
    Given a fulfillment with status "winner_notified"
    And 7 days have elapsed since notified_at
    When the reminder job runs
    Then a reminder email is sent to the winner
    And the status remains "winner_notified"

Feature: HTML Test Page Drawings & Tickets

  Scenario: View available drawings
    Given I am logged in on the test page
    And there are open drawings
    When I navigate to the Drawings & Tickets tab
    Then I see a list of drawings with:
      - Name, type (daily/weekly/monthly), status
      - Prizes, ticket cost, odds
      - Closing time countdown
      - "Buy Tickets" button for open drawings

  Scenario: Purchase tickets via test page
    Given I am viewing an open drawing
    And I have 1000 points
    When I click "Buy Tickets"
    Then a modal opens with quantity selector
    When I select quantity 5 and click "Confirm Purchase"
    Then the purchase is processed
    And a success message appears "5 tickets purchased"
    And my point balance is updated
    And "My Tickets" section shows the new tickets

  Scenario: View drawing results
    Given a drawing has completed
    When I view the drawing details
    Then I see the results:
      - Winner display names
      - Winning ticket numbers
      - Prizes won
      - Total tickets sold
    And I see if I won or not

  Scenario: View fulfillment status (winners only)
    Given I won a prize
    When I view "My Tickets" section
    Then I see the prize I won
    And I see fulfillment status (pending, address_confirmed, shipped, delivered)
    And if status is "winner_notified", I see a "Provide Address" button
    When I click "Provide Address"
    Then a form appears to enter shipping details
    When I submit the form
    Then status updates to "address_confirmed"

Feature: HTML Test Page Admin - Drawings

  Scenario: Admin creates drawing via test page
    Given I am logged in as an admin on the test page
    When I navigate to the Admin - Drawings tab
    And I fill the Create Drawing form with valid data
    And I click "Create Drawing"
    Then the drawing is created
    And appears in the drawings list with status "draft"

  Scenario: Admin executes drawing manually
    Given a drawing with status "closed" exists
    And I am on the Admin - Drawings tab
    When I click "Execute Drawing" button
    Then the drawing execution API is called
    And the drawing status changes to "completed"
    And winners are selected and displayed

  Scenario: Admin manages fulfillments
    Given there are pending fulfillments
    When I view the Fulfillment Management table
    Then I see all fulfillments with:
      - Winner, prize, status, address (if confirmed)
    When I select a fulfillment and click "Mark as Shipped"
    Then a form appears to enter carrier and tracking number
    When I submit the form
    Then the fulfillment status updates to "shipped"
```

### Security Considerations

- CSPRNG uses Python `secrets` module (cryptographically secure)
- Random seed stored for third-party audit verification
- Drawing execution requires admin role (cannot be triggered by users)
- Ticket purchase atomic transaction (point deduction + ticket creation)
- Eligibility validation server-side (never trust client)
- Drawing results immutable after completion (no edits allowed)
- Prize fulfillment PII (shipping address) encrypted at rest (Oracle TDE)
- All drawing events logged with correlation ID for audit

### Technical Notes

**CSPRNG Winner Selection**:
```python
import secrets

def select_winner(tickets: List[Ticket]) -> Ticket:
    """Select random winner using CSPRNG."""
    # Generate cryptographically secure random number
    rng = secrets.SystemRandom()
    winning_ticket_number = rng.randint(1, len(tickets))

    # Store random seed for audit (demonstration purposes)
    random_seed = secrets.token_hex(32)

    # Find winning ticket
    winner = next(t for t in tickets if t.ticket_number == winning_ticket_number)

    return winner, random_seed
```

**Drawing State Machine**:
```python
# Valid status transitions
STATE_TRANSITIONS = {
    "draft": ["scheduled", "cancelled"],
    "scheduled": ["open", "cancelled"],
    "open": ["closed", "cancelled"],
    "closed": ["completed"],
    "completed": [],  # Terminal state
    "cancelled": []   # Terminal state
}

def transition_status(drawing: Drawing, new_status: str):
    """Validate and perform status transition."""
    if new_status not in STATE_TRANSITIONS[drawing.status]:
        raise InvalidStateTransitionError(
            f"Cannot transition from {drawing.status} to {new_status}"
        )

    drawing.status = new_status
    drawing.updated_at = datetime.utcnow()

    if new_status == "completed":
        drawing.completed_at = datetime.utcnow()
```

**Ticket Purchase Transaction**:
```python
def purchase_tickets(user_id: UUID, drawing_id: UUID, quantity: int):
    """Purchase tickets with atomic point deduction."""
    with db.begin():  # Transaction
        # Lock user row for update
        user = user_repo.get_by_id_for_update(user_id)
        drawing = drawing_repo.get_by_id(drawing_id)

        # Validate
        total_cost = quantity * drawing.ticket_cost_points
        if user.point_balance < total_cost:
            raise InsufficientPointsError()

        if drawing.status != "open":
            raise DrawingClosedError()

        # Deduct points
        user.point_balance -= total_cost

        # Create point transaction
        pt = PointTransaction(
            user_id=user_id,
            transaction_type="spend",
            amount=-total_cost,
            balance_after=user.point_balance,
            reference_type="ticket_purchase"
        )
        points_repo.create(pt)

        # Create tickets
        tickets = [
            Ticket(
                drawing_id=drawing_id,
                user_id=user_id,
                purchase_transaction_id=pt.transaction_id
            )
            for _ in range(quantity)
        ]
        ticket_repo.create_batch(tickets)

        # Update drawing total
        drawing.total_tickets += quantity

        # Commit transaction
    return tickets
```

### Estimated Effort

| Task | Estimate |
|------|----------|
| CSPRNG utilities | 0.5 days |
| Drawing service (CRUD, state machine) | 1.5 days |
| Ticket service (purchase, validation) | 1 day |
| Execution service (winner selection) | 1.5 days |
| Fulfillment service (workflow management) | 1 day |
| Notification service (emails) | 0.5 days |
| Drawing API endpoints (user) | 1 day |
| Admin drawing API endpoints | 1 day |
| Fulfillment API endpoints | 1 day |
| Background workers (execution, notifications) | 1 day |
| HTML test page drawings tab | 1 day |
| HTML test page admin drawings tab | 0.5 days |
| Test suites (unit + integration + e2e) | 2 days |
| **Total** | **12 days** |

### Definition of Done

- [x] Drawing CRUD functional (admin can create, update, cancel)
- [x] Drawing state machine enforces valid transitions
- [x] Ticket purchase endpoint functional with point deduction
- [x] Drawing execution job runs every minute, executes closed drawings
- [x] Winner selection uses CSPRNG (Python secrets module)
- [x] Multiple prizes supported (ranks 1, 2, 3, etc.)
- [x] Winner notifications sent via email
- [x] Drawing results published and accessible
- [x] Prize fulfillment workflow functional (physical and digital)
- [x] Shipping address collection for physical prizes
- [x] Admin can mark fulfillments as shipped with tracking
- [x] Forfeit logic for unclaimed prizes (14-day timeout)
- [x] HTML test page drawings tab functional
- [x] HTML test page admin drawings tab functional
- [x] All tests passing with >85% coverage
- [x] Security review passed (CSPRNG audit, state machine integrity)
- [x] Demo completed (create drawing → purchase tickets → execute → notify winner → fulfill prize)

---

## Checkpoint 6: Production Readiness

### Objective

Harden the application for production deployment with comprehensive logging, monitoring, error tracking, load testing, deployment automation, and operational documentation. This checkpoint transforms the MVP into a production-grade system ready for real users.

### Prerequisites

- [x] Checkpoints 1-5 completed (all features functional)

### Deliverables

#### Observability Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Structured logging | `src/fittrack/utils/logging.py` | JSON structured logging with correlation IDs |
| Logging middleware | `src/fittrack/api/middleware.py` | Request/response logging with timing |
| Metrics collection | `src/fittrack/utils/metrics.py` | Prometheus metrics (counters, gauges, histograms) |
| Health checks | `src/fittrack/api/routes/health.py` | Enhanced health checks (DB, Redis, Celery) |
| Error tracking | Integration with Sentry | Automatic error capture, release tracking |
| Performance profiling | Integration with py-spy | CPU profiling for hot paths |

#### Deployment Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Production Dockerfile | `docker/Dockerfile` | Multi-stage build, non-root user |
| Gunicorn config | `gunicorn.conf.py` | Production WSGI server configuration |
| Nginx config | `docker/nginx.conf` | Reverse proxy, static files, rate limiting |
| Docker Compose (prod) | `docker/docker-compose.prod.yml` | Production stack configuration |
| GitHub Actions CD | `.github/workflows/cd.yml` | Automated deployment pipeline |
| Environment configs | `.env.staging`, `.env.production` | Environment-specific configuration templates |
| Database migration script | `scripts/migrate.sh` | Safe migration execution in production |
| Rollback script | `scripts/rollback.sh` | Quick rollback to previous version |

#### Testing & Quality Deliverables

| Component | Path | Description |
|-----------|------|-------------|
| Load test scripts | `tests/load/` | Locust load testing scenarios |
| Performance benchmarks | `tests/performance/` | Endpoint latency benchmarks |
| Security scan config | `.github/workflows/security.yml` | SAST/DAST automated scanning |
| Smoke tests | `tests/smoke/` | Post-deployment validation tests |

#### Documentation Deliverables

| Document | Description |
|----------|-------------|
| Deployment guide | `docs/deployment.md` | Step-by-step production deployment |
| Runbook | `docs/runbook.md` | Operational procedures (incidents, rollbacks, scaling) |
| API documentation | `docs/api/` | Complete endpoint reference (generated from OpenAPI) |
| Monitoring guide | `docs/monitoring.md` | Dashboard setup, alert thresholds, on-call procedures |
| Security hardening | `docs/security.md` | Security checklist, hardening steps, audit procedures |
| ADR-015 | Structured logging with correlation IDs |
| ADR-016 | Prometheus metrics for observability |
| ADR-017 | Gunicorn + Nginx for production deployment |

### Acceptance Criteria

```gherkin
Feature: Structured Logging

  Scenario: All requests are logged with correlation ID
    Given the application is running in production mode
    When a user makes a request to any endpoint
    Then a log entry is created with:
      - correlation_id (unique per request)
      - method, path, status_code, response_time
      - user_id (if authenticated)
      - timestamp, log_level
    And the log is in JSON format for parsing

  Scenario: Errors are logged with full context
    Given an unexpected error occurs during request processing
    When the error is caught by the exception handler
    Then a log entry is created with:
      - correlation_id, user_id, endpoint
      - error type, message, stack trace
      - log_level: ERROR
    And the error is sent to Sentry for tracking

  Scenario: Database queries are logged (debug mode only)
    Given the application is running in development mode
    And LOG_LEVEL=DEBUG
    When a database query is executed
    Then the query SQL and execution time are logged
    And log_level: DEBUG

Feature: Metrics Collection

  Scenario: API request metrics are collected
    Given the application is running
    When requests are made to API endpoints
    Then Prometheus metrics are updated:
      - http_requests_total (counter, labeled by method, path, status)
      - http_request_duration_seconds (histogram, labeled by method, path)
      - http_requests_in_flight (gauge)

  Scenario: Background job metrics are collected
    Given Celery workers are running
    When background jobs execute (sync, drawing execution, etc.)
    Then Prometheus metrics are updated:
      - celery_tasks_total (counter, labeled by task, status)
      - celery_task_duration_seconds (histogram, labeled by task)
      - celery_workers_active (gauge)

  Scenario: Business metrics are collected
    Given users are using the application
    When key events occur (registrations, ticket purchases, etc.)
    Then custom metrics are updated:
      - user_registrations_total (counter)
      - tickets_purchased_total (counter, labeled by drawing_type)
      - points_earned_total (counter)
      - drawings_executed_total (counter)

Feature: Health Checks

  Scenario: Enhanced health check includes all dependencies
    Given the application is running
    When I call GET /health/ready
    Then the response includes HTTP 200 (if all healthy)
    And the response includes status for:
      - database (can connect, can query)
      - redis (can connect, can ping)
      - celery (workers alive, queue lengths)
    And if any dependency is unhealthy, return HTTP 503

  Scenario: Liveness check is lightweight
    Given the application is running
    When I call GET /health/live
    Then the response includes HTTP 200 (if process alive)
    And the check does not query external dependencies
    And response time is < 10ms

Feature: Error Tracking

  Scenario: Errors are sent to Sentry
    Given Sentry integration is configured
    When an unhandled exception occurs
    Then the error is sent to Sentry with:
      - stack trace, error message
      - user_id, correlation_id
      - request context (method, path, headers)
      - environment (production, staging)
      - release version (git commit SHA)

  Scenario: Sentry captures breadcrumbs
    Given a user performs a series of actions
    When an error occurs
    Then Sentry includes breadcrumbs (previous actions):
      - User logged in
      - User purchased tickets
      - Error occurred during ticket purchase

Feature: Load Testing

  Scenario: System handles 5,000 concurrent users
    Given the production environment is running
    When a load test simulates 5,000 concurrent users
    Then the p95 response time is < 500ms
    And the error rate is < 0.5%
    And no memory leaks are detected
    And the system remains stable for 30 minutes

  Scenario: Database connection pool handles load
    Given the load test is running
    When concurrent database queries are executed
    Then the connection pool does not exhaust
    And no "too many connections" errors occur
    And query times remain under 100ms (p95)

  Scenario: Redis cache reduces database load
    Given the leaderboard cache is enabled
    When load test requests leaderboards repeatedly
    Then cache hit rate is > 80%
    And database query count is reduced by 80%

Feature: Deployment Automation

  Scenario: CI/CD pipeline deploys to staging on merge to main
    Given a PR is merged to the main branch
    When the CI/CD pipeline runs
    Then tests are executed (lint, unit, integration)
    And security scans are performed (SAST, dependency check)
    And Docker image is built and pushed to registry
    And the application is deployed to staging environment
    And smoke tests are executed on staging
    And if all pass, deployment is marked successful

  Scenario: Production deployment requires manual approval
    Given staging deployment succeeded
    When a maintainer approves production deployment
    Then the CI/CD pipeline deploys to production
    And database migrations are executed (if any)
    And the application containers are updated (rolling update)
    And smoke tests are executed on production
    And if smoke tests fail, automatic rollback is triggered

  Scenario: Rollback is executed within 5 minutes
    Given a production deployment introduced a critical bug
    When the rollback script is executed
    Then the previous Docker image tag is deployed
    And database migrations are rolled back (if safe)
    And the application is restored to working state
    And the rollback completes within 5 minutes

Feature: Security Hardening

  Scenario: Application runs as non-root user
    Given the Docker container is running
    When I inspect the running process
    Then the application runs as user "fittrack" (UID 1000)
    And the user has no sudo privileges
    And file system is read-only except for /tmp

  Scenario: Secrets are managed securely
    Given the production environment is running
    When I inspect environment variables
    Then no secrets are visible in plain text
    And secrets are loaded from OCI Vault
    And secrets are rotated quarterly

  Scenario: Rate limiting protects against abuse
    Given an attacker attempts to spam API endpoints
    When requests exceed rate limits (100 req/min)
    Then HTTP 429 responses are returned
    And the attacker's IP is temporarily blocked (15 min)
    And admins are alerted to suspicious activity

  Scenario: Security headers are configured
    Given the application is running
    When I make a request to any endpoint
    Then response includes security headers:
      - Strict-Transport-Security: max-age=31536000
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - Content-Security-Policy: default-src 'self'

Feature: Monitoring & Alerts

  Scenario: Prometheus metrics are scraped
    Given the application is running
    When Prometheus scrapes /metrics endpoint
    Then metrics are returned in Prometheus format
    And scrape duration is < 100ms

  Scenario: Alert fires for high error rate
    Given the application is running in production
    When the error rate exceeds 1% for 5 minutes
    Then an alert is fired to PagerDuty
    And the on-call engineer is notified
    And the alert includes correlation IDs for debugging

  Scenario: Alert fires for high latency
    Given the application is running
    When p95 latency exceeds 1 second for 5 minutes
    Then an alert is fired to PagerDuty
    And the on-call engineer is notified

  Scenario: Alert fires for database connection exhaustion
    Given the application is running
    When database connection pool utilization exceeds 90%
    Then an alert is fired to PagerDuty
    And the alert includes current pool size and active connections

Feature: Smoke Tests (Post-Deployment)

  Scenario: Smoke tests validate core functionality
    Given the application was just deployed
    When smoke tests execute
    Then the following tests pass:
      - Health check returns 200
      - User can register
      - User can login and receive JWT
      - User can view leaderboards
      - User can view drawings
      - Admin can create drawing
    And if any test fails, deployment is marked failed
    And rollback is triggered
```

### Security Considerations

- Docker container runs as non-root user (UID 1000)
- Secrets managed via OCI Vault (prod) with quarterly rotation
- Rate limiting enforced at Nginx level (100 req/min per IP)
- Security headers configured (HSTS, CSP, X-Frame-Options)
- SAST/DAST scans in CI/CD pipeline (Snyk, OWASP ZAP)
- Dependency vulnerability scanning (Snyk, safety)
- Database credentials rotated quarterly
- TLS 1.3 required, TLS 1.2 minimum
- Logs sanitized (no PII, no secrets)
- Sentry error tracking with data scrubbing (PII redacted)

### Technical Notes

**Structured Logging Configuration**:
```python
# src/fittrack/utils/logging.py
import structlog
import logging

def configure_logging():
    """Configure structured logging with JSON output."""
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()

# Usage
logger.info(
    "ticket_purchase_completed",
    user_id=str(user_id),
    drawing_id=str(drawing_id),
    quantity=5,
    points_spent=500,
    correlation_id=correlation_id
)
```

**Prometheus Metrics**:
```python
# src/fittrack/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"]
)

# Business metrics
user_registrations_total = Counter(
    "user_registrations_total",
    "Total user registrations"
)

tickets_purchased_total = Counter(
    "tickets_purchased_total",
    "Total tickets purchased",
    ["drawing_type"]
)
```

**Gunicorn Configuration**:
```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
timeout = 60
keepalive = 5
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

**Load Testing with Locust**:
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class FitTrackUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before tasks."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def view_leaderboard(self):
        """View weekly leaderboard."""
        self.client.get(
            "/api/v1/leaderboards/weekly",
            headers=self.headers
        )

    @task(2)
    def view_drawings(self):
        """View available drawings."""
        self.client.get(
            "/api/v1/drawings",
            headers=self.headers
        )

    @task(1)
    def purchase_tickets(self):
        """Purchase tickets (if user has points)."""
        self.client.post(
            "/api/v1/drawings/{drawing_id}/tickets",
            json={"quantity": 1},
            headers=self.headers
        )

# Run with: locust -f tests/load/locustfile.py --host http://localhost:8000
```

### Estimated Effort

| Task | Estimate |
|------|----------|
| Structured logging (JSON, correlation IDs) | 0.5 days |
| Logging middleware (request/response timing) | 0.5 days |
| Prometheus metrics (HTTP, business, Celery) | 1 day |
| Enhanced health checks (DB, Redis, Celery) | 0.5 days |
| Sentry integration (error tracking) | 0.5 days |
| Gunicorn + Nginx configuration | 0.5 days |
| Production Dockerfile (multi-stage, non-root) | 0.5 days |
| Docker Compose production setup | 0.5 days |
| GitHub Actions CD pipeline | 1 day |
| Database migration/rollback scripts | 0.5 days |
| Load testing (Locust scenarios) | 1 day |
| Performance benchmarking | 0.5 days |
| Security scanning (SAST/DAST) | 0.5 days |
| Smoke tests (post-deployment) | 0.5 days |
| Deployment guide | 0.5 days |
| Runbook (operational procedures) | 0.5 days |
| Monitoring guide (dashboards, alerts) | 0.5 days |
| Security hardening checklist | 0.5 days |
| **Total** | **10 days** |

### Definition of Done

- [x] Structured logging (JSON) implemented with correlation IDs
- [x] All requests logged with timing, status, user context
- [x] Errors logged with full context and sent to Sentry
- [x] Prometheus metrics exposed at /metrics endpoint
- [x] HTTP, business, and Celery metrics collected
- [x] Enhanced health checks functional (DB, Redis, Celery)
- [x] Gunicorn + Nginx production configuration
- [x] Production Dockerfile with multi-stage build, non-root user
- [x] Docker Compose production setup functional
- [x] GitHub Actions CD pipeline deploys to staging automatically
- [x] Production deployment requires manual approval
- [x] Database migration script safe for production
- [x] Rollback script tested and functional
- [x] Load testing: 5,000 concurrent users, p95 < 500ms, error rate < 0.5%
- [x] Security headers configured (HSTS, CSP, etc.)
- [x] Rate limiting enforced (100 req/min per IP)
- [x] SAST/DAST scans in CI/CD pipeline
- [x] Smoke tests execute post-deployment
- [x] Deployment guide complete and tested
- [x] Runbook complete with incident procedures
- [x] Monitoring guide with dashboard setup and alert thresholds
- [x] Security hardening checklist complete
- [x] Demo completed (deploy to staging → load test → deploy to production → monitor)

---

## Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|-------------|--------|------------|-------|
| R1 | Terra API service outage | Medium | High | Monitor Terra status page, implement retry logic with exponential backoff, notify users of sync delays | Engineering |
| R2 | Oracle 26ai Free insufficient for load | Low | High | Monitor database metrics (CPU, memory, connections), plan migration to Oracle Autonomous DB if needed | DevOps |
| R3 | Sweepstakes legal compliance failure | Low | Critical | Legal review of rules before launch, conservative state selection, third-party audit of drawing fairness | Legal |
| R4 | Manual prize fulfillment overwhelms admin | Medium | Medium | Monitor fulfillment volume, automate at 100+ fulfillments/month trigger, consider logistics partner | Product |
| R5 | CSPRNG manipulation allegations | Low | Critical | Store random seed for audit, implement immutable audit log, third-party verification available | Engineering |
| R6 | Tier fairness complaints | Medium | Low | Monitor leaderboard distribution, survey users, adjust multipliers based on data | Product |
| R7 | Daily point cap frustrates power users | Low | Low | Monitor outliers, consider tier-specific caps or achievement badges for capped users | Product |
| R8 | Email delivery delays/failures | Medium | Medium | Monitor SendGrid metrics, implement retry queue, use transactional emails (not marketing) | Engineering |
| R9 | Database connection pool exhaustion | Medium | High | Monitor pool utilization, alert at 80%, increase pool size if needed, optimize long-running queries | DevOps |
| R10 | Leaderboard cache invalidation bugs | Low | Medium | Comprehensive cache invalidation tests, monitor cache hit rate, manual cache clear button for admins | Engineering |
| R11 | Drawing execution job failure | Low | Critical | Idempotent execution logic, alert on failure, manual execution fallback, automated retry | Engineering |
| R12 | Security breach (account takeover, data leak) | Low | Critical | MFA in v1.1, rate limiting, security monitoring, incident response plan, penetration testing | Security |

## Assumptions

| ID | Assumption | Impact if Wrong | Validation Plan |
|----|------------|-----------------|-----------------|
| A1 | Terra API covers 80%+ of target market | Low adoption, user complaints | Market research, user survey during beta |
| A2 | 15-minute sync interval acceptable UX | User dissatisfaction | Beta user feedback, consider reducing to 5 min if API limits allow |
| A3 | Tier-adjusted points create fair competition | Complaints about unfairness | Monitor leaderboard distribution, survey users, adjust multipliers |
| A4 | Daily 1,000 point cap prevents gaming | Frustrated power users or continued gaming | Monitor outliers, adjust cap based on data |
| A5 | Email verification sufficient security | Account takeovers | Security monitoring, implement MFA in v1.1 |
| A6 | Manual prize fulfillment scales for MVP | Admin overload | Monitor volume, automate at 100+ fulfillments/month |
| A7 | Gift cards sufficient prizes for MVP | Low user interest | User surveys, sponsor outreach in parallel |
| A8 | OPEN tier opt-in reduces complaints | Low opt-in rate or continued complaints | Track opt-in rate, survey users |
| A9 | Python/FastAPI sufficient performance | Scalability issues | Load testing, profiling, optimize hot paths |
| A10 | 30-minute JWT expiration acceptable UX | Too frequent re-auth | Monitor refresh token usage, extend to 1 hour if needed |

## External Dependencies

| Dependency | Version | Purpose | Fallback |
|------------|---------|---------|----------|
| Terra API | v2 | Fitness tracker integration | Manual activity entry (v1.1 feature) |
| Oracle 26ai Free | 26.1+ | Primary database | Oracle Autonomous DB (paid tier) |
| SendGrid/SES | Latest | Email delivery | Alternative provider (Mailgun, Postmark) |
| Redis | 7.2+ | Caching, message broker | Memcached (caching only, requires different broker) |
| Docker | 24+ | Containerization | Required (no fallback) |
| GitHub Actions | N/A | CI/CD | Alternative CI (GitLab CI, CircleCI) |

---

## Conclusion

This implementation plan delivers FitTrack MVP in **6 checkpoints over approximately 20 weeks**. Each checkpoint delivers demonstrable value, maintains integration with previous work, and includes comprehensive testing.

**Next Steps**:
1. **Checkpoint 1** (16 days): Establish foundation, data layer, test environment
2. **Checkpoint 2** (8 days): Authentication & authorization
3. **Checkpoint 3** (10 days): Fitness tracker integration via Terra API
4. **Checkpoint 4** (8 days): Competition tiers & leaderboards
5. **Checkpoint 5** (12 days): Sweepstakes engine & prize fulfillment
6. **Checkpoint 6** (10 days): Production readiness (logging, monitoring, deployment)

**Success Criteria**:
- All 6 checkpoints completed with Definition of Done met
- All tests passing with >85% coverage
- Load testing validates 5,000 concurrent users
- Security review passed
- Legal review passed (sweepstakes rules)
- Deployment to production successful
- Smoke tests pass in production

Ready to review and begin implementation!
