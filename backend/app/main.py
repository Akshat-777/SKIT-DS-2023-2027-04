from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import RequestIDMiddleware, logger, sanitize_pii
from app.api.routes import (
    health, resumes, users, parsed_entities, skills, job_postings, analyses, audit_logs, market
)
from app.services.market.scheduler import start_market_scheduler, stop_market_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start APScheduler for 6-hour market refresh
    logger.info("Starting up CareerLens FastAPI Backend...")
    try:
        start_market_scheduler()
    except Exception as e:
        logger.warning(f"Could not start market scheduler on app launch: {e}")
    yield
    # Shutdown: Stop APScheduler
    logger.info("Shutting down CareerLens FastAPI Backend...")
    try:
        stop_market_scheduler()
    except Exception as e:
        logger.warning(f"Error stopping market scheduler: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="CareerLens AI Backend API - Smart Resume & Market Analysis System",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # CORS Setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID Middleware
    app.add_middleware(RequestIDMiddleware)

    # Routers
    app.include_router(health.router)
    app.include_router(users.router, prefix=settings.API_V1_STR)
    app.include_router(resumes.router, prefix=settings.API_V1_STR)
    app.include_router(parsed_entities.router, prefix=settings.API_V1_STR)
    app.include_router(skills.router, prefix=settings.API_V1_STR)
    app.include_router(job_postings.router, prefix=settings.API_V1_STR)
    app.include_router(analyses.router, prefix=settings.API_V1_STR)
    app.include_router(audit_logs.router, prefix=settings.API_V1_STR)
    app.include_router(market.router)
    app.include_router(market.router, prefix=settings.API_V1_STR)

    # Global Exception Handlers conforming strictly to {"error": {"code": str, "message": str}}
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        code = "HTTP_ERROR"
        message = str(exc.detail)

        if isinstance(exc.detail, dict):
            code = exc.detail.get("code", "HTTP_ERROR")
            message = exc.detail.get("message", str(exc.detail))

        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            code = "UNPROCESSABLE_ENTITY"

        logger.warning(sanitize_pii(f"HTTPException {exc.status_code}: {message}"))
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": message}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        error_msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()])
        logger.warning(sanitize_pii(f"Validation Error: {error_msg}"))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Input validation failed: {error_msg}"
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(sanitize_pii(f"Unhandled Server Exception: {str(exc)}"))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred."
                }
            }
        )

    return app

app = create_app()
