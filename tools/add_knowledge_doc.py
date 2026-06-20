from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from mvp_agent.db import get_session, init_db
from mvp_agent.models import KnowledgeChunk
from mvp_agent.vector_store import VectorStoreUnavailable, build_chroma_index


def add_knowledge_doc(title: str, content: str, source: str, rebuild_index: bool = True) -> int:
    init_db()
    with get_session() as session:
        existing = session.scalar(
            select(KnowledgeChunk).where(
                KnowledgeChunk.title == title,
                KnowledgeChunk.source == source,
            )
        )
        if existing:
            existing.content = content
            chunk_id = existing.id
        else:
            chunk = KnowledgeChunk(title=title, content=content, source=source)
            session.add(chunk)
            session.flush()
            chunk_id = chunk.id

    if rebuild_index:
        try:
            count = build_chroma_index()
            print(f"Rebuilt Chroma index with {count} chunks.")
        except VectorStoreUnavailable as exc:
            print(f"Chroma index was not rebuilt: {exc}")
            print("Install vector dependencies with: pip install chromadb sentence-transformers")
    return chunk_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or update one RAG knowledge document.")
    parser.add_argument("--title", required=True, help="Knowledge chunk title.")
    parser.add_argument("--content", required=True, help="Knowledge chunk content.")
    parser.add_argument("--source", required=True, help="Source filename or identifier.")
    parser.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding Chroma index.")
    args = parser.parse_args()

    chunk_id = add_knowledge_doc(
        title=args.title.strip(),
        content=args.content.strip(),
        source=args.source.strip(),
        rebuild_index=not args.no_rebuild,
    )
    print(f"Knowledge chunk saved: id={chunk_id}, title={args.title}")


if __name__ == "__main__":
    main()
