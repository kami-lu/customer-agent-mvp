from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

try:
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing FastAPI dependencies. Install them with: pip install fastapi uvicorn"
    ) from exc

from .agent import run_agent
from .auth import authenticate_user, create_token, create_user, get_user_by_token
from .db import create_ticket, get_messages, init_db, list_conversations, list_tickets, update_ticket_status
from .models import User
from .web import CHAT_HTML


class ChatRequest(BaseModel):
    query: str
    conversation_id: str = "demo"


class AuthRequest(BaseModel):
    username: str
    password: str


class TicketCreateRequest(BaseModel):
    description: str
    conversation_id: str | None = None
    title: str | None = None


class TicketStatusRequest(BaseModel):
    status: str


def user_payload(user: User) -> dict[str, Any]:
    return {"id": user.id, "username": user.username}


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()


def current_user(authorization: str | None, required: bool = False) -> User | None:
    token = extract_bearer_token(authorization)
    if not token:
        if required:
            raise HTTPException(status_code=401, detail="missing bearer token")
        return None
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="invalid token")
    return user


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Customer Agent MVP",
    description="A minimal customer service Agent with routing, tools, SQLite storage, and optional LLM response generation.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return CHAT_HTML


@app.get("/chat", response_class=HTMLResponse)
def chat_page() -> str:
    return CHAT_HTML


@app.post("/chat")
def chat(request: ChatRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query cannot be empty")
    conversation_id = request.conversation_id.strip() or "demo"
    user = current_user(authorization)
    return run_agent(query, conversation_id, user.id if user else None)


@app.post("/auth/register")
def register(request: AuthRequest) -> dict[str, Any]:
    username = request.username.strip()
    password = request.password
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="password must be at least 6 characters")
    try:
        user = create_user(username, password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    token = create_token(user.id)
    return {"token": token, "user": user_payload(user)}


@app.post("/auth/login")
def login(request: AuthRequest) -> dict[str, Any]:
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid username or password")
    token = create_token(user.id)
    return {"token": token, "user": user_payload(user)}


@app.get("/me")
def me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = current_user(authorization, required=True)
    assert user is not None
    return {"user": user_payload(user)}


@app.get("/conversations")
def conversations(limit: int = 20, authorization: str | None = Header(default=None)) -> dict[str, list[dict[str, Any]]]:
    limit = max(1, min(limit, 100))
    user = current_user(authorization)
    return {"conversations": list_conversations(limit, user.id if user else None)}


@app.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = current_user(authorization)
    return {
        "conversation_id": conversation_id,
        "messages": get_messages(conversation_id, user.id if user else None),
    }


@app.post("/tickets")
def create_support_ticket(
    request: TicketCreateRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    user = current_user(authorization, required=True)
    assert user is not None
    description = request.description.strip()
    if len(description) < 5:
        raise HTTPException(status_code=400, detail="description must be at least 5 characters")
    conversation_id = request.conversation_id.strip() if request.conversation_id else None
    title = request.title.strip() if request.title else None
    try:
        ticket = create_ticket(user.id, description, conversation_id, title)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ticket": ticket}


@app.get("/tickets")
def support_tickets(limit: int = 20, authorization: str | None = Header(default=None)) -> dict[str, list[dict[str, Any]]]:
    user = current_user(authorization, required=True)
    assert user is not None
    limit = max(1, min(limit, 100))
    return {"tickets": list_tickets(user.id, limit)}


@app.patch("/tickets/{ticket_id}/status")
def change_ticket_status(
    ticket_id: int,
    request: TicketStatusRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    user = current_user(authorization, required=True)
    assert user is not None
    try:
        ticket = update_ticket_status(user.id, ticket_id, request.status.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return {"ticket": ticket}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import os

    import uvicorn

    host = os.getenv("MVP_HOST", "127.0.0.1")
    port = int(os.getenv("MVP_PORT", "8010"))
    print(f"Customer Agent MVP running at http://{host}:{port}")
    print(f"Swagger docs running at http://{host}:{port}/docs")
    uvicorn.run("mvp_agent.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
