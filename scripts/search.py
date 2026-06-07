"""Tiny BM25 search over chunks.jsonl — a smoke-test for the dataset's retrieval shape.

Usage:
  python3 scripts/search.py "ما هو قناع توت عنخ آمون؟"

Pure-stdlib: no external deps. Returns top-k chunks ranked by BM25.
This is a baseline; for a real RAG system replace BM25 with a dense retriever
(AraDPR, Cohere multilingual, OpenAI text-embedding-3) and reuse the same chunks.
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "chunks.jsonl"

ARABIC_DIACRITICS = re.compile(r"[ً-ٰٟـ]")
NON_WORD = re.compile(r"[^ء-ي٠-٩A-Za-z0-9 ]+")


def normalize(s: str) -> str:
    s = s.lower()
    s = ARABIC_DIACRITICS.sub("", s)
    s = (
        s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        .replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    )
    s = NON_WORD.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokenize(s: str) -> list[str]:
    return [t for t in normalize(s).split() if len(t) > 1]


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.N = len(docs)
        self.avgdl = sum(len(d) for d in docs) / max(self.N, 1)
        self.k1 = k1
        self.b = b
        self.df: Counter[str] = Counter()
        for d in docs:
            for term in set(d):
                self.df[term] += 1
        self.idf = {
            t: math.log((self.N - df + 0.5) / (df + 0.5) + 1)
            for t, df in self.df.items()
        }

    def score(self, q: list[str], doc: list[str]) -> float:
        if not doc:
            return 0.0
        tf = Counter(doc)
        dl = len(doc)
        s = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = self.idf.get(term, 0.0)
            f = tf[term]
            s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

    def topk(self, q: list[str], k: int = 5) -> list[tuple[int, float]]:
        scored = [(i, self.score(q, d)) for i, d in enumerate(self.docs)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


def main(query: str, k: int = 5) -> None:
    if not CHUNKS.exists():
        print("Run scripts/package.py first to generate chunks.jsonl")
        return
    chunks = [json.loads(line) for line in CHUNKS.open(encoding="utf-8")]
    docs = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25(docs)
    q_tokens = tokenize(query)
    print(f"Query: {query!r}")
    print(f"Tokens: {q_tokens}\n")
    for rank, (idx, sc) in enumerate(bm25.topk(q_tokens, k), start=1):
        c = chunks[idx]
        print(f"#{rank}  score={sc:.3f}  [{c['lang']}]  {c.get('name_ar') or c.get('name_en')} ({c['artifact_id']})")
        text = c["text"]
        print("   " + text[:250].replace("\n", " ") + ("…" if len(text) > 250 else ""))
        print(f"   image: images/{c.get('primary_image', '?')}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 scripts/search.py \"<query>\" [k]")
        sys.exit(1)
    q = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    main(q, k)
