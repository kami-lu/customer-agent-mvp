from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select

from .db import BASE_DIR, get_session, model_to_dict
from .models import KnowledgeChunk


CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "customer_agent_knowledge"


class VectorStoreUnavailable(RuntimeError):
    pass


class HashEmbeddingFunction:
    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def name(self) -> str:
        return "customer_agent_hash_embedding"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in input]

    def embed_query(self, input: str | list[str]) -> list[float] | list[list[float]]:
        if isinstance(input, str):
            return self.embed(input)
        return [self.embed(text) for text in input]

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in input]

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{1,2}", text.lower())
        for token in tokens:
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def load_knowledge_documents() -> list[dict[str, Any]]:
    with get_session() as session:
        chunks = session.scalars(select(KnowledgeChunk).order_by(KnowledgeChunk.id.asc())).all()
        return [model_to_dict(chunk, ["id", "title", "content", "source"]) for chunk in chunks]


def document_id(document: dict[str, Any]) -> str:
    raw = f"{document['id']}|{document['title']}|{document['source']}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def document_text(document: dict[str, Any]) -> str:
    return f"{document['title']}\n{document['content']}"


def get_chroma_collection(persist_dir: Path = CHROMA_DIR):
    try:
        import chromadb
    except ModuleNotFoundError as exc:
        raise VectorStoreUnavailable("chromadb is not installed") from exc

    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=HashEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )


def build_chroma_index(persist_dir: Path = CHROMA_DIR) -> int:
    documents = load_knowledge_documents()
    collection = get_chroma_collection(persist_dir)
    if not documents:
        return 0

    ids = [document_id(document) for document in documents]
    texts = [document_text(document) for document in documents]
    metadatas = [
        {
            "chunk_id": document["id"],
            "title": document["title"],
            "source": document["source"],
            "content": document["content"],
        }
        for document in documents
    ]
    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
    return len(documents)


def search_chroma(query: str, limit: int = 3, persist_dir: Path = CHROMA_DIR) -> list[dict[str, Any]]:
    collection = get_chroma_collection(persist_dir)
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[query], n_results=limit)
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    chunks: list[dict[str, Any]] = []
    for metadata, distance in zip(metadatas, distances):
        if not metadata:
            continue
        chunks.append(
            {
                "id": metadata.get("chunk_id"),
                "title": metadata.get("title", ""),
                "content": metadata.get("content", ""),
                "source": metadata.get("source", ""),
                "score": round(1 - float(distance), 4),
                "retrieval": "vector",
            }
        )
    return chunks
