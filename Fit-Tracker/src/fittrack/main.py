"""
FitTrack FastAPI Application

Main entry point for the FitTrack gamified fitness platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import get_engine, Base
from .api.routes.v1.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    """
    # Startup event
    print("Starting FitTrack application...")
    
    # Create tables if they don't exist
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully")
    
    yield
    
    # Shutdown event
    print("Shutting down FitTrack application...")


# Create FastAPI application
app = FastAPI(
    title="FitTrack API",
    description="Gamified fitness platform with sweepstakes rewards",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "fittrack"}


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint - verifies database connectivity."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}, 503


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to FitTrack API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fittrack.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
