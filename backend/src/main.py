from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.mongodb import init_mongodb
from src.core.redis import init_redis
from src.core.database import AsyncSessionLocal
from src.events.kafka import init_kafka, close_kafka
from src.routes import auth, urls, workspaces, folders, tags, favorites, audit_logs, webhooks, redirect
from src.errors import AppError
from src.logging import setup_logging, get_logger
from src.middleware.tracing import TracingMiddleware
from src.middleware.metrics import MetricsMiddleware
from src.middleware.audit import AuditContextMiddleware
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.rbac import RBACMiddleware
from src.core.tracing import init_tracing, init_metrics, instrument_fastapi


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tracing()
    prometheus_reader = init_metrics()
    setup_logging()
    logger = get_logger()
    logger.info("Initializing URL Shortener services...")

    try:
        await init_redis()
        print("[OK] Redis (Upstash) connected successfully.")
    except Exception as e:
        print(f"[WARNING] Redis connection failed: {e}")

    try:
        await init_mongodb()
        print("[OK] MongoDB (Atlas) connected successfully.")
    except Exception as e:
        print(f"[WARNING] MongoDB connection failed (analytics disabled): {e}")

    try:
        await init_kafka()
        print("[OK] Kafka (Aiven) connected successfully.")
    except Exception as e:
        print(f"[WARNING] Kafka connection failed: {e}")

    logger.info("All services initialized successfully")
    yield

    logger.info("Shutting down URL Shortener services...")
    try:
        await close_kafka()
    except Exception as e:
        print(f"[WARNING] Error closing Kafka connection: {e}")
    logger.info("Shutdown complete")


openapi_tags = [
    {"name": "Auth", "description": "User registration, login, logout, email verification, OAuth SSO, and password reset."},
    {"name": "URLs", "description": "Create, list, update, delete shortened URLs. Supports QR codes, A/B testing, one-time links, and password protection."},
    {"name": "Workspaces", "description": "Workspace CRUD, member management, and invite system."},
    {"name": "Folders", "description": "Organize URLs into folders within a workspace."},
    {"name": "Tags", "description": "Tag URLs for flexible categorization and filtering."},
    {"name": "Favorites", "description": "Mark and manage frequently-used URLs."},
    {"name": "Analytics", "description": "Click analytics, time series, device and geo breakdown per short URL."},
    {"name": "API Keys", "description": "Programmatic API key management for automated access."},
    {"name": "Bulk Operations", "description": "Bulk create, update, disable, delete, export URLs and generate QR code ZIPs."},
    {"name": "Webhooks", "description": "Register webhook endpoints to receive real-time URL events."},
    {"name": "Audit Logs", "description": "Audit trail of all actions performed across workspaces."},
    {"name": "Redirection", "description": "Public short URL resolution — redirects to the original destination."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise URL Shortener — production-grade, event-driven, fully observable.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    contact={"name": "LinkForge Team", "url": "https://linkforge.dev"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(TracingMiddleware)

instrument_fastapi(app)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


# --- Routers ---
app.include_router(auth.router, prefix="/api/v1")
app.include_router(urls.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")
app.include_router(folders.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")
from src.routes import analytics
app.include_router(analytics.router, prefix="/api/v1")
from src.routes import api_keys, bulk
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(bulk.router, prefix="/api/v1")
app.include_router(audit_logs.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(redirect.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/metrics", tags=["Observability"])
async def metrics_endpoint():
    try:
        from prometheus_client import generate_latest
        metrics_data = generate_latest()
        return Response(content=metrics_data, media_type="text/plain; charset=utf-8")
    except Exception as e:
        logger = get_logger()
        logger.error("Error generating metrics: %s", str(e))
        return Response(content=f"# Error generating metrics: {str(e)}\n", media_type="text/plain; charset=utf-8")
