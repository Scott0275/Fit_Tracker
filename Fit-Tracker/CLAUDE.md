# FitTrack

> Gamified fitness platform with sweepstakes rewards and fair competition tiers

## Project Overview

FitTrack transforms fitness activity into a competitive, rewarding experience by awarding points for tracked physical activities and allowing users to spend those points on sweepstakes tickets for prize drawings. The platform addresses the critical problem of fitness motivation and accountability by providing tangible rewards for consistent effort.

The system integrates with popular fitness trackers (Apple Health, Google Fit, Fitbit via Terra API), automatically syncs activities, calculates points based on configurable rate tables, and places users into fair competition tiers based on age, sex, and fitness level. Users compete on leaderboards within their demographic brackets and can enter daily, weekly, monthly, and annual prize drawings using their earned points.

FitTrack serves health-conscious adults (18+) in sweepstakes-eligible US states, providing a sustainable gamification layer that increases long-term fitness adherence. The MVP focuses on core mechanics: activity tracking, point earning, tiered competition, and sweepstakes functionality, with premium features and native mobile apps deferred to v1.1+.

## Architecture

### System Architecture

FitTrack follows a **layered modular monolith** architecture pattern for MVP simplicity and rapid iteration:

- **API Layer**: FastAPI REST endpoints with OpenAPI documentation
- **Service Layer**: Business logic, workflow orchestration, domain rules
- **Data Layer**: Repository pattern with SQLAlchemy ORM and Oracle JSON Tables
- **Integration Layer**: Terra API client for unified fitness tracker integration
- **Worker Layer**: Background jobs for data sync, leaderboard updates, drawing execution

**Architectural Decisions**:

1. **Monolith First**: Single deployable unit for MVP reduces operational complexity. Clear module boundaries enable future microservices extraction if needed (candidates: sync worker, drawing engine).

2. **Oracle JSON Tables**: Leveraging Oracle's JSON Duality Views provides document-style flexibility for nested/variable data (activity metrics, user goals, drawing eligibility rules) while maintaining relational integrity for core entities.

3. **Terra API Integration**: Third-party fitness data aggregator eliminates need for native iOS app and provides unified interface for Apple Health, Google Fit, and Fitbit. Trade-off: monthly per-user cost (~$0.10) vs. development time savings (3+ weeks).

4. **Batch Sync Architecture**: 15-minute polling interval balances user experience with API rate limits and cost. Async worker processes sync jobs to avoid blocking API requests.

5. **Repository Pattern**: Abstraction layer over ORM enables testability, query optimization, and potential future data store migration without impacting business logic.

### Technology Stack

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| Runtime | Python | 3.12+ | Modern features (type hints, match statements), performance improvements, security patches |
| Web Framework | FastAPI | 0.110+ | Async support, automatic OpenAPI docs, native Pydantic integration, excellent performance |
| Database | Oracle 26ai Free | 26.1+ | JSON Duality Views, advanced JSON indexing, free tier sufficient for MVP, production-grade features |
| ORM | SQLAlchemy | 2.0+ | Industry standard, mature Oracle dialect, async support, comprehensive query API |
| DB Driver | python-oracledb | 2.4+ | Official Oracle driver, thin mode (no client install), connection pooling, async support |
| Migrations | Alembic | 1.13+ | Native SQLAlchemy integration, version-controlled schema changes, rollback support |
| Validation | Pydantic | 2.0+ | FastAPI native, excellent validation/serialization, JSON Schema generation, type safety |
| Task Queue | Celery | 5.3+ | Mature async task processing, scheduled jobs, retry logic, monitoring |
| Message Broker | Redis | 7.2+ | Celery backend, session storage, leaderboard caching, pub/sub for real-time features (v1.1+) |
| Testing | pytest | 8.0+ | Industry standard, excellent plugin ecosystem, async support, parametrization |
| Test Data | Faker, factory_boy | Latest | Realistic synthetic data generation, deterministic seeding, relationship handling |
| HTTP Client | httpx | 0.27+ | Async support for Terra API calls, connection pooling, timeout handling |
| Containerization | Docker | 24+ | Oracle 26ai deployment, development parity, isolated environments |
| CI/CD | GitHub Actions | N/A | Native GitHub integration, free for public repos, matrix testing |

### Database Design Principles

**Oracle JSON Tables Architecture (REQUIRED)**:

- **Primary data storage**: Oracle JSON Tables with native JSON type for all domain entities requiring flexibility
- **Hybrid approach**: JSON columns for nested/variable data + traditional columns for frequently queried/indexed fields
- **JSON indexing**: Functional indexes on JSON paths using `JSON_VALUE()` for performance (e.g., `CREATE INDEX idx_activity_type ON activities(JSON_VALUE(metrics, '$.type'))`)
- **JSON Duality Views**: Expose JSON document-style API over relational tables for simplified queries and updates
- **Connection pooling**: `python-oracledb` with pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=3600

**General Database Principles**:

- All timestamps stored as `TIMESTAMP WITH TIME ZONE`, application logic uses UTC
- Soft deletes preferred for audit trail (deleted_at column, NULL = active)
- Optimistic locking via `version` column for concurrent update conflict detection
- All primary keys use `RAW(16)` (UUID) for distributed system compatibility
- Foreign keys enforced at database level for referential integrity
- Indexing strategy: covering indexes for leaderboard queries, functional indexes for JSON paths, unique constraints for business rules

**Data Layer Implementation Requirements**:

- All entity models MUST use SQLAlchemy declarative base with common mixins (timestamps, soft delete, version)
- Repositories MUST implement generic CRUD interface with type hints
- All database operations MUST use parameterized queries (SQLAlchemy handles this)
- Migration scripts MUST be idempotent and include both upgrade/downgrade
- JSON columns MUST have CHECK constraints where structure is critical (e.g., eligibility rules format)

## Project Structure

```
fit-tracker/
├── src/
│   └── fittrack/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app factory, lifespan events
│       ├── config.py                  # Pydantic Settings, environment config
│       ├── exceptions.py              # Custom exception hierarchy
│       ├── database/
│       │   ├── __init__.py
│       │   ├── connection.py          # Engine, session factory, dependency
│       │   ├── models/                # SQLAlchemy ORM models
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # Declarative base, mixins (TimestampMixin, SoftDeleteMixin)
│       │   │   ├── user.py            # User, Profile models
│       │   │   ├── tracker.py         # TrackerConnection model
│       │   │   ├── activity.py        # Activity model
│       │   │   ├── points.py          # PointTransaction model
│       │   │   ├── drawing.py         # Drawing, Prize models
│       │   │   ├── ticket.py          # Ticket model
│       │   │   ├── fulfillment.py     # PrizeFulfillment model
│       │   │   └── sponsor.py         # Sponsor model
│       │   └── repositories/          # Data access layer
│       │       ├── __init__.py
│       │       ├── base.py            # Generic repository interface
│       │       ├── user_repository.py
│       │       ├── activity_repository.py
│       │       ├── points_repository.py
│       │       ├── drawing_repository.py
│       │       ├── ticket_repository.py
│       │       ├── leaderboard_repository.py  # Specialized aggregation queries
│       │       └── fulfillment_repository.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── dependencies.py        # FastAPI dependencies (db session, current user, etc.)
│       │   ├── middleware.py          # Request logging, timing, correlation IDs
│       │   ├── routes/                # API endpoint definitions
│       │   │   ├── __init__.py
│       │   │   ├── health.py          # /health, /health/ready
│       │   │   └── v1/
│       │   │       ├── __init__.py
│       │   │       ├── auth.py        # /auth/register, /auth/login, /auth/refresh
│       │   │       ├── users.py       # /users/me, /users/me/profile
│       │   │       ├── connections.py # /connections (tracker OAuth flows)
│       │   │       ├── activities.py  # /activities, /activities/summary
│       │   │       ├── points.py      # /points/balance, /points/transactions
│       │   │       ├── drawings.py    # /drawings, /drawings/{id}/tickets, /drawings/{id}/results
│       │   │       ├── leaderboards.py# /leaderboards/{period}
│       │   │       ├── admin/         # Admin-only endpoints
│       │   │       │   ├── __init__.py
│       │   │       │   ├── users.py
│       │   │       │   ├── drawings.py
│       │   │       │   ├── sponsors.py
│       │   │       │   ├── fulfillments.py
│       │   │       │   └── analytics.py
│       │   │       └── reports.py     # /reports/summary (for test page)
│       │   └── schemas/               # Pydantic request/response models
│       │       ├── __init__.py
│       │       ├── common.py          # PaginationParams, ErrorResponse, SuccessResponse
│       │       ├── auth.py            # RegisterRequest, LoginRequest, TokenResponse
│       │       ├── user.py            # UserResponse, ProfileUpdate, UserPublic
│       │       ├── activity.py        # ActivityResponse, ActivitySummary
│       │       ├── points.py          # PointTransactionResponse, BalanceResponse
│       │       ├── drawing.py         # DrawingResponse, DrawingListResponse, TicketPurchase
│       │       ├── leaderboard.py     # LeaderboardResponse, RankingEntry
│       │       └── admin.py           # Admin-specific schemas
│       ├── services/                  # Business logic layer
│       │   ├── __init__.py
│       │   ├── auth_service.py        # Registration, login, token management
│       │   ├── profile_service.py     # Profile management, tier assignment
│       │   ├── tracker_service.py     # OAuth flow, Terra API integration
│       │   ├── sync_service.py        # Activity sync orchestration
│       │   ├── points_service.py      # Point calculation, transaction management
│       │   ├── drawing_service.py     # Drawing creation, execution, winner selection
│       │   ├── ticket_service.py      # Ticket purchase, validation
│       │   ├── leaderboard_service.py # Ranking calculation, caching
│       │   ├── fulfillment_service.py # Prize delivery workflow
│       │   └── notification_service.py# Email notifications (winner alerts, etc.)
│       ├── integrations/              # External service clients
│       │   ├── __init__.py
│       │   ├── terra.py               # Terra API client
│       │   └── email.py               # Email provider (SendGrid/SES)
│       ├── workers/                   # Background task definitions
│       │   ├── __init__.py
│       │   ├── celery_app.py          # Celery configuration
│       │   ├── sync_tasks.py          # Periodic activity sync jobs
│       │   ├── leaderboard_tasks.py   # Leaderboard refresh jobs
│       │   ├── drawing_tasks.py       # Scheduled drawing execution
│       │   └── notification_tasks.py  # Async notification sending
│       ├── security/                  # Authentication, authorization, crypto
│       │   ├── __init__.py
│       │   ├── authentication.py      # JWT creation/validation, password hashing
│       │   ├── authorization.py       # RBAC decorators, permission checks
│       │   ├── encryption.py          # OAuth token encryption (AES-256-GCM)
│       │   └── random.py              # CSPRNG for drawing winner selection
│       └── utils/                     # Shared utilities
│           ├── __init__.py
│           ├── datetime.py            # UTC helpers, timezone conversion
│           ├── validation.py          # Custom validators (state eligibility, etc.)
│           └── tier.py                # Tier code generation/parsing logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures, test DB setup
│   ├── factories/                     # factory_boy model factories
│   │   ├── __init__.py
│   │   ├── base.py                    # Common factory configuration
│   │   ├── user_factory.py
│   │   ├── activity_factory.py
│   │   ├── drawing_factory.py
│   │   ├── ticket_factory.py
│   │   └── [entity]_factory.py
│   ├── unit/                          # Unit tests (isolated, mocked)
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── test_points_service.py
│   │   │   ├── test_tier_assignment.py
│   │   │   └── test_drawing_execution.py
│   │   ├── utils/
│   │   │   └── test_tier_logic.py
│   │   └── security/
│   │       └── test_authentication.py
│   ├── integration/                   # Integration tests (real DB)
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── test_user_repository.py
│   │   │   ├── test_activity_repository.py
│   │   │   └── test_leaderboard_queries.py
│   │   └── api/
│   │       ├── test_auth_endpoints.py
│   │       ├── test_drawing_endpoints.py
│   │       └── test_leaderboard_endpoints.py
│   └── e2e/                           # End-to-end workflow tests
│       ├── __init__.py
│       ├── test_registration_onboarding.py
│       ├── test_activity_to_points.py
│       ├── test_ticket_purchase_drawing.py
│       └── test_prize_fulfillment.py
├── migrations/
│   ├── env.py                         # Alembic environment
│   ├── script.py.mako                 # Migration template
│   └── versions/                      # Migration scripts
│       ├── 001_initial_schema.py
│       ├── 002_add_tier_adjustments.py
│       └── ...
├── scripts/
│   ├── seed_data.py                   # Synthetic data generation
│   ├── setup_dev.sh                   # Development environment bootstrap
│   ├── reset_db.sh                    # Database reset utility
│   └── verify_terra_connection.py     # Terra API connectivity test
├── static/
│   └── test/                          # HTML test page (dev only)
│       ├── index.html                 # Main test interface
│       ├── css/
│       │   └── test-page.css
│       └── js/
│           ├── api-tester.js          # Interactive endpoint testing
│           ├── leaderboard-viewer.js  # Sample leaderboard display
│           ├── report-viewer.js       # Data verification reports
│           └── sample-data.js         # Test data loading
├── docker/
│   ├── Dockerfile                     # Production container
│   ├── Dockerfile.dev                 # Development container (hot reload)
│   ├── docker-compose.yml             # Full stack (Oracle, Redis, app, worker)
│   └── docker-compose.test.yml        # Test environment
├── .github/
│   └── workflows/
│       ├── ci.yml                     # PR checks (lint, test, security)
│       └── cd.yml                     # Deployment pipeline (staging, prod)
├── docs/
│   ├── adr/                           # Architecture Decision Records
│   │   ├── 0001-record-architecture-decisions.md
│   │   ├── 0002-oracle-json-tables.md
│   │   ├── 0003-terra-api-integration.md
│   │   └── 0004-tier-based-point-scaling.md
│   ├── api/                           # API documentation supplements
│   │   └── sweepstakes-rules.md
│   └── diagrams/                      # System diagrams
│       ├── architecture.mmd
│       ├── data-model.mmd
│       └── sync-workflow.mmd
├── .env.example                       # Environment variable template
├── .gitignore
├── .pre-commit-config.yaml            # Pre-commit hooks (ruff, mypy, secrets detection)
├── pyproject.toml                     # Project metadata, dependencies, tool config
├── Makefile                           # Development task automation
├── CLAUDE.md                          # This file
├── README.md                          # Project introduction and setup
└── IMPLEMENTATION_PLAN.md             # Development roadmap
```

## Core Domain Entities

### User

**Purpose**: Represents an authenticated account with credentials, role, and point balance. Central entity for all user-scoped operations.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| user_id | RAW(16) | PK | UUID unique identifier |
| email | VARCHAR2(255) | UNIQUE, NOT NULL | Email address (login credential) |
| password_hash | VARCHAR2(255) | NOT NULL | Bcrypt hash of password (cost factor 12) |
| email_verified | NUMBER(1) | DEFAULT 0 | Boolean flag (0=pending, 1=verified) |
| email_verified_at | TIMESTAMP | NULL | Verification timestamp |
| status | VARCHAR2(20) | CHECK constraint | pending, active, suspended, banned |
| role | VARCHAR2(20) | CHECK constraint | user, premium, admin |
| premium_expires_at | TIMESTAMP | NULL | Premium subscription expiration |
| point_balance | NUMBER(10) | DEFAULT 0, >= 0 | Current spendable points |
| created_at | TIMESTAMP | NOT NULL, UTC | Account creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, UTC | Last modification timestamp |
| last_login_at | TIMESTAMP | NULL | Most recent login |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Relationships**:
- One-to-One to Profile (required after registration)
- One-to-Many to TrackerConnections (max 3, one per provider)
- One-to-Many to Activities
- One-to-Many to PointTransactions
- One-to-Many to Tickets

**Business Rules**:
- Email must be verified before profile completion
- Status must be 'active' to participate in drawings
- Point balance cannot go negative (enforced by CHECK constraint)
- Premium role requires premium_expires_at in future
- Admin role bypasses eligibility restrictions

**State Transitions**:
- pending → active: Email verification completed
- active → suspended: Admin action (ToS violation)
- suspended → active: Admin review/appeal accepted
- active → banned: Severe violation (permanent)

### Profile

**Purpose**: Stores user demographic and fitness data for tier assignment and fair competition grouping.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| profile_id | RAW(16) | PK | UUID unique identifier |
| user_id | RAW(16) | FK, UNIQUE | One-to-one to User |
| display_name | VARCHAR2(50) | NOT NULL, UNIQUE | Public username (alphanumeric + underscore) |
| date_of_birth | DATE | NOT NULL | DOB for age verification (18+) |
| state_of_residence | VARCHAR2(2) | NOT NULL | Two-letter state code (eligibility check) |
| biological_sex | VARCHAR2(10) | CHECK constraint | male, female (for tier assignment only) |
| age_bracket | VARCHAR2(10) | CHECK constraint | 18-29, 30-39, 40-49, 50-59, 60+ |
| fitness_level | VARCHAR2(20) | CHECK constraint | beginner, intermediate, advanced |
| tier_code | VARCHAR2(20) | NOT NULL | Computed: M-30-39-INT or OPEN |
| height_inches | NUMBER(3) | NULL | Optional metadata |
| weight_pounds | NUMBER(4) | NULL | Optional metadata |
| goals | JSON | NULL | Array of goal strings (weight_loss, endurance, etc.) |
| created_at | TIMESTAMP | NOT NULL, UTC | Profile creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, UTC | Last modification timestamp |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Relationships**:
- One-to-One to User (parent)

**Business Rules**:
- Age calculated from DOB must be >= 18 years
- State must be in eligible states list (excluded: NY, FL, RI per PRD pending legal review)
- Tier code format: `{SEX}-{AGE_BRACKET}-{FITNESS_LEVEL}` or `OPEN`
- Tier code recalculated on profile update (age bracket may change, fitness level may change)
- Display name must be unique across all profiles
- Users can opt into OPEN tier (competes with all demographics)

**Tier Code Logic**:
```
if user opts into open tier:
    tier_code = "OPEN"
else:
    tier_code = f"{sex_code}-{age_bracket}-{fitness_code}"
    # Example: M-30-39-INT, F-18-29-BEG, M-60+-ADV
```

**State Transitions**:
- Profile creation is one-time (required step after email verification)
- Profile updates trigger tier recalculation
- Tier changes move user to new leaderboard (historical rankings preserved)

### TrackerConnection

**Purpose**: Stores OAuth credentials and sync status for fitness tracker integrations via Terra API.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| connection_id | RAW(16) | PK | UUID unique identifier |
| user_id | RAW(16) | FK | Parent user |
| provider | VARCHAR2(20) | CHECK constraint | apple_health, google_fit, fitbit |
| is_primary | NUMBER(1) | DEFAULT 0 | Boolean: preferred tracker for deduplication |
| terra_user_id | VARCHAR2(255) | NOT NULL | Terra API user identifier |
| access_token | VARCHAR2(2000) | ENCRYPTED | Terra OAuth access token (AES-256-GCM) |
| refresh_token | VARCHAR2(2000) | ENCRYPTED | Terra OAuth refresh token |
| token_expires_at | TIMESTAMP | NOT NULL | Token expiration (proactive refresh at -1 hour) |
| last_sync_at | TIMESTAMP | NULL | Most recent successful sync |
| sync_status | VARCHAR2(20) | CHECK constraint | pending, syncing, success, error |
| error_message | VARCHAR2(500) | NULL | Last error details for debugging |
| created_at | TIMESTAMP | NOT NULL, UTC | Connection timestamp |
| updated_at | TIMESTAMP | NOT NULL, UTC | Last modification timestamp |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Relationships**:
- Many-to-One to User
- One-to-Many to Activities (source attribution)

**Business Rules**:
- User can have max one connection per provider (UNIQUE constraint on user_id, provider)
- Exactly one connection must be marked as primary (application-level validation)
- Tokens encrypted at rest using AES-256-GCM with key from OCI Vault (v1.0) or environment (dev)
- Sync status transitions: pending → syncing → success/error
- Error status triggers retry with exponential backoff (max 3 retries)

**State Transitions**:
- pending → syncing: Sync job started
- syncing → success: Sync completed, activities imported
- syncing → error: Sync failed (token expired, API error, rate limit)
- error → syncing: Retry attempt
- Any state → pending: User-initiated manual sync

### Activity

**Purpose**: Normalized fitness activity data synced from trackers. Base unit for point earning calculation.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| activity_id | RAW(16) | PK | UUID unique identifier |
| user_id | RAW(16) | FK, indexed | Parent user |
| connection_id | RAW(16) | FK | Source tracker connection |
| external_id | VARCHAR2(255) | NULL | Terra API activity ID (deduplication) |
| activity_type | VARCHAR2(30) | CHECK constraint | steps, workout, active_minutes |
| start_time | TIMESTAMP | NOT NULL, indexed | Activity start (UTC) |
| end_time | TIMESTAMP | NULL | Activity end (UTC) |
| duration_minutes | NUMBER(5) | NULL | Calculated duration |
| intensity | VARCHAR2(20) | CHECK constraint | light, moderate, vigorous (based on HR) |
| metrics | JSON | NOT NULL | Flexible metrics object (see below) |
| points_earned | NUMBER(5) | DEFAULT 0 | Calculated points for this activity |
| processed | NUMBER(1) | DEFAULT 0 | Boolean: points awarded and balance updated |
| created_at | TIMESTAMP | NOT NULL, UTC | Sync timestamp |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Metrics JSON Structure**:
```json
{
  "steps": 5000,
  "calories": 250,
  "distance_meters": 4000,
  "heart_rate_avg": 120,
  "heart_rate_max": 145,
  "elevation_gain_meters": 50,
  "source_specific": {
    "fitbit_activity_id": "12345"
  }
}
```

**Relationships**:
- Many-to-One to User
- Many-to-One to TrackerConnection (source attribution)

**Business Rules**:
- Unique constraint on (user_id, connection_id, external_id) prevents duplicate imports
- Activities with overlapping time windows from multiple trackers: keep only primary tracker's data
- Point calculation applies tier-adjusted rate table
- Daily cap: 1,000 points max per user per day (enforced in points_service)
- Processed flag set only after successful PointTransaction creation
- Points earned stored denormalized for audit/debugging (source of truth is PointTransaction)

**Point Calculation Logic** (tier-adjusted):
```python
base_rate = RATE_TABLE[activity_type][intensity]
tier_multiplier = TIER_MULTIPLIERS[tier_code]  # Beginner: 1.2, Intermediate: 1.0, Advanced: 0.9, OPEN: 1.0
points = base_rate * quantity * tier_multiplier

# Example: 30 active minutes (vigorous) for beginner (M-18-29-BEG)
# Base rate: 3 points/min (vigorous)
# Tier multiplier: 1.2 (beginner)
# Points: 3 * 30 * 1.2 = 108 points
```

**State Transitions**:
- processed=0 → processed=1: Points calculated and awarded (irreversible for audit)

### PointTransaction

**Purpose**: Immutable audit log of all point balance changes (earn, spend, admin adjustments).

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| transaction_id | RAW(16) | PK | UUID unique identifier |
| user_id | RAW(16) | FK, indexed | Parent user |
| transaction_type | VARCHAR2(20) | CHECK constraint | earn, spend, adjust, expire |
| amount | NUMBER(10) | NOT NULL | Signed integer (positive=earn, negative=spend) |
| balance_after | NUMBER(10) | NOT NULL, >= 0 | User's point balance after this transaction |
| reference_type | VARCHAR2(30) | NULL | activity, ticket_purchase, admin_adjust |
| reference_id | RAW(16) | NULL | ID of related entity (activity_id, ticket_id, etc.) |
| description | VARCHAR2(255) | NOT NULL | Human-readable description |
| created_at | TIMESTAMP | NOT NULL, UTC | Transaction timestamp |

**Relationships**:
- Many-to-One to User
- Optional references to Activity, Ticket, or other entities

**Business Rules**:
- Transactions are immutable (no updates or deletes)
- balance_after must equal previous transaction's balance_after + amount
- Transaction creation and user.point_balance update must be atomic (database transaction)
- Negative balance prevented by CHECK constraint on user.point_balance
- Earn transactions require reference_id (activity_id or bonus type)
- Spend transactions require reference_id (ticket_id)
- Admin adjustments require audit trail (admin_user_id in description or separate audit table)

**Transaction Types**:
- **earn**: Activity points, bonuses (daily goal, streak, etc.)
- **spend**: Ticket purchases
- **adjust**: Admin manual adjustment (corrections, compensation)
- **expire**: Point expiration (v1.1 feature if implemented)

### Drawing

**Purpose**: Configuration and state for sweepstakes prize drawings.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| drawing_id | RAW(16) | PK | UUID unique identifier |
| drawing_type | VARCHAR2(20) | CHECK constraint | daily, weekly, monthly, annual |
| name | VARCHAR2(255) | NOT NULL | Display name (e.g., "Daily Drawing - Jan 15, 2026") |
| description | CLOB | NULL | Detailed description (Markdown supported) |
| ticket_cost_points | NUMBER(6) | NOT NULL, > 0 | Cost per ticket |
| drawing_time | TIMESTAMP | NOT NULL | Scheduled execution time (UTC) |
| ticket_sales_close | TIMESTAMP | NOT NULL | Sales cutoff (5 min before drawing_time) |
| eligibility | JSON | NOT NULL | Eligibility rules (see below) |
| status | VARCHAR2(20) | CHECK constraint | draft, scheduled, open, closed, completed, cancelled |
| total_tickets | NUMBER(10) | DEFAULT 0 | Total tickets sold (cached for odds display) |
| random_seed | VARCHAR2(255) | NULL | CSPRNG seed used for winner selection (audit) |
| created_by | RAW(16) | FK to users | Admin who created drawing |
| created_at | TIMESTAMP | NOT NULL, UTC | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, UTC | Last modification timestamp |
| completed_at | TIMESTAMP | NULL | Actual execution timestamp |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Eligibility JSON Structure**:
```json
{
  "user_type": "all",  // "all", "premium"
  "min_account_age_days": 7,
  "excluded_states": [],  // Empty or list of state codes
  "tier_codes": []  // Empty = all tiers, or specific list
}
```

**Relationships**:
- One-to-Many to Prizes (drawing configuration includes prize list)
- One-to-Many to Tickets (user entries)
- Many-to-One to User (created_by admin)

**Business Rules**:
- Ticket sales close time must be >= 5 minutes before drawing time
- Status transitions enforce workflow (see below)
- Drawing execution at drawing_time is idempotent (scheduled job checks completed_at)
- Winner selection uses CSPRNG from OCI Vault (Python secrets module for dev)
- Random seed stored for third-party audit verification

**State Transitions**:
- draft → scheduled: Admin approval, passes validation
- scheduled → open: Current time >= scheduled open time (automatic via cron)
- open → closed: Current time >= ticket_sales_close (automatic via cron)
- closed → completed: Drawing execution job finishes successfully
- Any state → cancelled: Admin cancellation (tickets refunded)

**Drawing Execution Algorithm**:
```python
# Executed at drawing_time by scheduled worker
1. Set status = 'closed' if still 'open' (safety)
2. Create immutable snapshot of all tickets for this drawing
3. Assign sequential ticket numbers (1 to N)
4. For each prize (rank order):
   a. Generate random number in range [1, N] using CSPRNG
   b. Select winning ticket by ticket number
   c. Mark ticket as winner, record prize_id
   d. Create PrizeFulfillment record
   e. Send winner notification
5. Set status = 'completed', store random_seed, set completed_at
6. Publish results (public endpoint, email to all participants)
```

### Prize

**Purpose**: Reward item associated with a drawing, provided by sponsor.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| prize_id | RAW(16) | PK | UUID unique identifier |
| drawing_id | RAW(16) | FK, indexed | Parent drawing |
| sponsor_id | RAW(16) | FK | Sponsor providing prize |
| rank | NUMBER(3) | NOT NULL | Prize tier (1=grand prize, 2=second, etc.) |
| name | VARCHAR2(255) | NOT NULL | Prize name (e.g., "$50 Amazon Gift Card") |
| description | CLOB | NULL | Detailed prize description |
| value_usd | NUMBER(10,2) | NOT NULL, > 0 | Approximate retail value (ARV) |
| quantity | NUMBER(3) | DEFAULT 1 | Number of prizes at this rank (typically 1) |
| fulfillment_type | VARCHAR2(20) | CHECK constraint | digital, physical |
| image_url | VARCHAR2(500) | NULL | Prize image (hosted in OCI Object Storage) |
| created_at | TIMESTAMP | NOT NULL, UTC | Creation timestamp |

**Relationships**:
- Many-to-One to Drawing
- Many-to-One to Sponsor
- One-to-Many to PrizeFulfillments (after drawing completion)

**Business Rules**:
- Rank must be unique within drawing (multiple prizes at same rank not supported in MVP)
- Physical prizes require shipping address from winner
- Digital prizes delivered via email (gift card codes, etc.)
- Value USD used for tax reporting (1099 threshold TBD by legal)

### Ticket

**Purpose**: User entry into a sweepstakes drawing. One ticket = one chance to win.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| ticket_id | RAW(16) | PK | UUID unique identifier |
| drawing_id | RAW(16) | FK, indexed | Parent drawing |
| user_id | RAW(16) | FK, indexed | Ticket purchaser |
| ticket_number | NUMBER(10) | NULL | Sequential number assigned at sales close |
| purchase_transaction_id | RAW(16) | FK | PointTransaction for this purchase (spend) |
| is_winner | NUMBER(1) | DEFAULT 0 | Boolean: selected as winner |
| prize_id | RAW(16) | FK, NULL | Prize won (if is_winner=1) |
| created_at | TIMESTAMP | NOT NULL, UTC | Purchase timestamp |

**Relationships**:
- Many-to-One to Drawing
- Many-to-One to User
- One-to-One to PointTransaction (purchase record)
- Many-to-One to Prize (winner association)

**Business Rules**:
- Tickets created in batch during purchase (user can buy N tickets in one transaction)
- ticket_number assigned at drawing close time (immutable snapshot)
- Ticket purchase validates: user eligibility, sufficient points, drawing is open
- Ticket refunds (drawing cancellation) create new PointTransaction (adjust type)
- is_winner and prize_id set during drawing execution (atomic update)

### PrizeFulfillment

**Purpose**: Tracks prize delivery workflow from winner notification to delivery confirmation.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| fulfillment_id | RAW(16) | PK | UUID unique identifier |
| ticket_id | RAW(16) | FK, UNIQUE | Winning ticket |
| prize_id | RAW(16) | FK | Prize being fulfilled |
| user_id | RAW(16) | FK, indexed | Winner |
| status | VARCHAR2(30) | CHECK constraint | pending, winner_notified, address_confirmed, shipped, delivered, forfeited |
| shipping_address | JSON | NULL | Address object (for physical prizes) |
| tracking_number | VARCHAR2(100) | NULL | Carrier tracking number |
| carrier | VARCHAR2(50) | NULL | Shipping carrier name |
| notes | CLOB | NULL | Admin notes, special instructions |
| notified_at | TIMESTAMP | NULL | Winner notification sent timestamp |
| address_confirmed_at | TIMESTAMP | NULL | Winner provided/confirmed address |
| shipped_at | TIMESTAMP | NULL | Admin marked as shipped |
| delivered_at | TIMESTAMP | NULL | Confirmed delivery |
| forfeit_at | TIMESTAMP | NULL | Scheduled forfeit time (14 days from notified_at) |
| created_at | TIMESTAMP | NOT NULL, UTC | Creation timestamp (drawing completion) |
| updated_at | TIMESTAMP | NOT NULL, UTC | Last modification timestamp |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Shipping Address JSON Structure**:
```json
{
  "full_name": "Jane Doe",
  "address_line1": "123 Main St",
  "address_line2": "Apt 4B",
  "city": "Austin",
  "state": "TX",
  "postal_code": "78701",
  "country": "US",
  "phone": "+1-555-123-4567"
}
```

**Relationships**:
- One-to-One to Ticket (winning ticket)
- Many-to-One to Prize
- Many-to-One to User (winner)

**Business Rules**:
- Created automatically when winner selected during drawing execution
- Winner notified immediately (email + in-app notification)
- Winner has 7 days to provide address (warning at day 6)
- Winner has 14 days total to claim prize (forfeit if no response)
- Forfeited prizes returned to sponsor or re-drawn (per sponsor agreement)
- Digital prizes skip address_confirmed state (straight to delivered)

**State Transitions**:
- pending → winner_notified: Notification sent successfully
- winner_notified → address_confirmed: Winner provides/confirms address
- winner_notified → forfeited: 14 days elapsed, no response
- address_confirmed → shipped: Admin enters tracking number
- shipped → delivered: Carrier confirms delivery or admin marks delivered
- Any state → forfeited: Winner explicitly declines or timeout

### Sponsor

**Purpose**: Organization providing prizes for drawings. MVP uses placeholder sponsors for gift cards.

**Key Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| sponsor_id | RAW(16) | PK | UUID unique identifier |
| name | VARCHAR2(255) | NOT NULL, UNIQUE | Sponsor name (e.g., "Amazon", "FitTrack Platform") |
| contact_name | VARCHAR2(255) | NULL | Primary contact person |
| contact_email | VARCHAR2(255) | NULL | Contact email |
| contact_phone | VARCHAR2(20) | NULL | Contact phone |
| website_url | VARCHAR2(500) | NULL | Sponsor website |
| logo_url | VARCHAR2(500) | NULL | Logo image (hosted in OCI Object Storage) |
| status | VARCHAR2(20) | CHECK constraint | active, inactive |
| notes | CLOB | NULL | Internal notes, partnership details |
| created_at | TIMESTAMP | NOT NULL, UTC | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, UTC | Last modification timestamp |
| version | NUMBER(10) | DEFAULT 1 | Optimistic lock version |

**Relationships**:
- One-to-Many to Prizes

**Business Rules**:
- MVP uses "FitTrack Platform" sponsor for all gift card prizes
- v1.1+ adds sponsor self-service portal for prize submission
- Inactive sponsors cannot be assigned to new prizes (existing prizes unaffected)

## Core Workflows

### User Registration & Onboarding

**Purpose**: New user account creation with age/state verification and fitness profile setup.

**Actors**: Anonymous user (guest)

**Preconditions**:
- User is 18+ years old
- User resides in eligible state
- Email address not already registered

**Flow**:
1. User submits registration form:
   - Email, password (12+ chars, complexity requirements)
   - Date of birth (DOB)
   - State of residence
   - Acceptance of Terms of Service and Sweepstakes Rules
2. System validates input:
   - Email format and uniqueness
   - Password strength (bcrypt cost factor 12)
   - Age >= 18 years (calculated from DOB)
   - State in eligible list (excluded: NY, FL, RI pending legal review)
3. System creates User record (status=pending, role=user)
4. System sends verification email with unique token (expires in 24 hours)
5. User clicks verification link in email
6. System validates token and updates User (email_verified=1, status=active)
7. User redirected to profile completion form:
   - Display name (unique, alphanumeric + underscore)
   - Biological sex (for tier assignment)
   - Fitness level (beginner/intermediate/advanced)
   - Optional: goals, height, weight
   - Option to select "Open" tier (compete with all demographics)
8. System creates Profile record and calculates tier_code
9. User redirected to tracker connection page (optional step, can skip)

**Postconditions**:
- User record exists with status=active, email_verified=1
- Profile record exists with calculated tier_code
- User can log in and access platform features

**Exception Handling**:
- Underage (< 18): Registration rejected with error message, no account created
- Ineligible state: Registration rejected with message about state restrictions
- Duplicate email: Error message, suggest password reset if user forgot account
- Email delivery failure: Log error, allow retry via "resend verification email"
- Token expired: Generate new token and resend email

**Related Entities**: User, Profile

**Security Considerations**:
- Password hashed with bcrypt before storage (never store plaintext)
- Verification token cryptographically random, single-use, time-limited
- Rate limiting on registration endpoint (max 5 attempts per IP per hour)
- CAPTCHA on registration form (v1.1 to prevent bot accounts)

### Fitness Tracker Connection (OAuth Flow)

**Purpose**: Connect user's fitness tracker account to enable automatic activity syncing via Terra API.

**Actors**: Authenticated user

**Preconditions**:
- User is logged in
- User has account with Apple Health, Google Fit, or Fitbit
- Terra API credentials configured (client ID, client secret)

**Flow**:
1. User clicks "Connect [Provider]" button in app
2. System initiates Terra OAuth flow:
   - Calls Terra API `/auth/generateWidgetSession` endpoint
   - Receives widget session token and authorization URL
3. System redirects user to Terra's authentication widget
4. User authenticates with provider (Apple, Google, or Fitbit)
5. User grants FitTrack access to fitness data (scopes: activity, sleep, body, nutrition)
6. Provider redirects back to FitTrack callback URL with authorization code
7. System exchanges authorization code for Terra user ID and access token:
   - Calls Terra API `/auth/developer` endpoint
   - Receives terra_user_id, access_token, refresh_token, expires_in
8. System encrypts tokens (AES-256-GCM) and creates TrackerConnection record:
   - provider, terra_user_id, encrypted tokens, expiration
   - is_primary = 1 if this is user's first connection, else 0
   - sync_status = pending
9. System triggers immediate sync job for initial data fetch
10. User redirected to dashboard with success message

**Postconditions**:
- TrackerConnection record exists with valid encrypted tokens
- User has primary tracker designated (for deduplication)
- Initial sync job queued in Celery

**Exception Handling**:
- User denies permission: Redirect with message, no connection created
- OAuth error (invalid code, timeout): Log error, display user-friendly message, allow retry
- Terra API error: Log full error details, display generic message, alert admin
- Duplicate connection (user, provider): Error message, suggest disconnecting old connection first
- Token encryption failure: Critical error, log and alert, abort connection

**Related Entities**: User, TrackerConnection

**Security Considerations**:
- OAuth tokens encrypted at rest using AES-256-GCM
- Encryption key stored in environment variable (dev) or OCI Vault (production)
- State parameter in OAuth flow prevents CSRF attacks
- Tokens never logged or exposed in API responses
- Token refresh handled proactively (refresh 1 hour before expiration)

### Activity Sync & Point Earning

**Purpose**: Periodic background job that fetches new activities from Terra API, normalizes data, calculates points with tier adjustments, and updates user balance.

**Actors**: Celery worker (system)

**Preconditions**:
- TrackerConnection exists with valid tokens
- Current time >= last_sync_at + 15 minutes (sync interval)
- Terra API available

**Flow**:
1. Scheduled Celery task (every 15 minutes) selects users due for sync
2. For each user's TrackerConnection:
   a. Check token expiration; refresh if needed (< 1 hour remaining)
   b. Update sync_status = syncing
   c. Call Terra API `/data/activity` endpoint with date range (last_sync_at to now)
   d. Terra returns activity data in normalized format
3. For each activity in response:
   a. Check for duplicate (user_id, connection_id, external_id)
   b. If duplicate from non-primary tracker, skip (deduplication rule)
   c. Normalize activity data to internal format:
      - activity_type (steps, workout, active_minutes)
      - start_time, end_time, duration
      - intensity (light, moderate, vigorous based on heart rate)
      - metrics JSON (steps, calories, distance, heart rate, etc.)
4. Calculate tier-adjusted points for each activity:
   a. Get user's tier_code from Profile
   b. Lookup tier multiplier (beginner: 1.2, intermediate: 1.0, advanced: 0.9, OPEN: 1.0)
   c. Apply rate table: base_rate = RATE_TABLE[activity_type][intensity]
   d. Calculate: points = base_rate * quantity * tier_multiplier
   e. Check daily cap: if user's today_points + points > 1000, truncate to 1000
5. Create Activity records with calculated points_earned (processed=0)
6. For each Activity, create PointTransaction in database transaction:
   a. transaction_type = earn
   b. amount = points_earned
   c. balance_after = user.point_balance + amount
   d. reference_type = activity, reference_id = activity_id
   e. Update user.point_balance atomically
   f. Set activity.processed = 1
7. Update TrackerConnection: last_sync_at = now, sync_status = success
8. Trigger leaderboard update job (debounced, max once per minute)

**Rate Table (Base Points)**:
| Activity Type | Light | Moderate | Vigorous |
|---------------|-------|----------|----------|
| Active Minutes | 1 pt/min | 2 pts/min | 3 pts/min |
| Steps | N/A | 10 pts/1000 steps | N/A |
| Workout (20+ min) | N/A | +50 bonus | +50 bonus |

**Tier Multipliers**:
| Tier | Multiplier | Rationale |
|------|------------|-----------|
| Beginner | 1.2 | Encourages new users, compensates for lower activity volume |
| Intermediate | 1.0 | Baseline |
| Advanced | 0.9 | Normalizes higher activity volume |
| OPEN | 1.0 | No adjustment for mixed competition |

**Postconditions**:
- Activity records created for all new activities
- PointTransaction records created for all earned points
- user.point_balance updated to reflect new points
- TrackerConnection.last_sync_at updated
- Leaderboard refresh queued

**Exception Handling**:
- Token expired: Attempt token refresh; if fails, set sync_status = error, notify user to reconnect
- Terra API rate limit: Exponential backoff, retry after delay
- Terra API error (500, timeout): Log error, set sync_status = error, retry with exponential backoff (max 3 attempts)
- Activity parsing error: Log malformed activity data, skip this activity, continue with others
- Duplicate activity: Skip silently (expected behavior)
- Daily cap reached: Truncate points, create PointTransaction with truncated amount, add note in description

**Related Entities**: TrackerConnection, Activity, PointTransaction, User, Profile

**Security Considerations**:
- Token refresh uses encrypted refresh_token
- All API calls use HTTPS
- Failed token refresh triggers user notification (email) to reconnect
- Sync errors logged with correlation ID for debugging (no PII in logs)

### Ticket Purchase & Drawing Entry

**Purpose**: User spends points to purchase tickets for a sweepstakes drawing, increasing their chance to win.

**Actors**: Authenticated user

**Preconditions**:
- User is logged in
- Drawing exists with status = open
- Current time < ticket_sales_close
- User meets eligibility criteria (account age, user type, tier, state)
- User has sufficient point balance

**Flow**:
1. User navigates to drawings list, sees available drawings with details:
   - Prize description, ARV, sponsor
   - Ticket cost, total tickets sold, user's current tickets
   - Odds calculation: 1 in (total_tickets / user_tickets)
   - Closing time countdown
2. User clicks "Buy Tickets" button, opens purchase modal
3. User selects quantity (default 1, max limited by point balance)
4. UI shows:
   - Total cost = quantity * ticket_cost_points
   - Remaining balance = user.point_balance - total_cost
   - Current odds vs. odds after purchase
5. User clicks "Confirm Purchase"
6. API validates request:
   - Drawing status is open
   - Current time < ticket_sales_close
   - User meets eligibility criteria (check drawing.eligibility JSON)
   - user.point_balance >= total_cost
7. System creates database transaction:
   a. Create PointTransaction:
      - transaction_type = spend
      - amount = -(quantity * ticket_cost_points)
      - balance_after = user.point_balance + amount (negative spend)
      - reference_type = ticket_purchase
   b. Update user.point_balance (atomic decrement)
   c. Create Ticket records (quantity count):
      - drawing_id, user_id
      - purchase_transaction_id (reference)
      - ticket_number = NULL (assigned at drawing close)
   d. Increment drawing.total_tickets (cached count for UI)
   e. Commit transaction
8. API returns success response with new balance and ticket count
9. UI updates to show confirmation and new balance

**Postconditions**:
- PointTransaction record created (spend type)
- Ticket records created (N tickets for drawing)
- user.point_balance decreased by total cost
- drawing.total_tickets incremented
- User has entries in the drawing

**Exception Handling**:
- Insufficient points: Return 400 error with current balance and required amount
- Drawing closed: Return 403 error, refresh drawing list UI
- Eligibility check fails: Return 403 error with specific reason (account age, tier, state, user type)
- Concurrent purchase causes insufficient balance: Transaction rollback, return 409 conflict, suggest retry
- Database transaction fails: Rollback all changes, return 500 error, log incident

**Related Entities**: User, Drawing, Ticket, PointTransaction

**Security Considerations**:
- Eligibility validation server-side (never trust client)
- Atomic transaction prevents race conditions (multiple purchases)
- Rate limiting on purchase endpoint (max 10 purchases per user per minute)
- Ticket creation and point deduction must be atomic (rollback if any step fails)

### Drawing Execution & Winner Selection

**Purpose**: Automated job that executes scheduled drawings, randomly selects winners using CSPRNG, and initiates prize fulfillment.

**Actors**: Celery worker (system)

**Preconditions**:
- Drawing exists with status = closed
- Current time >= drawing_time
- Drawing has at least one ticket sold

**Flow**:
1. Scheduled Celery task runs every minute, queries drawings:
   - WHERE status = closed AND drawing_time <= NOW() AND completed_at IS NULL
2. For each drawing:
   a. Begin database transaction
   b. Set status = 'executing' (prevent duplicate execution)
   c. Commit transaction
3. Fetch all tickets for this drawing (immutable snapshot)
4. Assign sequential ticket numbers (1 to N):
   - ORDER BY created_at, ticket_id (deterministic ordering)
   - UPDATE tickets SET ticket_number = row_number WHERE drawing_id = X
5. Generate CSPRNG seed for audit:
   - Use Python secrets.token_hex(32) for random seed
   - Store in drawing.random_seed
6. For each prize (ORDER BY rank ASC):
   a. Generate random winning ticket number in range [1, N]:
      - Use secrets.SystemRandom().randint(1, N)
   b. Fetch ticket with that ticket_number
   c. Update ticket: is_winner = 1, prize_id = prize.prize_id
   d. Create PrizeFulfillment record:
      - ticket_id, prize_id, user_id (from ticket)
      - status = pending
   e. Send winner notification (async task):
      - Email to user.email
      - In-app notification
   f. Set fulfillment.notified_at = NOW(), status = winner_notified
7. Update drawing: status = completed, completed_at = NOW()
8. Commit transaction
9. Publish results (public endpoint):
   - Winner usernames, prize names, winning ticket numbers
   - Total tickets, total participants
10. Send participation notification to all non-winners (async batch task):
    - "Thanks for participating, drawing results available"

**CSPRNG Implementation**:
```python
import secrets

# Generate cryptographically secure random number
rng = secrets.SystemRandom()
winning_ticket_number = rng.randint(1, total_tickets)

# Store seed for audit (demonstration; actual CSPRNG doesn't expose seed)
random_seed = secrets.token_hex(32)  # 64-char hex string
```

**Postconditions**:
- Drawing status = completed
- Ticket records have ticket_number assigned (1 to N)
- Winner tickets marked (is_winner = 1, prize_id set)
- PrizeFulfillment records created for all winners
- Winners notified via email and in-app
- Drawing results published publicly
- random_seed stored for audit

**Exception Handling**:
- No tickets sold: Skip drawing, set status = cancelled, send notification to admins
- CSPRNG failure: Critical error, log and alert, abort drawing, set status = error
- Winner notification failure: Log error, mark fulfillment.notified_at = NULL for retry
- Transaction failure: Rollback, set drawing.status = error, alert admin for manual intervention
- Duplicate execution (rare race condition): EXECUTING status prevents; if occurs, log warning and exit

**Related Entities**: Drawing, Prize, Ticket, PrizeFulfillment, User

**Security Considerations**:
- CSPRNG ensures unpredictable, unbiased winner selection
- random_seed stored for third-party audit verification
- Drawing execution code audited for fairness
- Ticket number assignment deterministic and transparent
- All operations logged with correlation ID
- Admin cannot influence winner selection (no manual selection)

### Prize Fulfillment Workflow

**Purpose**: Manage prize delivery from winner notification through shipping to delivery confirmation.

**Actors**: Winner (user), Admin

**Preconditions**:
- PrizeFulfillment record exists with status = winner_notified
- Winner has been notified via email and in-app notification

**Flow (Physical Prize)**:
1. Winner receives email with link to prize claim page
2. Winner clicks link, directed to "Claim Your Prize" form
3. Winner provides/confirms shipping address:
   - Full name, address line 1, line 2, city, state, ZIP, phone
   - System validates address format (basic validation, no USPS verification in MVP)
4. Winner submits form
5. System updates PrizeFulfillment:
   - shipping_address = JSON object
   - address_confirmed_at = NOW()
   - status = address_confirmed
6. System notifies admin (email to admin team):
   - Prize to ship, winner details, shipping address
7. Admin manually ships prize (external process)
8. Admin logs into admin panel, navigates to fulfillments list
9. Admin selects fulfillment, enters tracking information:
   - Carrier (USPS, UPS, FedEx, etc.)
   - Tracking number
10. System updates PrizeFulfillment:
    - tracking_number, carrier
    - shipped_at = NOW()
    - status = shipped
11. System notifies winner (email):
    - "Your prize has shipped! Track: [tracking_link]"
12. Admin or automated job (v1.1 with carrier API) confirms delivery
13. System updates PrizeFulfillment:
    - delivered_at = NOW()
    - status = delivered
14. Fulfillment complete

**Flow (Digital Prize)**:
1. Winner receives email with gift card code or redemption link
2. PrizeFulfillment status: pending → winner_notified → delivered (skip address step)
3. delivered_at = NOW()
4. Fulfillment complete

**Forfeit Flow**:
1. Winner does not respond within 7 days: System sends reminder email
2. Winner does not respond within 14 days:
   - System updates PrizeFulfillment: status = forfeited
   - System creates audit log entry
   - Admin notified to return prize to sponsor or re-draw (per sponsor agreement)

**Postconditions**:
- PrizeFulfillment status = delivered (success) or forfeited (failure)
- Winner received prize (physical or digital)
- Shipping details recorded for audit

**Exception Handling**:
- Invalid shipping address: Winner notified to correct address, status = address_invalid
- Address correction timeout (3 days): Send reminder, extend deadline by 3 days (max once)
- Shipping failure (lost package): Admin creates replacement fulfillment, marks original as error
- Winner explicitly declines prize: Set status = forfeited, record reason in notes

**Related Entities**: PrizeFulfillment, Ticket, Prize, User

**Security Considerations**:
- Shipping address stored in JSON, encrypted at rest (database TDE)
- PII access logged (admin views shipping address)
- Tracking numbers visible only to winner and admin
- Gift card codes sent via secure email (no plaintext in database after delivery)

## User Roles and Permissions

### Role Hierarchy

FitTrack uses a flat role hierarchy (no role inheritance):
- **guest**: Anonymous users (pre-registration)
- **user**: Registered free tier users
- **premium**: Paid subscribers (v1.1 feature)
- **admin**: Platform administrators

### Guest (Unauthenticated)

**Description**: Anonymous visitors exploring the platform before registration.

**Permissions**:

| Resource | Create | Read | Update | Delete | Special |
|----------|--------|------|--------|--------|---------|
| Landing pages | ✗ | ✓ | ✗ | ✗ | Can view public marketing pages |
| Registration | ✓ | ✗ | ✗ | ✗ | Can create account |
| Login | ✓ | ✗ | ✗ | ✗ | Can authenticate |
| Drawings | ✗ | ✓ | ✗ | ✗ | Can view public drawing results |
| Leaderboards | ✗ | ✗ | ✗ | ✗ | Must register to view |

**Restrictions**:
- Cannot access any authenticated endpoints
- Cannot purchase tickets or earn points
- Cannot view detailed user profiles

**Data Scope**: Public data only (landing pages, terms of service, public drawing results)

### User (Free Tier)

**Description**: Registered users on the free tier. This is the default role after registration.

**Permissions**:

| Resource | Create | Read | Update | Delete | Special |
|----------|--------|------|--------|--------|---------|
| Own profile | ✗ | ✓ | ✓ | ✗ | Can update display name, goals, fitness level |
| Own account | ✗ | ✓ | ✓ | ✗ | Can update email, password |
| Tracker connections | ✓ | ✓ | ✗ | ✓ | Can connect/disconnect trackers |
| Own activities | ✗ | ✓ | ✗ | ✗ | Read-only (synced from trackers) |
| Own point transactions | ✗ | ✓ | ✗ | ✗ | Read-only audit log |
| Drawings (all user types) | ✗ | ✓ | ✗ | ✗ | Can view all open drawings for "all" user type |
| Tickets | ✓ | ✓ | ✗ | ✗ | Can purchase, cannot refund |
| Leaderboards | ✗ | ✓ | ✗ | ✗ | Can view own tier and other tiers |
| Other users (public) | ✗ | ✓ | ✗ | ✗ | Can view public profiles (display name, tier, rank) |
| Prize fulfillments | ✗ | ✓ | ✓ | ✗ | Can view own wins, provide shipping address |

**Restrictions**:
- Cannot access premium-only drawings (v1.1)
- Cannot access admin endpoints
- Cannot modify point balance directly (earn through activities, spend on tickets)
- Cannot modify other users' data
- Cannot cancel/refund tickets after purchase

**Data Scope**: Own data + public data (leaderboards, drawing results, other users' public profiles)

### Premium (Paid Subscriber - v1.1)

**Description**: Users who pay for premium subscription. Inherits all user permissions plus premium-specific features.

**Permissions**:

| Resource | Create | Read | Update | Delete | Special |
|----------|--------|------|--------|--------|---------|
| All User permissions | ✓ | ✓ | ✓ | ✓ | Inherits all free tier permissions |
| Premium drawings | ✗ | ✓ | ✗ | ✗ | Can view and enter premium-only drawings |
| Professional services | ✓ | ✓ | ✓ | ✓ | Can book sessions with coaches/nutritionists |

**Restrictions**:
- Same as user role, except premium drawing access
- Cannot access admin functions

**Data Scope**: Own data + public data + premium features

**Notes**: Premium role is v1.1 feature. MVP defers premium subscription, but database schema includes role and premium_expires_at for future use.

### Admin (Platform Administrator)

**Description**: FitTrack staff members with full platform access.

**Permissions**:

| Resource | Create | Read | Update | Delete | Special |
|----------|--------|------|--------|--------|---------|
| Users | ✗ | ✓ | ✓ | ✗ | Can suspend/ban, adjust points, view all details |
| Drawings | ✓ | ✓ | ✓ | ✓ | Full CRUD, can execute drawings manually |
| Sponsors | ✓ | ✓ | ✓ | ✗ | Full CRUD except delete (soft delete via status) |
| Prizes | ✓ | ✓ | ✓ | ✓ | Can add/edit prizes for drawings |
| Fulfillments | ✗ | ✓ | ✓ | ✗ | Can update status, enter tracking, mark delivered |
| Point transactions | ✓ | ✓ | ✗ | ✗ | Can create manual adjustments, cannot edit existing |
| Analytics | ✗ | ✓ | ✗ | ✗ | Access to analytics dashboards |
| System logs | ✗ | ✓ | ✗ | ✗ | Can view audit logs, error logs |

**Restrictions**:
- Cannot delete users (soft delete via status=banned)
- Cannot modify point transaction history (audit integrity)
- Cannot influence drawing winner selection (automated CSPRNG only)
- Two-factor authentication required (v1.1 security hardening)

**Data Scope**: All data across all users (read access), limited write access per permissions above

**Security Notes**:
- Admin actions logged in audit table (admin_user_id, action, entity, timestamp)
- Admin role assignment requires superadmin approval (manual process)
- Admin account compromise is critical security incident (immediate revocation process)

## API Design Standards

### URL Structure

- **Base path**: `/api/v1/`
- **Resource naming**: Plural nouns, kebab-case for multi-word resources
  - Examples: `/users`, `/drawings`, `/point-transactions`
- **Nested resources**: Only when true parent-child relationship exists
  - Good: `/drawings/{drawing_id}/tickets` (tickets belong to drawing)
  - Bad: `/users/{user_id}/leaderboards` (leaderboards are independent)
- **Query parameters**: Filtering, sorting, pagination
  - Filter: `?filter[status]=active&filter[type]=daily`
  - Sort: `?sort=-created_at,name` (descending created_at, ascending name)
  - Pagination: `?page=2&per_page=20` or `?cursor=xyz123`

### Request/Response Standards

**Successful Response (Single Resource)**:
```json
{
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "point_balance": 1250
  },
  "meta": {
    "request_id": "req_abc123xyz",
    "timestamp": "2026-01-15T14:30:00Z"
  }
}
```

**Collection Response**:
```json
{
  "data": [
    {"drawing_id": "...", "name": "Daily Drawing"},
    {"drawing_id": "...", "name": "Weekly Drawing"}
  ],
  "pagination": {
    "total": 156,
    "page": 2,
    "per_page": 20,
    "total_pages": 8,
    "next_cursor": "eyJpZCI6MTIzfQ",
    "prev_cursor": "eyJpZCI6OTB9"
  },
  "meta": {
    "request_id": "req_def456uvw",
    "timestamp": "2026-01-15T14:31:00Z"
  }
}
```

**Error Response (RFC 7807)**:
```json
{
  "type": "https://api.fittrack.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid data",
  "instance": "/api/v1/users/550e8400-e29b-41d4-a716-446655440000",
  "errors": [
    {
      "field": "email",
      "code": "invalid_format",
      "message": "Email must be a valid email address"
    },
    {
      "field": "password",
      "code": "too_weak",
      "message": "Password must be at least 12 characters with uppercase, lowercase, number, and special character"
    }
  ],
  "meta": {
    "request_id": "req_ghi789rst",
    "timestamp": "2026-01-15T14:32:00Z"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET or PUT request |
| 201 | Created | Successful POST request creating resource |
| 204 | No Content | Successful DELETE request (or PUT with no response body) |
| 400 | Bad Request | Malformed request syntax (invalid JSON, missing required field) |
| 401 | Unauthorized | Authentication required (missing or invalid token) |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (duplicate email, insufficient balance, drawing closed) |
| 422 | Unprocessable Entity | Validation error (semantically invalid data) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Temporary outage (maintenance, overload) |

### Pagination

**Cursor-based pagination** (recommended for large datasets, prevents page drift):
```
GET /api/v1/activities?cursor=eyJpZCI6MTIzfQ&limit=20
```

Response includes `next_cursor` and `prev_cursor` for navigation.

**Page-based pagination** (admin interfaces, smaller datasets):
```
GET /api/v1/admin/users?page=2&per_page=50
```

**Defaults**:
- `per_page` / `limit`: 20
- Maximum `per_page`: 100

### Filtering and Sorting

**Filtering** (query parameters with array notation):
```
GET /api/v1/drawings?filter[status]=open&filter[type]=daily,weekly
```

Backend interprets as:
```sql
WHERE status = 'open' AND type IN ('daily', 'weekly')
```

**Sorting** (comma-separated fields, `-` prefix for descending):
```
GET /api/v1/leaderboards/weekly?sort=-points_earned,display_name
```

Backend interprets as:
```sql
ORDER BY points_earned DESC, display_name ASC
```

### Authentication Header

All authenticated requests include JWT Bearer token:
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Token payload includes:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "email": "user@example.com",
  "role": "user",
  "exp": 1737824400,  // Expiration timestamp
  "iat": 1737820800   // Issued at timestamp
}
```

## Security Requirements

### Authentication

**Method**: JWT (JSON Web Tokens) with RS256 signing
- **Access token lifetime**: 30 minutes
- **Refresh token lifetime**: 7 days
- **Token storage (client)**:
  - Access token: Memory only (JavaScript variable, not localStorage)
  - Refresh token: HTTP-only, Secure, SameSite cookie
- **Token rotation**: Refresh token rotated on each use (v1.1 security enhancement)

**Implementation**:
- RS256 algorithm (asymmetric key pair)
- Private key stored in OCI Vault (production) or environment variable (dev)
- Public key used by API to verify signatures
- Token includes user_id, email, role, expiration

**Password Requirements**:
- Minimum 12 characters
- Must include: uppercase, lowercase, number, special character
- Bcrypt hashing with cost factor 12
- Password reset requires email verification (time-limited token)

**Account Lockout**:
- 5 failed login attempts → 15 minute lockout
- Progressive backoff: 6-10 fails → 30 min, 11+ → 1 hour
- Lockout bypass for admin accounts requires superadmin intervention

### Authorization

**Model**: Role-Based Access Control (RBAC)
- Roles: guest, user, premium, admin
- Permissions defined per role (see User Roles section)

**Enforcement**:
- API middleware checks JWT role for endpoint access
- Service layer checks fine-grained permissions (e.g., user can only update own profile)
- Default deny: All endpoints require authentication unless explicitly public

**Decorator Pattern**:
```python
@router.get("/admin/users")
@require_role("admin")  # Middleware checks JWT role
async def list_users(...):
    # Additional authorization logic if needed
    pass
```

### Data Protection

**Encryption at Rest**:
- Database: Oracle Transparent Data Encryption (TDE) enabled
- OAuth tokens: AES-256-GCM encryption before storage (python `cryptography` library)
- Encryption keys: Stored in OCI Vault (production), environment variable (dev)

**Encryption in Transit**:
- TLS 1.3 required for all API traffic (TLS 1.2 minimum)
- HSTS header enforces HTTPS
- Certificate from Let's Encrypt (auto-renewal via Certbot)

**PII Handling**:
- Email, DOB, shipping address classified as PII
- PII access logged in audit table (admin_audit_log)
- Data retention: Account lifetime + 30 days after deletion
- Data export: User can request JSON export via API (CCPA compliance)
- Data deletion: User can request account deletion (30-day soft delete, then hard delete)

**Sensitive Data Logging**:
- Never log passwords (even hashed), tokens, or PII
- Log only: user_id, request_id, endpoint, status code
- Example good log: `{"user_id": "550e...", "endpoint": "/api/v1/users/me", "status": 200}`
- Example bad log: `{"email": "user@example.com", "password_hash": "..."}`

### Input Validation

**Pydantic Schema Validation**:
- All API requests validated via Pydantic models
- Type checking, range validation, regex patterns
- Custom validators for business rules (e.g., age >= 18, state in eligible list)

**SQL Injection Prevention**:
- Parameterized queries only (SQLAlchemy handles this automatically)
- Never construct SQL strings with f-strings or concatenation
- ORM provides additional protection layer

**XSS Prevention**:
- Output encoding: FastAPI/Pydantic serializes JSON safely
- HTML test page uses DOMPurify for any user-generated content display
- Content-Security-Policy header restricts script sources

**File Upload Restrictions** (future feature for avatar images, prize images):
- Allowed types: JPEG, PNG, GIF (whitelist, check magic bytes)
- Max size: 5 MB
- Virus scanning via ClamAV (v1.1)
- Stored in OCI Object Storage (isolated from application server)

### Audit Logging

**What to Log**:
- All state-changing operations (CREATE, UPDATE, DELETE)
- Authentication events (login, logout, failed attempts)
- Admin actions (user suspension, point adjustments, drawing execution)
- Prize fulfillment status changes
- Security events (rate limit exceeded, suspicious activity)

**Log Format** (structured JSON):
```json
{
  "timestamp": "2026-01-15T14:30:00Z",
  "request_id": "req_abc123xyz",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "ticket_purchase",
  "resource_type": "ticket",
  "resource_id": "ticket_789...",
  "changes": {
    "drawing_id": "draw_456...",
    "quantity": 5,
    "points_spent": 500
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

**Log Retention**:
- Application logs: 90 days
- Audit logs (security, financial): 7 years (compliance requirement)
- Logs stored in OCI Logging service (searchable, alertable)

**Log Immutability**:
- Logs write-only (no updates or deletes)
- Tamper detection via checksums (v1.1)

### Secrets Management

**Development Environment**:
- `.env` file for local secrets (Git-ignored)
- Template `.env.example` committed with placeholder values
- Pre-commit hook prevents accidental secret commits (detect-secrets)

**Production Environment**:
- OCI Vault for secrets storage (database passwords, API keys, encryption keys)
- Application fetches secrets at startup via OCI SDK
- Secrets rotated quarterly (automated rotation for database credentials)

**API Keys**:
- Terra API credentials stored in OCI Vault
- Email service API key (SendGrid/SES) in OCI Vault
- Admin cannot view secrets in plain text (only masked values in UI)

### Rate Limiting

| User Type | Limit | Window | Penalty |
|-----------|-------|--------|---------|
| Anonymous | 10 req/min | 60 sec | 429 response, 1 min cooldown |
| Authenticated | 100 req/min | 60 sec | 429 response, 1 min cooldown |
| Admin | 500 req/min | 60 sec | 429 response |
| Ticket purchase | 10 req/min | 60 sec | 429 response, suspected abuse alert |

**Implementation**: Redis-based rate limiting (FastAPI Limiter library)

## Testing Strategy

### Test Pyramid

```
       /\
      /  \
     / E2E \      ~10% of tests (critical workflows)
    /------\
   /        \
  /Integration\  ~20% of tests (API + database)
 /------------\
/              \
|     Unit     | ~70% of tests (services, utils, business logic)
\______________/
```

### Coverage Requirements

| Component | Target | Rationale |
|-----------|--------|-----------|
| Business logic (services) | >90% | Critical for correctness, complex rules |
| Data layer (repositories) | >90% | Data integrity, query correctness |
| API layer (endpoints) | >85% | Input validation, auth/authz, error handling |
| Utilities | >90% | Reusable functions, edge cases |
| Models | >80% | Validation rules, constraints |
| Overall project | >80% | Acceptable balance of rigor and effort |

### Test Data Strategy

**factory_boy Factories**:
- One factory per entity model
- Faker providers for realistic data (names, emails, addresses)
- Sequences for unique fields (email, display_name)
- SubFactories for relationships (UserFactory → ProfileFactory)

**Deterministic Seeding**:
- `Faker.seed(12345)` for reproducible tests
- Random seed reset in `conftest.py` for each test

**Test Isolation**:
- Each test runs in database transaction (rollback after test)
- Session-scoped test database fixture (create once, rollback per test)
- pytest-xdist for parallel test execution (independent test isolation)

**Example Factory**:
```python
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    user_id = factory.LazyFunction(uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = factory.LazyFunction(lambda: bcrypt.hashpw(b"password123", bcrypt.gensalt()))
    email_verified = 1
    status = "active"
    role = "user"
    point_balance = 500
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    version = 1

class ProfileFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Profile

    profile_id = factory.LazyFunction(uuid4)
    user = factory.SubFactory(UserFactory)
    display_name = factory.Sequence(lambda n: f"User{n}")
    date_of_birth = factory.Faker("date_of_birth", minimum_age=18, maximum_age=70)
    state_of_residence = "TX"
    biological_sex = "male"
    age_bracket = "30-39"
    fitness_level = "intermediate"
    tier_code = "M-30-39-INT"
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
```

### Running Tests

```bash
# All tests
make test

# With coverage report (HTML)
make test-coverage

# Specific test types
make test-unit           # Fast, mocked dependencies
make test-integration    # Real database, API endpoints
make test-e2e            # Full workflows

# Watch mode (re-run on file changes)
make test-watch

# Parallel execution (faster CI)
pytest -n auto

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run specific test file
pytest tests/unit/services/test_points_service.py

# Run specific test function
pytest tests/unit/services/test_points_service.py::test_calculate_tier_adjusted_points
```

### Test Organization

**Unit Tests** (`tests/unit/`):
- Test individual functions/methods in isolation
- Mock external dependencies (database, APIs, filesystem)
- Fast execution (< 0.01 sec per test)
- Focus on edge cases, error handling, business logic

**Integration Tests** (`tests/integration/`):
- Test interactions between components
- Real database (test database, transactions rolled back)
- Test API endpoints with FastAPI TestClient
- Verify database constraints, triggers, queries

**E2E Tests** (`tests/e2e/`):
- Test complete user workflows
- Multiple API calls in sequence
- Verify end-to-end state changes
- Example: Register → Connect Tracker → Sync → Buy Ticket → Check Leaderboard

**Example Test Structure**:
```python
# tests/unit/services/test_points_service.py
import pytest
from fittrack.services.points_service import PointsService
from fittrack.utils.tier import TIER_MULTIPLIERS

def test_calculate_tier_adjusted_points_beginner():
    """Beginners get 1.2x multiplier for encouragement."""
    service = PointsService(db_session=None)  # Unit test, no DB

    # Base: 3 pts/min vigorous, 30 min = 90 pts
    # Beginner multiplier: 1.2
    # Expected: 90 * 1.2 = 108
    points = service.calculate_points(
        activity_type="active_minutes",
        intensity="vigorous",
        quantity=30,
        tier_code="M-18-29-BEG"
    )

    assert points == 108

def test_daily_cap_enforced():
    """Users cannot earn more than 1000 points per day."""
    service = PointsService(db_session=mock_session)

    # User already earned 950 points today
    mock_session.query.return_value.filter.return_value.scalar.return_value = 950

    # Attempting to earn 100 more (total 1050)
    points = service.calculate_points_with_cap(
        user_id=uuid4(),
        activity_points=100,
        date=date.today()
    )

    # Should be truncated to 50 (reaching 1000 cap)
    assert points == 50

# tests/integration/api/test_ticket_purchase.py
from fastapi.testclient import TestClient
from fittrack.main import app

client = TestClient(app)

def test_purchase_tickets_success(db_session, auth_token):
    """User can purchase tickets if eligible and has sufficient points."""
    # Arrange: Create test data
    user = UserFactory(point_balance=1000)
    drawing = DrawingFactory(status="open", ticket_cost_points=100)
    db_session.add_all([user, drawing])
    db_session.commit()

    # Act: Purchase 5 tickets
    response = client.post(
        f"/api/v1/drawings/{drawing.drawing_id}/tickets",
        json={"quantity": 5},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    # Assert
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["tickets_purchased"] == 5
    assert data["points_spent"] == 500
    assert data["new_point_balance"] == 500

    # Verify database changes
    db_session.refresh(user)
    assert user.point_balance == 500

    tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).all()
    assert len(tickets) == 5
```

## Development Commands

All common tasks automated via `Makefile`:

```bash
# === Environment Setup ===
make setup              # Initial project setup (venv, dependencies, pre-commit hooks)
make dev                # Start full development environment (docker-compose up)
make down               # Stop development environment

# === Database ===
make db-up              # Start Oracle 26ai container only
make db-down            # Stop Oracle container
make db-shell           # Open SQL*Plus shell in Oracle container
make db-migrate         # Run pending Alembic migrations
make db-rollback        # Rollback last migration
make db-seed            # Generate and load synthetic data via scripts/seed_data.py
make db-reset           # Drop all tables, re-migrate, re-seed

# === Testing ===
make test               # Run all tests (unit + integration + e2e)
make test-unit          # Run unit tests only (fast, mocked)
make test-integration   # Run integration tests (real DB)
make test-e2e           # Run end-to-end tests (full workflows)
make test-coverage      # Run tests with coverage report (HTML + terminal)
make test-watch         # Run tests in watch mode (re-run on file change)

# === Code Quality ===
make lint               # Run all linters (ruff check, mypy)
make format             # Auto-format code (ruff format)
make type-check         # Run mypy type checking
make security-scan      # Run bandit security scanner
make quality            # Run all quality checks (lint + type-check + security-scan)

# === Application ===
make run                # Start FastAPI server (development mode, auto-reload)
make run-prod           # Start FastAPI server (production mode, Gunicorn)
make worker             # Start Celery worker (background tasks)
make shell              # Open Python shell with app context (IPython)

# === Documentation ===
make docs               # Generate API documentation (Sphinx)
make docs-serve         # Serve documentation locally (http://localhost:8080)

# === Docker ===
make docker-build       # Build application Docker image
make docker-run         # Run application in Docker container
make docker-push        # Push image to registry (OCI Container Registry)

# === Utilities ===
make clean              # Remove generated files (__pycache__, .pytest_cache, coverage files)
make help               # Show all available commands with descriptions
```

## Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# === Application Configuration ===
APP_ENV=development                    # development | staging | production
APP_DEBUG=true                         # Enable debug mode (development only!)
APP_SECRET_KEY=change-me-in-production # Used for session signing (generate with secrets.token_urlsafe(32))
APP_HOST=0.0.0.0
APP_PORT=8000
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:8000  # Comma-separated

# === Database Configuration ===
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE=FREEPDB1               # Default service name for Oracle Free
ORACLE_USER=fittrack_app
ORACLE_PASSWORD=SecureP@ssw0rd123!    # Change in production!
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
ORACLE_POOL_RECYCLE=3600              # Recycle connections after 1 hour

# === Redis Configuration ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                       # Optional, leave empty for development

# === Security ===
JWT_SECRET_KEY=change-me-jwt-secret   # Separate key for JWT signing (RS256 private key path or secret)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=RS256
PASSWORD_BCRYPT_ROUNDS=12             # Bcrypt cost factor (12 = good balance)
ENCRYPTION_KEY=base64-encoded-32-byte-key  # For OAuth token encryption (AES-256)

# === Terra API Configuration ===
TERRA_API_KEY=your_terra_api_key
TERRA_API_SECRET=your_terra_api_secret
TERRA_WEBHOOK_SECRET=your_webhook_secret
TERRA_BASE_URL=https://api.tryterra.co/v2

# === Email Configuration (SendGrid example) ===
EMAIL_PROVIDER=sendgrid               # sendgrid | ses | smtp
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM_ADDRESS=noreply@fittrack.com
EMAIL_FROM_NAME=FitTrack

# === Celery Configuration ===
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# === Logging ===
LOG_LEVEL=DEBUG                       # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                       # json | text (JSON for production, text for development)

# === Feature Flags (v1.1 features) ===
FEATURE_PREMIUM_SUBSCRIPTIONS=false
FEATURE_SOCIAL_LOGIN=false
FEATURE_HTML_TEST_PAGE=true           # Enable /test/ endpoint (dev only!)

# === External Services (v1.1+) ===
# STRIPE_API_KEY=your_stripe_key      # For premium subscriptions
# SENTRY_DSN=your_sentry_dsn          # For error tracking
```

### Configuration Validation

All configuration validated at startup via **Pydantic Settings**:

```python
# src/fittrack/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str

    oracle_host: str
    oracle_port: int = 1521
    oracle_user: str
    oracle_password: str

    # ... all environment variables as typed fields

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # ORACLE_HOST or oracle_host both work

settings = Settings()  # Fails fast if required vars missing or invalid
```

**Validation Behavior**:
- Missing required variables cause immediate failure with clear error message
- Invalid types (e.g., `ORACLE_PORT=abc`) cause validation error
- Sensitive values masked in logs (`oracle_password: ***`)
- Settings singleton accessible throughout application

## Coding Standards

### General Principles

- **Type hints required** on all function signatures (arguments and return values)
- **Docstrings required** on all public functions, classes, and modules (Google style)
- **No magic numbers**: Use named constants or Enums
- **Prefer composition over inheritance**: Use dependency injection, not deep class hierarchies
- **Single Responsibility Principle**: Each function/class does one thing well
- **Maximum function length**: 50 lines (consider refactoring if longer)
- **Maximum file length**: 500 lines (consider splitting into multiple modules)

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `UserService`, `DrawingRepository` |
| Functions/methods | snake_case | `calculate_points`, `get_user_by_id` |
| Variables | snake_case | `point_balance`, `drawing_id` |
| Constants | UPPER_SNAKE_CASE | `MAX_DAILY_POINTS`, `TIER_MULTIPLIERS` |
| Private members | `_leading_underscore` | `_encrypt_token`, `_validate_eligibility` |
| Modules/packages | snake_case | `points_service.py`, `database/models/` |
| Test files | `test_*.py` | `test_points_service.py` |
| Test functions | `test_*` | `test_calculate_tier_adjusted_points` |

### Error Handling

**Custom Exception Hierarchy**:
```python
# src/fittrack/exceptions.py
class FitTrackException(Exception):
    """Base exception for all application errors."""
    pass

class ValidationError(FitTrackException):
    """Raised when input validation fails."""
    pass

class NotFoundError(FitTrackException):
    """Raised when a requested resource is not found."""
    pass

class AuthenticationError(FitTrackException):
    """Raised when authentication fails."""
    pass

class AuthorizationError(FitTrackException):
    """Raised when user lacks permission for action."""
    pass

class InsufficientPointsError(FitTrackException):
    """Raised when user has insufficient points for purchase."""
    pass

class DrawingClosedError(FitTrackException):
    """Raised when attempting to purchase tickets for closed drawing."""
    pass
```

**Usage Pattern**:
```python
# Service layer raises domain exceptions
def purchase_tickets(user_id: UUID, drawing_id: UUID, quantity: int) -> List[Ticket]:
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    drawing = drawing_repo.get_by_id(drawing_id)
    if not drawing:
        raise NotFoundError(f"Drawing {drawing_id} not found")

    if drawing.status != "open":
        raise DrawingClosedError(f"Drawing {drawing_id} is {drawing.status}")

    total_cost = quantity * drawing.ticket_cost_points
    if user.point_balance < total_cost:
        raise InsufficientPointsError(
            f"User {user_id} has {user.point_balance} points, needs {total_cost}"
        )

    # ... proceed with purchase

# API layer catches exceptions and returns HTTP responses
@router.post("/drawings/{drawing_id}/tickets")
async def purchase_tickets_endpoint(...):
    try:
        tickets = ticket_service.purchase_tickets(...)
        return {"data": tickets, "meta": {...}}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DrawingClosedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InsufficientPointsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FitTrackException as e:
        logger.exception("Unexpected error in ticket purchase")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
```

### Database Access

**Always use repository pattern**:
```python
# src/fittrack/database/repositories/user_repository.py
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from fittrack.database.models.user import User

class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Retrieve user by ID."""
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email address."""
        stmt = select(User).where(User.email == email)
        return self._session.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        """Create new user record."""
        self._session.add(user)
        self._session.flush()  # Get user_id without committing
        return user

    def update_point_balance(self, user_id: UUID, delta: int) -> None:
        """Atomically update user's point balance."""
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(point_balance=User.point_balance + delta)
        )
        self._session.execute(stmt)
```

**Never raw SQL in business logic** (use SQLAlchemy ORM):
```python
# Bad: Raw SQL (SQL injection risk, not portable)
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

# Good: ORM query (safe, portable, type-safe)
stmt = select(User).where(User.email == email)
user = session.execute(stmt).scalar_one_or_none()
```

**Always manage transactions explicitly**:
```python
# Service layer manages transactions
def purchase_tickets_transactional(self, ...):
    with self._session.begin():  # Automatic commit/rollback
        # 1. Deduct points
        self.user_repo.update_point_balance(user_id, -total_cost)

        # 2. Create tickets
        tickets = [Ticket(...) for _ in range(quantity)]
        self.ticket_repo.create_batch(tickets)

        # 3. Create point transaction
        txn = PointTransaction(...)
        self.points_repo.create(txn)

        # All or nothing: commit if no exceptions, rollback on error
```

### API Endpoints

**Use dependency injection for common concerns**:
```python
from fastapi import Depends, HTTPException
from fittrack.api.dependencies import get_db_session, get_current_user
from fittrack.services.user_service import UserService

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),  # Auth dependency
    db_session: Session = Depends(get_db_session),  # DB session dependency
) -> UserResponse:
    """Retrieve current user's profile."""
    user_service = UserService(db_session)
    profile = user_service.get_full_profile(current_user.user_id)
    return UserResponse.model_validate(profile)
```

**Pydantic schemas for request/response**:
```python
# src/fittrack/api/schemas/ticket.py
from pydantic import BaseModel, Field
from uuid import UUID

class TicketPurchaseRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=100, description="Number of tickets to purchase")

class TicketPurchaseResponse(BaseModel):
    tickets_purchased: int
    points_spent: int
    new_point_balance: int
    total_user_tickets: int
    transaction_id: UUID
```

### Logging

**Use structured logging** (JSON format for production):
```python
import structlog

logger = structlog.get_logger()

# Good: Structured, parsable, searchable
logger.info(
    "ticket_purchase_completed",
    user_id=str(user_id),
    drawing_id=str(drawing_id),
    quantity=5,
    points_spent=500,
    request_id=request_id
)

# Bad: Unstructured string (hard to parse/search)
logger.info(f"User {user_id} purchased 5 tickets for {drawing_id}, spent 500 points")
```

**Never log sensitive data**:
```python
# Good: Log user_id only
logger.info("user_login_success", user_id=str(user.user_id))

# Bad: Logs PII (email, password hash)
logger.info("user_login_success", email=user.email, password_hash=user.password_hash)
```

## Known Constraints and Limitations

### MVP Scope Constraints

- **Geography**: United States only, excluding NY, FL, RI (sweepstakes compliance)
- **Age**: 18+ only (legal requirement for sweepstakes participation)
- **Platforms**: Web only (responsive design for mobile browsers, native apps in v1.1)
- **Fitness Trackers**: Apple Health, Google Fit, Fitbit via Terra API (no manual entry)
- **Data Sync**: 15-minute batch intervals (not real-time)
- **Monetization**: Premium subscriptions deferred to v1.1 (all MVP features free)
- **Prize Administration**: Manual admin management (sponsor self-service portal in v1.1)
- **Authentication**: Email/password only (no social login in MVP)

### Technical Limitations

- **Oracle 26ai Free**: Single-instance, max 2 GB memory, 12 GB storage (sufficient for MVP < 10K users)
- **Terra API Rate Limits**: Varies by provider (Google Fit: 86.4K req/day, Fitbit: 150 req/hour/user)
- **Point Earning Cap**: 1,000 points per user per day (anti-gaming measure)
- **Workout Bonus Cap**: Max 3 workout bonuses per day (prevents splitting workouts)
- **Leaderboard Latency**: 15-minute update interval (tied to sync interval)
- **Drawing Execution**: Scheduled job runs every minute (1-min resolution for drawing time)
- **Email Delivery**: Dependent on third-party provider (SendGrid/SES delays possible)

### Known Risks

- **Terra API Dependency**: Single point of failure for fitness data (mitigation: fallback to manual sync in v1.1)
- **Oracle Free License**: Community support only, no SLA (mitigation: production uses Autonomous DB)
- **Sweepstakes Compliance**: Legal risk if rules not followed (mitigation: legal review before launch)
- **Prize Fulfillment Manual**: Admin overhead scales poorly (mitigation: automate in v1.1)

## Assumptions

| ID | Assumption | Risk if Wrong | Validation Plan |
|----|------------|---------------|-----------------|
| A1 | Biological sex (male/female) sufficient for fair competition | User complaints, inclusivity concerns | User research, legal review, add "prefer not to say" + OPEN tier option |
| A2 | 15-minute sync interval acceptable UX | User dissatisfaction with delay | Beta user feedback, consider reducing to 5 min if API limits allow |
| A3 | Daily 1,000 point cap balances anti-gaming and legitimate use | Frustrated power users or continued gaming | Monitor outliers, adjust cap based on data |
| A4 | Email verification sufficient security (no MFA in MVP) | Account takeovers | Security monitoring, implement MFA in v1.1 |
| A5 | Manual prize fulfillment scales for MVP | Admin overload | Monitor volume, automate at 100+ fulfillments/month |
| A6 | Gift cards sufficient prizes (no sponsor partnerships required for MVP) | Low user interest | User surveys, sponsor outreach in parallel |
| A7 | Terra API covers 80%+ of target market fitness tracker users | Low adoption, user complaints | Market research on tracker popularity |
| A8 | Tier-adjusted point rates create fair competition | Complaints about unfairness | Monitor leaderboard distribution, adjust multipliers |
| A9 | OPEN tier opt-in reduces complaints about strict demographics | Low OPEN tier adoption or continued complaints | Track opt-in rate, survey users |
| A10 | Python/FastAPI stack sufficient performance for MVP (5K concurrent users) | Scalability issues | Load testing, profiling, optimize hot paths |

## Glossary

| Term | Definition |
|------|------------|
| **Activity** | A fitness event synced from a tracker (steps, workout session, active minutes) |
| **Drawing** | A sweepstakes event where winners are randomly selected from ticket holders |
| **CSPRNG** | Cryptographically Secure Pseudo-Random Number Generator (used for drawing winner selection) |
| **Fulfillment** | The process of delivering a prize to a winner (notification → address → shipping → delivery) |
| **JSON Duality View** | Oracle database feature allowing document-style JSON access over relational tables |
| **Leaderboard** | Ranked list of users within a tier, ordered by points earned in a period (daily, weekly, monthly, all-time) |
| **OCI** | Oracle Cloud Infrastructure (cloud platform for production deployment) |
| **OPEN Tier** | Competition tier where users from all demographics compete together (opt-in) |
| **Point Balance** | User's current spendable points (can go up via earning, down via spending) |
| **Points Earned** | Total cumulative points a user has earned (used for leaderboard ranking, never decreases) |
| **Terra API** | Third-party fitness data aggregator providing unified API for Apple Health, Google Fit, Fitbit |
| **Ticket** | Entry into a sweepstakes drawing, purchased with points (one ticket = one chance to win) |
| **Tier** | Competition bracket based on user demographics (age bracket, biological sex, fitness level) |
| **Tier Code** | Identifier for a tier (e.g., `M-30-39-INT` = Male, 30-39, Intermediate) or `OPEN` for open competition |
| **Tier Multiplier** | Adjustment factor applied to point earning rates based on tier (beginner: 1.2x, intermediate: 1.0x, advanced: 0.9x) |

## References

- **Product Specification**: `docs/FitTrack-PRD-v1.0.md`
- **Oracle 26ai Documentation**: https://docs.oracle.com/en/database/oracle/oracle-database/
- **Oracle JSON Duality Views**: https://docs.oracle.com/en/database/oracle/oracle-database/23/jsnvu/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0 Documentation**: https://docs.sqlalchemy.org/en/20/
- **python-oracledb Documentation**: https://python-oracledb.readthedocs.io/
- **Terra API Documentation**: https://docs.tryterra.co/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **pytest Documentation**: https://docs.pytest.org/
- **Celery Documentation**: https://docs.celeryproject.org/
