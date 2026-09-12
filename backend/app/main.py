from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db.database import Base, engine
from app.models import session as session_model
from app.models import user as user_model
from app.routes.auth import router as auth_router

APP_DIR = Path(__file__).resolve().parents[2]
PUBLIC_DIR = APP_DIR

app = FastAPI(title="RAZVITON", version="1.1.0")

@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
    response.headers.setdefault("Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self';")
    return response

@app.get("/health")
def health():
    return {"status": "ok", "service": "RAZVITON"}

app.include_router(auth_router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Mount last so /api and /health are resolved first.
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")
