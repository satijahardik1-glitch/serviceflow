import logging
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.routers import admin, auth, bookings, services, technicians

logging.basicConfig(level=settings.LOG_LEVEL.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("serviceflow")

IS_PROD = settings.is_production
app = FastAPI(
    title="ServiceFlow API", version="1.1.0", description="Trusted Technician Marketplace",
    docs_url=None if IS_PROD else "/docs", redoc_url=None, openapi_url=None if IS_PROD else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"],
)

CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
       "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")


@app.middleware("http")
async def security_headers_and_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:  # never leak stack traces to clients
        logger.exception("Unhandled error rid=%s %s %s", request_id, request.method, request.url.path)
        response = JSONResponse({"detail": "Internal server error"}, status_code=500)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = CSP
    if request.url.path.startswith("/api"):
        response.headers.setdefault("Cache-Control", "no-store")
    elif request.url.path.startswith("/assets"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    logger.info("%s %s -> %s %.0fms rid=%s", request.method, request.url.path, response.status_code,
                (time.perf_counter() - start) * 1000, request_id)
    return response


for module in (auth, services, technicians, bookings, admin):
    app.include_router(module.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/api/health/ready", tags=["health"])
def ready(db: Session = Depends(get_db)):
    """Readiness probe: verifies database connectivity."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed")
        raise HTTPException(503, "Database unavailable")
    return {"status": "ready"}


# Serve the built React app (frontend/dist) from the same origin, with SPA fallback routing.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = (DIST / full_path).resolve()
        if full_path and candidate.is_file() and DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-cache"})
