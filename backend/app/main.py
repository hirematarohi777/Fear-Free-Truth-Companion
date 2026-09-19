import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.db.mongo import DatabaseManager
from app.workers.job_worker import worker_instance

# Import Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analyses import router as analyses_router
from app.api.v1.url_checks import router as url_checks_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.calculations import router as calculations_router
from app.api.v1.reports import router as reports_router
from app.api.v1.family import router as family_router
from app.api.v1.privacy import router as privacy_router
from app.api.v1.health import router as health_router
from app.api.v1.demo import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured logging
    setup_logging()
    logger.info("Initializing Fear-Free Family Truth Companion Backend...")
    settings.validate_production_safety()

    # Connect to MongoDB
    await DatabaseManager.connect_to_database()

    # Start background worker task
    worker_task = asyncio.create_task(worker_instance.start())
    logger.info("Background job worker started.")

    yield

    # Shutdown
    logger.info("Shutting down backend...")
    worker_instance.stop()
    worker_task.cancel()
    await DatabaseManager.close_database_connection()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Consent-first financial clarity platform for Indian home loans.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global sanitized error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    # In production, do not return raw tracebacks or sensitive data
    if settings.APP_ENV.lower() == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal error occurred. Please try again later."}
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )


# Register API v1 Routers
api_v1_prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(documents_router, prefix=api_v1_prefix)
app.include_router(analyses_router, prefix=api_v1_prefix)
app.include_router(url_checks_router, prefix=api_v1_prefix)
app.include_router(jobs_router, prefix=api_v1_prefix)
app.include_router(calculations_router, prefix=api_v1_prefix)
app.include_router(reports_router, prefix=api_v1_prefix)
app.include_router(family_router, prefix=api_v1_prefix)
app.include_router(privacy_router, prefix=api_v1_prefix)
app.include_router(health_router, prefix=api_v1_prefix)
app.include_router(demo_router, prefix=api_v1_prefix)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "tagline": settings.APP_TAGLINE,
        "version": "1.0.0",
        "docs": "/docs"
    }
