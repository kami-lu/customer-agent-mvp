from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mvp_agent.db import init_db
from mvp_agent.vector_store import CHROMA_DIR, VectorStoreUnavailable, build_chroma_index


def main() -> None:
    init_db()
    try:
        count = build_chroma_index()
    except VectorStoreUnavailable as exc:
        raise SystemExit(
            "Chroma dependencies are missing. Install them with: "
            "pip install chromadb"
        ) from exc
    print(f"Built Chroma index with {count} chunks at {CHROMA_DIR}")


if __name__ == "__main__":
    main()
