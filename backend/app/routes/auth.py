from __future__ import annotations

import datetime as dt
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.session import Session as DbSession
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RegisterRequest, UserMe
from app.services.rate_limit import auth_rate_limit
from app.utils.security import (
    hash_password,
    hash_token,
    is_valid_email,
    random_token,
    verify_password,
)

COOKIE_NAME = "razviton_sid"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _cleanup_sessions(db: Session) -> None:
    now = dt.datetime.utcnow()
    db.query(DbSession).filter(DbSession.expires_at < now).delete()
    db.commit()


def _get_client_ip(req: Request) -> str:
    return req.client.host if req.client else "unknown"


def _set_session_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("RAZVITON_COOKIE_SECURE", "0") == "1",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )


def _clear_cookie(resp: Response) -> None:
    resp.delete_cookie(COOKIE_NAME, path="/")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHENTICATED")

    token_hash = hash_token(token)
    now = dt.datetime.utcnow()
    row = (
        db.query(DbSession)
        .filter(DbSession.token_hash == token_hash, DbSession.expires_at >= now)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SESSION_EXPIRED")

    user = db.query(User).filter(User.id == row.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER_INACTIVE")
    return user


def _create_session(db: Session, user: User, request: Request) -> str:
    token = random_token()
    row = DbSession(
        user_id=user.id,
        token_hash=hash_token(token),
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        expires_at=dt.datetime.utcnow() + dt.timedelta(seconds=SESSION_TTL_SECONDS),
    )
    db.add(row)
    db.commit()
    return token


@router.post("/register", summary="Create account")
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    client_ip = _get_client_ip(request)
    if not auth_rate_limit.allow(f"register:{client_ip}"):
        raise HTTPException(status_code=429, detail="RATE_LIMIT")

    email = payload.normalized_email()
    username = payload.normalized_username()
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="INVALID_EMAIL")
    if db.query(User).filter((User.email == email) | (User.username == username)).first():
        raise HTTPException(status_code=409, detail="USER_EXISTS")

    user = User(
        email=email,
        username=username,
        full_name=(payload.full_name.strip() if payload.full_name else None),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _cleanup_sessions(db)
    token = _create_session(db, user, request)
    _set_session_cookie(response, token)
    return {"ok": True, "user_id": user.id, "username": user.username}


@router.post("/login", summary="Login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    client_ip = _get_client_ip(request)
    if not auth_rate_limit.allow(f"login:{client_ip}"):
        raise HTTPException(status_code=429, detail="RATE_LIMIT")

    ident = payload.normalized_identifier()
    _cleanup_sessions(db)
    user = db.query(User).filter((User.email == ident) | (User.username == ident)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="USER_INACTIVE")

    token = _create_session(db, user, request)
    user.last_login_at = dt.datetime.utcnow()
    db.commit()
    _set_session_cookie(response, token)
    return {"ok": True, "username": user.username}


@router.post("/logout", summary="Logout")
def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    token = request.cookies.get(COOKIE_NAME)
    _clear_cookie(response)
    if not token:
        return {"ok": True}

    token_hash = hash_token(token)
    if payload.all_devices:
        row = db.query(DbSession).filter(DbSession.token_hash == token_hash).first()
        if row:
            db.query(DbSession).filter(DbSession.user_id == row.user_id).delete()
            db.commit()
    else:
        db.query(DbSession).filter(DbSession.token_hash == token_hash).delete()
        db.commit()
    return {"ok": True}


@router.get("/me", summary="Current user", response_model=UserMe)
def me(user: User = Depends(get_current_user)) -> UserMe:
    return UserMe(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        full_name=user.full_name,
    )


@router.get("/admin/stats", summary="Admin stats")
def admin_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    active_sessions = db.query(func.count(DbSession.id)).filter(DbSession.expires_at >= dt.datetime.utcnow()).scalar() or 0
    return {"total_users": int(total_users), "active_users": int(active_users), "active_sessions": int(active_sessions)}
