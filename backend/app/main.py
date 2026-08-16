import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth, health, models, predictions, users
from app.api.rate_limit import limiter
from app.core.config import BACKEND_DIR, get_settings
from app.core.logging_config import get_logger, setup_logging
from app.ml.model_manager import ModelManager
from app.services import model_service

settings = get_settings()
logger = get_logger("app.main")

_BACKEND_ONLY_PREFIXES = ("/api", "/health", "/docs", "/redoc", "/openapi.json")


def _frontend_dist() -> Path | None:
    dist = settings.FRONTEND_DIST_DIR
    if dist.is_dir() and (dist / "index.html").is_file():
        return dist
    return None


def _serve_frontend(dist: Path, path: str) -> FileResponse:
    candidate = (dist / path.lstrip("/")).resolve()
    if dist.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(dist / "index.html",
                        headers={"Cache-Control": "no-cache"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application starting", extra={"app": settings.APP_NAME})

    _run_migrations()

    try:
        ModelManager.get_instance().load()
    except Exception as exc:
        logger.error("Models not loaded — run `python -m app.ml.train`",
                     extra={"error": str(exc)})

    from app.db.database import SessionLocal

    with SessionLocal() as db:
        model_service.sync_model_metadata(db)

    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="HeartGuard AI API",
        description=(
            "Secure heart disease prediction system (educational). "
            "Runs the Logistic Regression model locally on the backend. "
            "NOT a medical diagnosis tool."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url=None,
    )

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()")
        path = request.url.path
        if path.startswith("/assets/"):
            response.headers["Cache-Control"] = (
                "public, max-age=31536000, immutable")
        elif path in ("/", "/index.html"):
            response.headers["Cache-Control"] = "no-cache"
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains")
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "font-src 'self' data:; connect-src 'self'; "
                "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        return response

    @app.middleware("http")
    async def limit_payload_size(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if len(body) > settings.MAX_PAYLOAD_BYTES:
                return JSONResponse(
                    {"detail": "Request payload too large."},
                    status_code=413)
        return await call_next(request)

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(users.router, prefix=settings.API_PREFIX)
    app.include_router(predictions.router, prefix=settings.API_PREFIX)
    app.include_router(models.router, prefix=settings.API_PREFIX)

    dist = _frontend_dist()

    if dist is not None:
        assets_dir = dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir),
                      name="assets")

    @app.get("/")
    def root():
        if dist is not None:
            return FileResponse(dist / "index.html",
                                headers={"Cache-Control": "no-cache"})
        return {"app": settings.APP_NAME, "docs": "/docs",
                "health": f"{settings.API_PREFIX}/health"}

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    if dist is not None:
        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str):
            if f"/{full_path}".startswith(_BACKEND_ONLY_PREFIXES):
                return JSONResponse({"detail": "Not found."}, status_code=404)
            return _serve_frontend(dist, full_path)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        if errors:
            loc = ".".join(str(p) for p in errors[0]["loc"] if p != "body")
            message = errors[0].get("msg", "Invalid input")
            detail = f"Invalid value for '{loc}': {message}"
        else:
            detail = "Invalid request."
        return JSONResponse({"detail": detail}, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", extra={"path": request.url.path})
        return JSONResponse(
            {"detail": "An internal error occurred. Please try again later."},
            status_code=500)

    return app


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        {"detail": "Too many requests. Please slow down and try again."},
        status_code=429)


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config as AlembicConfig

    cfg = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


app = create_app()
