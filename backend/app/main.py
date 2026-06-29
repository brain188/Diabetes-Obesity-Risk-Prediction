"""
FastAPI application entry point.
Configures the application, middleware, and startup/shutdown events.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import init_database, close_database
from app.core.logging import setup_logging, get_logger, audit_logger
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    NotFoundError,
    DuplicateError,
    PredictionError,
    ModelNotLoadedError,
    DatabaseError,
)
from app.ml.model_loader import model_loader

# Setup logging first
setup_logging()
logger = get_logger(__name__)


# Lifespan Context Manager

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events.
    
    Startup:
        - Initialize database connection pool
        - Load ML models and artifacts
        - Warm up caches
    
    Shutdown:
        - Close database connections
        - Clean up resources
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)
    
    # Startup
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_database()
        logger.info("Database initialized successfully")
        
        # Load ML models
        logger.info("Loading ML artifacts...")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, model_loader.load_all)

            # Pre-build all cached explainers so the first prediction is fast.
            # Run in executor — these are CPU-bound and would block the event loop.
            logger.info("Warming up caches (feature importance, SHAP, LIME)...")
            await loop.run_in_executor(None, model_loader.get_feature_importance_cached)
            await loop.run_in_executor(None, model_loader.get_shap_explainer_cached)
            await loop.run_in_executor(None, model_loader.get_lime_explainer_cached)

            logger.info("All systems ready!")
        except FileNotFoundError as e:
            # In test/dev environments model artifacts may be absent.
            logger.warning(f"ML artifacts not found; continuing without model. Error: {str(e)}")
            # Keep app running; prediction endpoints should return 503 if needed.
        
    except Exception as e:
        logger.error(f" Startup failed: {str(e)}")
        raise

    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    logger.info("=" * 60)
    logger.info(f"{settings.APP_NAME} shutdown complete")
    logger.info("=" * 60)


# Create FastAPI Application

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Middleware Configuration

# Request/Response Middleware — registered first so CORS (added last) ends up outermost.

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to each request for tracing and logging."""
    import uuid
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"Request completed | {request.method} {request.url.path} | "
        f"status={response.status_code} | duration={duration_ms:.2f}ms | "
        f"request_id={request_id}"
    )
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with metadata."""
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else "unknown")
    )
    logger.info(
        f"Request received | {request.method} {request.url.path} | "
        f"ip={client_ip} | user_agent={request.headers.get('User-Agent', '-')} | "
        f"request_id={getattr(request.state, 'request_id', '-')}"
    )
    return await call_next(request)


# CORS must be added LAST so Starlette places it outermost in the middleware
# stack — it runs first and handles OPTIONS preflights before anything else.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware (security)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )


# Exception Handlers

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle custom application exceptions.
    """
    logger.warning(
        f"AppException: {exc.message} | "
        f"status={exc.status_code} | error_code={exc.error_code} | "
        f"path={request.url.path} | request_id={getattr(request.state, 'request_id', '-')}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    audit_logger.log_login(
        email=request.headers.get("email", "unknown"),
        success=False,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("User-Agent"),
        request_id=getattr(request.state, 'request_id', '-')
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "AUTHENTICATION_ERROR",
            "message": exc.message,
            "status_code": 401,
            "timestamp": time.time(),
            "path": request.url.path,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        f"Validation error: {errors} | "
        f"path={request.url.path} | request_id={getattr(request.state, 'request_id', '-')}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "status_code": 422,
            "detail": errors,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Handle not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "RESOURCE_NOT_FOUND",
            "message": exc.message,
            "status_code": 404,
            "detail": exc.detail,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(DuplicateError)
async def duplicate_exception_handler(request: Request, exc: DuplicateError):
    """Handle duplicate resource errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "DUPLICATE_RESOURCE",
            "message": exc.message,
            "status_code": 409,
            "detail": exc.detail,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(PredictionError)
async def prediction_exception_handler(request: Request, exc: PredictionError):
    """Handle prediction errors."""
    logger.error(
        f"Prediction error: {exc.message} | "
        f"path={request.url.path} | request_id={getattr(request.state, 'request_id', '-')}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "PREDICTION_ERROR",
            "message": exc.message,
            "status_code": 500,
            "detail": exc.detail,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_exception_handler(request: Request, exc: ModelNotLoadedError):
    """Handle model not loaded errors."""
    logger.error(f"Model not loaded: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "MODEL_NOT_LOADED",
            "message": exc.message,
            "status_code": 503,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(
        f"Database error: {exc.message} | "
        f"path={request.url.path} | request_id={getattr(request.state, 'request_id', '-')}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DATABASE_ERROR",
            "message": "A database error occurred. Please try again later.",
            "status_code": 500,
            "timestamp": time.time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle any unhandled exceptions.
    """
    logger.error(
        f"Unhandled exception: {str(exc)} | "
        f"type={type(exc).__name__} | "
        f"path={request.url.path} | request_id={getattr(request.state, 'request_id', '-')}",
        exc_info=True
    )
    
    # Log to audit for security-critical errors
    if "auth" in request.url.path:
        audit_logger.log_login(
            email=request.headers.get("email", "unknown"),
            success=False,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent"),
            request_id=getattr(request.state, 'request_id', '-'),
            details={"error": str(exc)}
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
            "timestamp": time.time(),
            "path": request.url.path,
            "request_id": getattr(request.state, 'request_id', '-'),
        },
    )


# Health Check Endpoint

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Check if the service is running and healthy.",
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Status of the service including database and model status.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "database": "connected",
        "models_loaded": model_loader.is_loaded,
        "model_version": model_loader.model_version if model_loader.is_loaded else None,
    }


@app.get(
    "/ready",
    tags=["Health"],
    summary="Readiness check",
    description="Check if the service is ready to accept traffic.",
)
async def readiness_check() -> dict:
    """
    Readiness check endpoint.
    
    Returns:
        Status indicating if the service is ready.
    """
    is_ready = (
        model_loader.is_loaded
        # Add other readiness checks here
    )
    
    return {
        "ready": is_ready,
        "models_loaded": model_loader.is_loaded,
    }


# Include API Routes

# Include v1 API routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs" if settings.DEBUG else None,
        "api_v1": settings.API_V1_PREFIX,
        "environment": settings.ENVIRONMENT,
    }


# Application State

# Store the model loader in app state for easy access
app.state.model_loader = model_loader

logger.info(f"{settings.APP_NAME} application created successfully")


# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_dirs=["app"] if settings.DEBUG else None,
        log_level=settings.LOG_LEVEL.lower(),
    )