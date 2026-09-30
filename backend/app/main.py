import logging
import logging.config
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import admin_llm, analytics, audit, auth, departments, diagnostic, documents, incident, learning, mentor, modules, phishing, phishing_public, schedules, social_eng, testing, users
from app.routers import settings as settings_router

cfg = get_settings()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)-8s %(name)s  %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn.access": {"level": "WARNING"},  # suppress raw access log (we have our middleware)
        "sqlalchemy.engine": {"level": "WARNING"},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup model=%s", cfg.OPENAI_MODEL)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="VKR Security Awareness API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.exception("http %s %s 500 %dms (unhandled)", request.method, request.url.path, latency_ms)
        return JSONResponse(status_code=500, content={"data": None, "error": "Internal server error"})
    latency_ms = int((time.monotonic() - t0) * 1000)
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(level, "http %s %s %d %dms", request.method, request.url.path, response.status_code, latency_ms)
    return response


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(modules.router, prefix="/api/modules", tags=["modules"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])
app.include_router(testing.router, prefix="/api/testing", tags=["testing"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(mentor.router, prefix="/api/mentor", tags=["mentor"])
app.include_router(phishing.router, prefix="/api/phishing", tags=["phishing"])
app.include_router(phishing_public.router, prefix="/phishing", tags=["phishing-public"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(diagnostic.router, prefix="/api/diagnostic", tags=["diagnostic"])
app.include_router(settings_router.router, prefix="/api/admin/settings", tags=["settings"])
app.include_router(admin_llm.router, prefix="/api/admin/llm", tags=["admin-llm"])
app.include_router(social_eng.router, prefix="/api/social-eng", tags=["social-engineering"])
app.include_router(incident.router, prefix="/api/incident", tags=["incident"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
