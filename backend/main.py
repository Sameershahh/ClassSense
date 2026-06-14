# backend/main.py
# ClassSense FastAPI application entry point.
# Run with: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan: startup & shutdown ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────
    logger.info("ClassSense API starting up …")

    # Create all DB tables (safe to call even if tables already exist)
    from backend.database import create_tables
    create_tables()
    logger.info("Database tables verified.")

    # ML pipeline is loaded at import time (ml_runner singleton)
    from backend.services.ml_runner import ml_runner
    if ml_runner.is_ready:
        logger.info("ML pipeline: ✅ ready")
        if ml_runner.model_loaded:
            logger.info("Emotion model: ✅ fine-tuned weights loaded")
        else:
            logger.warning(
                "Emotion model: ⚠️  weights not found. "
                "Copy classsense_BEST.pth → ml/emotion/model_weights/classsense_mobilenetv2.pth"
            )
    else:
        logger.error("ML pipeline: ❌ failed to load — check ml/ directory structure")

    logger.info("ClassSense API ready. Swagger: http://localhost:8000/docs")
    yield

    # ── SHUTDOWN ──────────────────────────────────────────────
    logger.info("ClassSense API shutting down.")


# ── Application ───────────────────────────────────────────────
app = FastAPI(
    title       = "ClassSense API",
    description = (
        "Classroom engagement & emotion monitoring backend.\n\n"
        "## Workflow\n"
        "1. `POST /auth/token` — login, get JWT\n"
        "2. `POST /api/sessions/` — start a session\n"
        "3. `POST /api/sessions/{id}/upload-video` — upload classroom video\n"
        "4. `POST /api/sessions/{id}/end` — compute summary\n"
        "5. `GET  /api/analytics/{id}/report/pdf` — download PDF\n\n"
        "All endpoints except `/health` require a Bearer JWT token."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
# Adjust allow_origins for production (remove * and set your domain).
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins     = CORS_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Global exception handler ──────────────────────────────────
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error("HTTPException on %s %s (status %d): %s",
                 request.method, request.url.path, exc.status_code, exc.detail, exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("RequestValidationError on %s %s: %s",
                 request.method, request.url.path, exc.errors(), exc_info=True)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s",
                 request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs."},
    )


# ── Routers ───────────────────────────────────────────────────
from backend.auth              import router as auth_router       # noqa
from backend.routers.sessions  import router as sessions_router   # noqa
from backend.routers.analytics import router as analytics_router  # noqa
from backend.routers.admin     import router as admin_router      # noqa
from backend.routers.hod       import router as hod_router        # noqa

app.include_router(auth_router,      prefix="/auth",          tags=["Authentication"])
app.include_router(sessions_router,  prefix="/api/sessions",  tags=["Sessions"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(admin_router,     prefix="/api/admin",     tags=["Super Admin"])
app.include_router(hod_router,       prefix="/api/hod",       tags=["HOD Management"])




# ── Health check (no auth required) ──────────────────────────
@app.get("/health", tags=["Health"], summary="API health check")
def health_check():
    """
    Public endpoint. Returns API status and ML pipeline state.
    Used by Docker health checks and monitoring tools.
    """
    from backend.services.ml_runner import ml_runner
    return {
        "status"      : "ok",
        "service"     : "ClassSense API",
        "version"     : "1.0.0",
        "ml_ready"    : ml_runner.is_ready,
        "model_loaded": ml_runner.model_loaded,
    }


# ── Dev runner ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host    = "0.0.0.0",
        port    = 8000,
        reload  = True,
        workers = 1,   # keep at 1 — ML pipeline is not multi-process safe
    )
