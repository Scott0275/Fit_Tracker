# FitTrack Implementation Checklist

 > Track progress through all 6 checkpoints. Check off items as completed. This checklist corresponds to IMPLEMENTATION_PLAN.md.

**Legend**:
- [ ] Not started
- [x] Completed
- [~] In progress
- [!] Blocked

---

## Checkpoint 1: Foundation - Test Environment & Data Layer (16 days)

### Infrastructure Setup
- [ ] Install Docker and verify it's running
- [ ] Pull Oracle 26ai Free container image
- [ ] Create `docker/docker-compose.yml` with Oracle, Redis, app, worker services
- [ ] Create `docker/Dockerfile.dev` with hot reload support
- [ ] Create `docker/Dockerfile` for production
- [ ] Create `Makefile` with all development commands
- [ ] Create `.env.example` with all required environment variables
- [ ] Create `.gitignore` with appropriate exclusions
- [ ] Create `scripts/setup_dev.sh` for automated environment setup
- [ ] Test `make setup && make dev` from fresh clone (< 15 min)

### Database Models & Migrations
- [ ] Set up SQLAlchemy with `python-oracledb` driver
- [ ] Create `src/fittrack/database/connection.py` (engine, session factory)
- [ ] Create `src/fittrack/database/models/base.py` (declarative base, mixins)
- [ ] Create `src/fittrack/database/models/user.py` (User, Profile models)
- [ ] Create `src/fittrack/database/models/tracker.py` (TrackerConnection model)
- [ ] Create `src/fittrack/database/models/activity.py` (Activity model with JSON metrics)
- [ ] Create `src/fittrack/database/models/points.py` (PointTransaction model)
- [ ] Create `src/fittrack/database/models/drawing.py` (Drawing, Prize models)
- [ ] Create `src/fittrack/database/models/ticket.py` (Ticket model)
- [ ] Create `src/fittrack/database/models/fulfillment.py` (PrizeFulfillment model with JSON address)
- [ ] Create `src/fittrack/database/models/sponsor.py` (Sponsor model)
- [ ] Set up Alembic for migrations
- [ ] Create initial migration `migrations/versions/001_initial_schema.py`
- [ ] Create indexes for all foreign keys and frequently queried columns
- [ ] Create functional indexes for JSON columns (e.g., metrics.steps)
- [ ] Test `make db-migrate` successfully creates all tables

### Repository Layer
- [ ] Create `src/fittrack/database/repositories/base.py` (generic CRUD interface)
- [ ] Create `src/fittrack/database/repositories/user_repository.py`
- [ ] Create `src/fittrack/database/repositories/activity_repository.py`
- [ ] Create `src/fittrack/database/repositories/points_repository.py`
- [ ] Create `src/fittrack/database/repositories/drawing_repository.py`
- [ ] Create `src/fittrack/database/repositories/ticket_repository.py`
- [ ] Create `src/fittrack/database/repositories/leaderboard_repository.py`
- [ ] Create `src/fittrack/database/repositories/fulfillment_repository.py`
- [ ] Add type hints to all repository methods
- [ ] Test each repository with integration tests

### Synthetic Data Generation
- [ ] Set up `factory_boy` and `Faker`
- [ ] Create `tests/factories/base.py` (common factory config)
- [ ] Create `tests/factories/user_factory.py`
- [ ] Create `tests/factories/profile_factory.py`
- [ ] Create `tests/factories/activity_factory.py`
- [ ] Create `tests/factories/drawing_factory.py`
- [ ] Create `tests/factories/ticket_factory.py`
- [ ] Create `scripts/seed_data.py` CLI tool
- [ ] Add seed scenarios for all 30 tiers + OPEN tier
- [ ] Add seed scenarios for all 3 tracker providers
- [ ] Add seed scenarios for completed drawings with winners
- [ ] Test `make db-seed` generates complete data in < 2 min
- [ ] Test `make db-reset` resets database successfully

### FastAPI Application Setup
- [ ] Create `src/fittrack/main.py` (FastAPI app factory)
- [ ] Create `src/fittrack/config.py` (Pydantic Settings)
- [ ] Create `src/fittrack/exceptions.py` (custom exception hierarchy)
- [ ] Add CORS middleware configuration
- [ ] Add request logging middleware
- [ ] Set up health check endpoints
- [ ] Test application starts with `make run`

### API Schemas
- [ ] Create `src/fittrack/api/schemas/common.py` (pagination, errors)
- [ ] Create `src/fittrack/api/schemas/user.py`
- [ ] Create `src/fittrack/api/schemas/activity.py`
- [ ] Create `src/fittrack/api/schemas/drawing.py`
- [ ] Create `src/fittrack/api/schemas/points.py`
- [ ] Add Pydantic validation to all schemas
- [ ] Add examples to all schemas for documentation

### API Endpoints
- [ ] Create `src/fittrack/api/routes/health.py` (GET /health, /health/ready)
- [ ] Create `src/fittrack/api/routes/v1/users.py` (CRUD for users)
- [ ] Create `src/fittrack/api/routes/v1/activities.py` (list, get activities)
- [ ] Create `src/fittrack/api/routes/v1/drawings.py` (list, get drawings)
- [ ] Create `src/fittrack/api/routes/v1/points.py` (list transactions, get balance)
- [ ] Create `src/fittrack/api/routes/v1/reports.py` (GET /reports/summary)
- [ ] Create `src/fittrack/api/dependencies.py` (get_db_session dependency)
- [ ] Test all endpoints return valid responses
- [ ] Verify OpenAPI docs accessible at `/docs`

### HTML Test Page
- [ ] Create `static/test/index.html` (main page with tabs)
- [ ] Create `static/test/css/test-page.css` (responsive styling)
- [ ] Create `static/test/js/api-tester.js` (interactive endpoint testing)
- [ ] Create `static/test/js/leaderboard-viewer.js` (sample leaderboard display)
- [ ] Create `static/test/js/report-viewer.js` (data verification reports)
- [ ] Create `static/test/js/sample-data.js` (seed/reset controls)
- [ ] Add syntax highlighting for JSON responses (Prism.js)
- [ ] Test page accessible at `/test/` in dev mode
- [ ] Test page returns 404 in production mode
- [ ] Verify all CRUD operations work via test page
- [ ] Verify seed/reset buttons function correctly

### Testing
- [ ] Set up pytest with test configuration
- [ ] Create `tests/conftest.py` (test fixtures, test DB)
- [ ] Create integration tests for all repositories
- [ ] Create integration tests for all API endpoints
- [ ] Create unit tests for factories
- [ ] Run `make test` - all tests pass
- [ ] Run `make test-coverage` - coverage > 85%
- [ ] Fix any failing tests

### Documentation
- [ ] Create `README.md` with setup instructions
- [ ] Create `docs/adr/0001-record-architecture-decisions.md`
- [ ] Create `docs/adr/0002-oracle-json-tables.md`
- [ ] Create `docs/adr/0003-terra-api-integration.md`
- [ ] Create `docs/adr/0004-tier-based-point-scaling.md`
- [ ] Create `docs/diagrams/data-model.mmd` (ERD)
- [ ] Verify README setup works in < 15 min

### Checkpoint 1 Validation
- [ ] Demo: Show full stack running
- [ ] Demo: Show database seeded with complete data
- [ ] Demo: Show test page CRUD operations
- [ ] Demo: Show leaderboard viewer (mock data)
- [ ] Demo: Show report viewer with metrics
- [ ] Stakeholder approval received

---

## Checkpoint 2: Authentication & Authorization (8 days)

### Password & JWT Utilities
- [ ] Create `src/fittrack/security/authentication.py`
- [ ] Implement bcrypt password hashing (cost factor 12)
- [ ] Implement password strength validation
- [ ] Implement JWT creation with RS256
- [ ] Implement JWT validation
- [ ] Implement JWT refresh logic
- [ ] Generate RSA key pair for JWT signing
- [ ] Test password hashing/verification
- [ ] Test JWT creation/validation

### Auth Service
- [ ] Create `src/fittrack/services/auth_service.py`
- [ ] Implement user registration with validation
- [ ] Implement age verification (18+)
- [ ] Implement state eligibility check
- [ ] Implement email verification flow
- [ ] Implement login with credential validation
- [ ] Implement account lockout (5 failed attempts)
- [ ] Implement password reset flow
- [ ] Test all auth service methods

### Email Service
- [ ] Create `src/fittrack/integrations/email.py`
- [ ] Set up SendGrid (or alternative) integration
- [ ] Create email templates directory `templates/emails/`
- [ ] Create verification email template (HTML)
- [ ] Create password reset email template (HTML)
- [ ] Create welcome email template (HTML)
- [ ] Test email sending in development
- [ ] Configure email sending for production

### RBAC & Authorization
- [ ] Create `src/fittrack/security/authorization.py`
- [ ] Implement `@require_role` decorator
- [ ] Implement `@require_permission` decorator
- [ ] Create `get_current_user` dependency
- [ ] Create `get_current_admin` dependency
- [ ] Implement role-based access checks
- [ ] Test RBAC decorators

### Auth API Endpoints
- [ ] Create `src/fittrack/api/schemas/auth.py`
- [ ] Create `src/fittrack/api/routes/v1/auth.py`
- [ ] Implement POST /auth/register
- [ ] Implement POST /auth/login
- [ ] Implement POST /auth/refresh
- [ ] Implement POST /auth/verify-email
- [ ] Implement POST /auth/forgot-password
- [ ] Implement POST /auth/reset-password
- [ ] Implement POST /auth/logout
- [ ] Test all auth endpoints

### Protected Endpoints
- [ ] Update GET /api/v1/users/me (require auth)
- [ ] Update PUT /api/v1/users/me (require auth)
- [ ] Update PUT /api/v1/users/me/password (require auth)
- [ ] Add auth requirements to existing endpoints
- [ ] Test protected endpoints return 401 without token
- [ ] Test protected endpoints work with valid token

### HTML Test Page Enhancement
- [ ] Add "Authentication Tester" tab to test page
- [ ] Add login form to test page
- [ ] Add registration form to test page
- [ ] Add token display panel
- [ ] Add "Test Protected Endpoint" button
- [ ] Update API Tester to include Authorization header
- [ ] Test login/logout flow via test page

### Testing
- [ ] Create unit tests for password hashing
- [ ] Create unit tests for JWT creation/validation
- [ ] Create unit tests for auth service
- [ ] Create unit tests for RBAC decorators
- [ ] Create integration tests for auth endpoints
- [ ] Create E2E test for registration flow
- [ ] Run all tests - >85% coverage

### Documentation
- [ ] Create `docs/adr/0005-jwt-authentication.md`
- [ ] Create `docs/adr/0006-email-password-only-mvp.md`
- [ ] Create `docs/diagrams/auth-flow.mmd`
- [ ] Update README with auth setup instructions

### Checkpoint 2 Validation
- [ ] Demo: Register new user
- [ ] Demo: Verify email
- [ ] Demo: Login and receive JWT
- [ ] Demo: Access protected endpoint with token
- [ ] Demo: Admin role access control
- [ ] Stakeholder approval received

---

## Checkpoint 3: Fitness Tracker Integration (10 days)

### Terra API Client
- [ ] Create Terra API developer account
- [ ] Obtain Terra API credentials
- [ ] Create `src/fittrack/integrations/terra.py`
- [ ] Implement OAuth widget session generation
- [ ] Implement OAuth callback handling
- [ ] Implement activity data fetching
- [ ] Implement token refresh logic
- [ ] Implement error handling and retry logic
- [ ] Test Terra API client with mock responses

### Connection Service
- [ ] Create `src/fittrack/services/tracker_service.py`
- [ ] Implement OAuth flow orchestration
- [ ] Implement connection creation (store encrypted tokens)
- [ ] Implement connection deletion
- [ ] Implement primary tracker designation
- [ ] Implement token encryption (AES-256-GCM)
- [ ] Test tracker service methods

### Sync Service
- [ ] Create `src/fittrack/services/sync_service.py`
- [ ] Implement activity fetching from Terra
- [ ] Implement activity normalization
- [ ] Implement duplicate detection logic
- [ ] Implement primary tracker deduplication
- [ ] Implement sync error handling
- [ ] Test sync service with sample data

### Points Service
- [ ] Create `src/fittrack/services/points_service.py`
- [ ] Create `src/fittrack/utils/tier.py` (rate tables, multipliers)
- [ ] Implement base point calculation
- [ ] Implement tier multiplier lookup
- [ ] Implement tier-adjusted point calculation
- [ ] Implement daily cap enforcement (1,000 points)
- [ ] Implement workout bonus logic (max 3 per day)
- [ ] Test point calculation for all tier types
- [ ] Test daily cap enforcement

### Celery Workers
- [ ] Create `src/fittrack/workers/celery_app.py`
- [ ] Configure Celery with Redis broker
- [ ] Create `src/fittrack/workers/sync_tasks.py`
- [ ] Implement periodic sync task (every 15 min)
- [ ] Implement user-specific sync task
- [ ] Implement token refresh task
- [ ] Create `docker/Dockerfile.worker`
- [ ] Update docker-compose.yml to include worker
- [ ] Test Celery worker starts successfully
- [ ] Test periodic sync task executes

### Connection API Endpoints
- [ ] Create `src/fittrack/api/schemas/terra.py`
- [ ] Create `src/fittrack/api/routes/v1/connections.py`
- [ ] Implement GET /connections (list user's connections)
- [ ] Implement POST /connections/{provider}/initiate
- [ ] Implement GET /connections/{provider}/callback
- [ ] Implement DELETE /connections/{provider}
- [ ] Implement POST /connections/{provider}/sync (manual sync)
- [ ] Test all connection endpoints

### Activity API Endpoints
- [ ] Update `src/fittrack/api/routes/v1/activities.py`
- [ ] Implement GET /activities with date filters
- [ ] Implement GET /activities with type filters
- [ ] Implement GET /activities/{id}
- [ ] Implement GET /activities/summary
- [ ] Test all activity endpoints

### HTML Test Page Enhancement
- [ ] Add "Tracker Connection Simulator" tab
- [ ] Add provider selection dropdown
- [ ] Add "Connect Tracker" button
- [ ] Add connection status display
- [ ] Add "Trigger Sync" button
- [ ] Add activity log display with points breakdown
- [ ] Test tracker connection simulation

### Testing
- [ ] Create unit tests for Terra client (mocked HTTP)
- [ ] Create unit tests for points calculation
- [ ] Create unit tests for tier utilities
- [ ] Create unit tests for sync service
- [ ] Create integration tests for connection endpoints
- [ ] Create integration tests for activity endpoints
- [ ] Create E2E test for activity sync flow
- [ ] Run all tests - >85% coverage

### Documentation
- [ ] Create `docs/adr/0007-terra-api-integration.md`
- [ ] Create `docs/adr/0008-15-minute-sync-interval.md`
- [ ] Create `docs/adr/0009-tier-adjusted-points.md`
- [ ] Create `docs/diagrams/sync-flow.mmd`
- [ ] Create `docs/point-calculation.md` (rate tables)

### Checkpoint 3 Validation
- [ ] Demo: Connect fitness tracker
- [ ] Demo: Trigger manual sync
- [ ] Demo: View synced activities with points
- [ ] Demo: Verify tier-adjusted point calculation
- [ ] Demo: Verify daily cap enforcement
- [ ] Stakeholder approval received

---

## Checkpoint 4: Competition & Leaderboards (8 days)

### Tier Calculation
- [ ] Update `src/fittrack/utils/tier.py`
- [ ] Implement tier code generation (M-30-39-INT format)
- [ ] Implement age bracket calculation from DOB
- [ ] Implement OPEN tier opt-in logic
- [ ] Test tier code calculation for all 30 tiers
- [ ] Test OPEN tier generation

### Profile Service Update
- [ ] Create `src/fittrack/services/profile_service.py`
- [ ] Implement tier recalculation on profile update
- [ ] Implement age bracket update on birthday
- [ ] Test tier recalculation logic

### Leaderboard Repository
- [ ] Update `src/fittrack/database/repositories/leaderboard_repository.py`
- [ ] Implement daily leaderboard query
- [ ] Implement weekly leaderboard query
- [ ] Implement monthly leaderboard query
- [ ] Implement all-time leaderboard query
- [ ] Implement tier filtering
- [ ] Implement pagination for leaderboards
- [ ] Optimize queries with indexes
- [ ] Test leaderboard queries with sample data

### Leaderboard Service
- [ ] Create `src/fittrack/services/leaderboard_service.py`
- [ ] Implement ranking calculation
- [ ] Implement tie-breaking logic (timestamp)
- [ ] Implement user position calculation
- [ ] Implement Redis caching (5-min TTL)
- [ ] Implement cache invalidation on activity sync
- [ ] Test leaderboard service methods
- [ ] Test cache hit/miss behavior

### Leaderboard API Endpoints
- [ ] Create `src/fittrack/api/schemas/leaderboard.py`
- [ ] Create `src/fittrack/api/routes/v1/leaderboards.py`
- [ ] Implement GET /leaderboards/daily
- [ ] Implement GET /leaderboards/weekly
- [ ] Implement GET /leaderboards/monthly
- [ ] Implement GET /leaderboards/alltime
- [ ] Implement tier query parameter (browse tiers)
- [ ] Test all leaderboard endpoints
- [ ] Test response includes user position

### Public Profile Endpoint
- [ ] Update `src/fittrack/api/routes/v1/users.py`
- [ ] Implement GET /users/{id}/public
- [ ] Return only public data (display name, tier, rank)
- [ ] Test public profile endpoint

### HTML Test Page Enhancement
- [ ] Update "Leaderboard Viewer" tab
- [ ] Replace mock data with real API calls
- [ ] Add period selector (Daily, Weekly, Monthly, All-Time)
- [ ] Add tier selector dropdown
- [ ] Highlight user's position
- [ ] Add pagination controls
- [ ] Add auto-refresh toggle (every 60 sec)
- [ ] Test live leaderboard display

### Testing
- [ ] Create unit tests for tier calculation
- [ ] Create integration tests for leaderboard queries
- [ ] Create unit tests for leaderboard service
- [ ] Create integration tests for leaderboard endpoints
- [ ] Create integration tests for cache invalidation
- [ ] Run all tests - >85% coverage
- [ ] Performance test: leaderboard query < 500ms

### Documentation
- [ ] Create `docs/adr/0010-leaderboard-caching.md`
- [ ] Create `docs/adr/0011-tier-recalculation.md`
- [ ] Create `docs/tier-matrix.md` (all 30 tiers)

### Checkpoint 4 Validation
- [ ] Demo: View leaderboard for own tier
- [ ] Demo: Browse other tier leaderboards
- [ ] Demo: See position highlighted on leaderboard
- [ ] Demo: Verify cache performance
- [ ] Demo: Verify tier recalculation on profile update
- [ ] Stakeholder approval received

---

## Checkpoint 5: Sweepstakes Engine (12 days)

### CSPRNG Utilities
- [ ] Create `src/fittrack/security/random.py`
- [ ] Implement CSPRNG winner selection (Python secrets)
- [ ] Implement random seed generation for audit
- [ ] Test CSPRNG randomness and distribution

### Drawing Service
- [ ] Create `src/fittrack/services/drawing_service.py`
- [ ] Implement drawing creation (admin)
- [ ] Implement drawing state machine (draft → scheduled → open → closed → completed)
- [ ] Implement state transition validation
- [ ] Implement drawing update (admin)
- [ ] Implement drawing cancellation
- [ ] Implement eligibility validation
- [ ] Test drawing service methods
- [ ] Test state machine transitions

### Ticket Service
- [ ] Create `src/fittrack/services/ticket_service.py`
- [ ] Implement ticket purchase with validation
- [ ] Implement atomic transaction (point deduction + ticket creation)
- [ ] Implement eligibility check
- [ ] Implement odds calculation
- [ ] Test ticket service methods
- [ ] Test insufficient points handling
- [ ] Test closed drawing handling

### Execution Service
- [ ] Create `src/fittrack/services/execution_service.py`
- [ ] Implement ticket number assignment
- [ ] Implement CSPRNG winner selection
- [ ] Implement multiple prize winner selection
- [ ] Implement idempotent execution (check completed_at)
- [ ] Implement result publication
- [ ] Test execution service
- [ ] Test idempotency

### Fulfillment Service
- [ ] Create `src/fittrack/services/fulfillment_service.py`
- [ ] Implement fulfillment creation on winner selection
- [ ] Implement shipping address collection
- [ ] Implement fulfillment status transitions
- [ ] Implement forfeit logic (14-day timeout)
- [ ] Implement reminder email (7-day warning)
- [ ] Test fulfillment service methods

### Notification Service
- [ ] Create `src/fittrack/services/notification_service.py`
- [ ] Implement winner notification email
- [ ] Implement participant notification email
- [ ] Implement drawing result email
- [ ] Implement reminder email
- [ ] Create email templates for all notifications
- [ ] Test notification service

### Drawing Background Workers
- [ ] Create `src/fittrack/workers/drawing_tasks.py`
- [ ] Implement drawing state transition task (runs every minute)
- [ ] Implement drawing execution task
- [ ] Implement forfeit check task
- [ ] Implement reminder email task
- [ ] Test drawing workers

### Drawing API Endpoints (User)
- [ ] Create `src/fittrack/api/schemas/drawing.py`
- [ ] Create `src/fittrack/api/routes/v1/drawings.py`
- [ ] Implement GET /drawings (list with filters)
- [ ] Implement GET /drawings/{id}
- [ ] Implement POST /drawings/{id}/tickets (purchase)
- [ ] Implement GET /drawings/{id}/results
- [ ] Implement GET /tickets (user's tickets)
- [ ] Test all user drawing endpoints

### Fulfillment API Endpoints (User)
- [ ] Implement GET /fulfillments (user's wins)
- [ ] Implement PUT /fulfillments/{id}/address
- [ ] Test fulfillment endpoints

### Admin Drawing Endpoints
- [ ] Create `src/fittrack/api/routes/v1/admin/drawings.py`
- [ ] Implement POST /admin/drawings (create)
- [ ] Implement PUT /admin/drawings/{id} (update)
- [ ] Implement POST /admin/drawings/{id}/execute (manual trigger)
- [ ] Test admin drawing endpoints

### Admin Fulfillment Endpoints
- [ ] Create `src/fittrack/api/routes/v1/admin/fulfillments.py`
- [ ] Implement GET /admin/fulfillments (list all)
- [ ] Implement PUT /admin/fulfillments/{id} (update status)
- [ ] Implement POST /admin/fulfillments/{id}/ship (mark shipped)
- [ ] Test admin fulfillment endpoints

### HTML Test Page Enhancement
- [ ] Add "Drawings & Tickets" tab
- [ ] Add drawings list with filters
- [ ] Add "Buy Tickets" button with modal
- [ ] Add "My Tickets" section
- [ ] Add drawing results display
- [ ] Add fulfillment status tracking
- [ ] Add "Admin - Drawings" tab
- [ ] Add drawing creation form
- [ ] Add "Execute Drawing" button
- [ ] Add fulfillment management table
- [ ] Test all drawing functionality via test page

### Testing
- [ ] Create unit tests for CSPRNG
- [ ] Create unit tests for drawing service
- [ ] Create unit tests for ticket service
- [ ] Create unit tests for execution service
- [ ] Create unit tests for fulfillment service
- [ ] Create integration tests for drawing endpoints
- [ ] Create integration tests for admin endpoints
- [ ] Create E2E test for ticket purchase flow
- [ ] Create E2E test for prize fulfillment flow
- [ ] Run all tests - >85% coverage

### Documentation
- [ ] Create `docs/adr/0012-csprng-winner-selection.md`
- [ ] Create `docs/adr/0013-drawing-state-machine.md`
- [ ] Create `docs/adr/0014-manual-fulfillment-mvp.md`
- [ ] Create `docs/diagrams/drawing-flow.mmd`
- [ ] Create `docs/sweepstakes-rules.md` (legal compliance)

### Checkpoint 5 Validation
- [ ] Demo: Admin creates drawing
- [ ] Demo: User purchases tickets
- [ ] Demo: Drawing executes automatically
- [ ] Demo: Winner is selected via CSPRNG
- [ ] Demo: Winner notification sent
- [ ] Demo: Prize fulfillment workflow
- [ ] Stakeholder approval received

---

## Checkpoint 6: Production Readiness (10 days)

### Structured Logging
- [ ] Create `src/fittrack/utils/logging.py`
- [ ] Implement structured logging (JSON format)
- [ ] Implement correlation ID generation
- [ ] Update middleware to add correlation IDs
- [ ] Update all log statements to use structured logging
- [ ] Test logging in development
- [ ] Test logging in production mode

### Metrics Collection
- [ ] Create `src/fittrack/utils/metrics.py`
- [ ] Implement Prometheus HTTP metrics (counters, histograms)
- [ ] Implement Prometheus business metrics (registrations, tickets, points)
- [ ] Implement Celery metrics
- [ ] Add /metrics endpoint
- [ ] Test metrics collection
- [ ] Test Prometheus scraping

### Enhanced Health Checks
- [ ] Update `src/fittrack/api/routes/health.py`
- [ ] Implement GET /health/live (lightweight)
- [ ] Implement GET /health/ready (DB, Redis, Celery)
- [ ] Test health checks return correct status
- [ ] Test health check when dependencies are down

### Error Tracking
- [ ] Set up Sentry account
- [ ] Integrate Sentry SDK
- [ ] Configure Sentry with environment tags
- [ ] Configure error scrubbing (remove PII)
- [ ] Test error capture
- [ ] Test breadcrumb capture

### Production Configuration
- [ ] Create `gunicorn.conf.py`
- [ ] Create `docker/nginx.conf`
- [ ] Update `docker/Dockerfile` (multi-stage build)
- [ ] Create non-root user in Dockerfile
- [ ] Create `docker/docker-compose.prod.yml`
- [ ] Create `.env.staging` template
- [ ] Create `.env.production` template
- [ ] Test production Docker build

### Deployment Automation
- [ ] Create `.github/workflows/cd.yml`
- [ ] Implement CI pipeline (lint, test, security scan)
- [ ] Implement staging deployment (automatic on merge)
- [ ] Implement production deployment (manual approval)
- [ ] Create `scripts/migrate.sh` (safe migrations)
- [ ] Create `scripts/rollback.sh` (quick rollback)
- [ ] Test CI/CD pipeline on staging

### Load Testing
- [ ] Create `tests/load/locustfile.py`
- [ ] Implement load test scenarios (leaderboards, drawings, tickets)
- [ ] Run load test: 5,000 concurrent users
- [ ] Verify p95 latency < 500ms
- [ ] Verify error rate < 0.5%
- [ ] Verify no memory leaks
- [ ] Document load test results

### Security Hardening
- [ ] Configure security headers (HSTS, CSP, X-Frame-Options)
- [ ] Configure rate limiting in Nginx
- [ ] Set up secrets in OCI Vault (or environment)
- [ ] Implement secret rotation process
- [ ] Run SAST scan (Snyk or similar)
- [ ] Run DAST scan (OWASP ZAP)
- [ ] Run dependency vulnerability scan
- [ ] Fix all critical/high vulnerabilities

### Smoke Tests
- [ ] Create `tests/smoke/` directory
- [ ] Implement smoke test: health check
- [ ] Implement smoke test: user registration
- [ ] Implement smoke test: user login
- [ ] Implement smoke test: view leaderboards
- [ ] Implement smoke test: view drawings
- [ ] Implement smoke test: admin create drawing
- [ ] Run smoke tests post-deployment

### Documentation
- [ ] Create `docs/deployment.md` (step-by-step guide)
- [ ] Create `docs/runbook.md` (operational procedures)
- [ ] Create `docs/monitoring.md` (dashboards, alerts)
- [ ] Create `docs/security.md` (security checklist)
- [ ] Create `docs/adr/0015-structured-logging.md`
- [ ] Create `docs/adr/0016-prometheus-metrics.md`
- [ ] Create `docs/adr/0017-gunicorn-nginx-deployment.md`
- [ ] Generate API documentation from OpenAPI spec

### Checkpoint 6 Validation
- [ ] Deploy to staging environment
- [ ] Run load tests on staging
- [ ] Run security scans
- [ ] Review all metrics and logs
- [ ] Deploy to production (with approval)
- [ ] Run smoke tests on production
- [ ] Monitor production for 48 hours
- [ ] Stakeholder approval received

---

## Post-Implementation

### Final Validation
- [ ] All 6 checkpoints completed
- [ ] All tests passing with >85% coverage
- [ ] Load testing passed (5,000 concurrent users)
- [ ] Security review passed
- [ ] Legal review passed (sweepstakes rules)
- [ ] Production deployment successful
- [ ] Smoke tests pass in production
- [ ] 48-hour production monitoring completed
- [ ] No critical issues in production

### Documentation Review
- [ ] README.md complete and accurate
- [ ] CLAUDE.md complete and accurate
- [ ] IMPLEMENTATION_PLAN.md matches actual implementation
- [ ] All ADRs documented
- [ ] API documentation generated
- [ ] Runbook tested and validated

### Handoff
- [ ] Code repository access provided to team
- [ ] Production credentials documented securely
- [ ] On-call procedures documented
- [ ] Monitoring dashboards shared
- [ ] Incident response plan shared
- [ ] Training materials prepared
- [ ] Stakeholder sign-off received

---

## Notes

**How to use this checklist**:
1. Check off items as you complete them
2. Use `[~]` for items in progress
3. Use `[!]` for blocked items (add notes in comments)
4. Review this checklist at the start of each day
5. Update progress at the end of each day
6. Share updates with stakeholders weekly

**Estimation**: Total ~64 working days across 6 checkpoints (approximately 20 weeks with buffer for integration and testing).

**Priority**: Focus on completing each checkpoint fully before moving to the next. Each checkpoint should be demonstrable and stakeholder-approved.
