from __future__ import annotations

import hashlib
import secrets
import time

from sqlalchemy import select

from .db import get_session
from .models import AuthToken, User


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected_digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return secrets.compare_digest(digest.hex(), expected_digest)


def create_user(username: str, password: str) -> User:
    username = username.strip()
    with get_session() as session:
        existing = session.scalar(select(User).where(User.username == username))
        if existing:
            raise ValueError("username already exists")
        user = User(
            username=username,
            password_hash=hash_password(password),
            created_at=int(time.time()),
        )
        session.add(user)
        session.flush()
        session.refresh(user)
        return user


def authenticate_user(username: str, password: str) -> User | None:
    with get_session() as session:
        user = session.scalar(select(User).where(User.username == username.strip()))
        if not user or not verify_password(password, user.password_hash):
            return None
        session.expunge(user)
        return user


def create_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with get_session() as session:
        session.add(AuthToken(token=token, user_id=user_id, created_at=int(time.time())))
    return token


def get_user_by_token(token: str) -> User | None:
    token = token.strip()
    if not token:
        return None
    with get_session() as session:
        auth_token = session.get(AuthToken, token)
        if not auth_token:
            return None
        user = session.get(User, auth_token.user_id)
        if user:
            session.expunge(user)
        return user
