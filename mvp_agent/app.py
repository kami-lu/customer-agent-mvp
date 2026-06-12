from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing FastAPI dependencies. Install them with: pip install fastapi uvicorn"
    ) from exc

from .agent import run_agent
from .db import get_messages, init_db, list_conversations
from .web import CHAT_HTML


class ChatRequest(BaseModel):
    query: str
    conversation_id: str = "demo"


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
def chat(request: ChatRequest) -> dict[str, Any]:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query cannot be empty")
    conversation_id = request.conversation_id.strip() or "demo"
    return run_agent(query, conversation_id)


@app.get("/conversations")
def conversations(limit: int = 20) -> dict[str, list[dict[str, Any]]]:
    limit = max(1, min(limit, 100))
    return {"conversations": list_conversations(limit)}


@app.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: str) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "messages": get_messages(conversation_id),
    }


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
