from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select

from .db import BASE_DIR, get_session, model_to_dict
from .models import KnowledgeChunk


CHROMA_DIR = BASE_DIR / "chroma_db"
BGE_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
COLLECTION_NAME = "customer_agent_knowledge_bge_small_zh_v1_5"


class VectorStoreUnavailable(RuntimeError):
    pass


class BGEEmbeddingFunction:
    def __init__(self, model_name: str = BGE_MODEL_NAME):
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            raise VectorStoreUnavailable(
                "sentence-transformers is not installed. Install it with: pip install sentence-transformers"
            ) from exc
        self.model_name = model_name
        allow_download = os.getenv("BGE_ALLOW_DOWNLOAD", "").strip() == "1"
        self.model = SentenceTransformer(model_name, local_files_only=not allow_download)

    def name(self) -> str:
        return self.model_name.replace("/", "_").replace("-", "_").replace(".", "_").lower()

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embed_documents(input)

    def embed_query(self, input: str | list[str]) -> list[float] | list[list[float]]:
        if isinstance(input, str):
            return self.embed_documents([input])[0]
        return self.embed_documents(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


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
        embedding_function=BGEEmbeddingFunction(),
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
