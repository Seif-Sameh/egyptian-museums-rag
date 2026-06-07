"""Dense retriever — sentence embeddings + FAISS vector index over the same chunks.

Model: intfloat/multilingual-e5-small  (~118 MB, 384-dim, supports Arabic).
This matches the brief's "Dense Vector Retrieval (DPR) and FAISS" requirement.

Persists embeddings to dataset/data/_embeddings.npy and the FAISS index
to dataset/data/_faiss.index, so subsequent server starts are instantaneous.

Top-level API
-------------
DenseRetriever(chunks).search(query, k) → list[(chunk_index, score), ...]
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EMB_PATH = DATA_DIR / "_embeddings.npy"
FAISS_PATH = DATA_DIR / "_faiss.index"
META_PATH = DATA_DIR / "_embeddings_meta.json"

MODEL_NAME = os.environ.get(
    "EMBED_MODEL", "intfloat/multilingual-e5-small"
)
# E5 models expect a "passage:" prefix on docs and "query:" on queries.
DOC_PREFIX = "passage: "
QUERY_PREFIX = "query: "


class DenseRetriever:
    def __init__(self, chunks: list[dict]) -> None:
        from sentence_transformers import SentenceTransformer  # lazy import
        import faiss

        self.chunks = chunks
        self.model = SentenceTransformer(MODEL_NAME, device="cpu")
        self.dim = self.model.get_sentence_embedding_dimension()

        meta_ok = META_PATH.exists() and EMB_PATH.exists() and FAISS_PATH.exists()
        if meta_ok:
            try:
                meta = json.loads(META_PATH.read_text(encoding="utf-8"))
                if (
                    meta.get("model") == MODEL_NAME
                    and meta.get("n_chunks") == len(chunks)
                    and meta.get("dim") == self.dim
                ):
                    self.embeddings = np.load(EMB_PATH)
                    self.index = faiss.read_index(str(FAISS_PATH))
                    return
            except Exception:
                pass

        # Build embeddings + FAISS index from scratch
        texts = [DOC_PREFIX + c["text"] for c in chunks]
        embs = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine via inner product
        ).astype("float32")
        self.embeddings = embs
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embs)

        # Persist
        np.save(EMB_PATH, embs)
        faiss.write_index(self.index, str(FAISS_PATH))
        META_PATH.write_text(
            json.dumps({"model": MODEL_NAME, "n_chunks": len(chunks), "dim": self.dim}),
            encoding="utf-8",
        )

    def encode_query(self, query: str) -> np.ndarray:
        return self.model.encode(
            [QUERY_PREFIX + query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        if not query.strip():
            return []
        q = self.encode_query(query)
        scores, idxs = self.index.search(q, k)
        return [(int(i), float(s)) for i, s in zip(idxs[0], scores[0]) if i >= 0]
