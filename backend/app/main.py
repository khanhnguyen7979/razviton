from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text as sql_text
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import Base, engine
from app.models import session as session_model
from app.models import user as user_model
from app.routes.auth import router as auth_router

APP_DIR = Path(__file__).resolve().parents[2]
PUBLIC_DIR = APP_DIR / "public"

app = FastAPI(title="RAZVITON", version="1.1.0", docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
    response.headers.setdefault("Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self';")
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo password or other submitted input in validation responses.
    return JSONResponse(status_code=422, content={"detail": "INVALID_INPUT"})

@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    # SQLAlchemy exception strings can contain SQL parameters; do not expose them.
    return JSONResponse(status_code=503, content={"detail": "DATABASE_UNAVAILABLE"}, headers={"Cache-Control": "no-store"})

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(sql_text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "error", "service": "RAZVITON", "database": "unavailable"})
    return {"status": "ok", "service": "RAZVITON"}

app.include_router(auth_router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Mount last so /api and /health are resolved first.
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")
