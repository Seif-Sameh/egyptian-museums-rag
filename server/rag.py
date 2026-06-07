"""RAG pipeline — hybrid retrieval (BM25 + dense embeddings) + answer generation.

Architecture (matches the project brief):

  ┌─────────────────────────────────────────────────────────────┐
  │ 1. Query                                                     │
  │    └─ Arabic-aware normalize + synonym expansion + alias lookup │
  │                                                               │
  │ 2. Retrieval (hybrid):                                       │
  │    ├─ Sparse: BM25 over normalized tokens                   │
  │    └─ Dense:  multilingual-E5 → FAISS IndexFlatIP (cosine)  │
  │      ↓                                                       │
  │    Reciprocal Rank Fusion (RRF) merges both rankings        │
  │      ↓                                                       │
  │    Title-match boost re-rank                                 │
  │                                                               │
  │ 3. Answer:                                                   │
  │    ├─ Generative: Anthropic Claude / OpenAI GPT (env keys)  │
  │    └─ Extractive (no key): templated answer from struct      │
  │                                                               │
  │ 4. Augment with full artifact record + related items         │
  └─────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"

ARABIC_DIACRITICS = re.compile(r"[ً-ٰٟـ]")
NON_WORD = re.compile(r"[^ء-ي٠-٩A-Za-z0-9 ]+")


def normalize_ar(s: str) -> str:
    s = (s or "").lower()
    s = ARABIC_DIACRITICS.sub("", s)
    s = (
        s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        .replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    )
    s = NON_WORD.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


# Synonym expansion: map common Arabic Egyptology terms to alternates so the
# user's word doesn't have to exactly match the Wikipedia article wording.
SYNONYMS_AR: dict[str, list[str]] = {
    "صلايه": ["لوحه", "بالليت"],
    "لوحه": ["صلايه"],
    "مقمعه": ["صولجان", "دبوس", "راس صولجان"],
    "صولجان": ["مقمعه", "راس صولجان"],
    "ابو الهول": ["تمثال الاسد", "اسفنكس"],
    "اسفنكس": ["ابو الهول"],
    "مسله": ["اوبليسك"],
    "بردي": ["بردية", "بابيروس"],
    "تابوت": ["ساركوفاج", "ناووس"],
    "ناووس": ["تابوت", "ساركوفاج"],
    "موميا": ["موميه"],
    "موميه": ["موميا"],
    "متحف مصري كبير": ["جي اي ام"],
    "جي اي ام": ["متحف مصري كبير"],
    "متحف الحضاره": ["متحف الحضارة المصرية"],
}


def expand_query(s_norm: str) -> list[str]:
    base = [t for t in s_norm.split() if len(t) > 1]
    out = list(base)
    # also try multi-word keys
    for key, alts in SYNONYMS_AR.items():
        if key in s_norm:
            for a in alts:
                for t in a.split():
                    if t not in out:
                        out.append(t)
    for tok in base:
        for alt in SYNONYMS_AR.get(tok, []):
            for t in alt.split():
                if t not in out:
                    out.append(t)
    return out


def tokenize(s: str) -> list[str]:
    return expand_query(normalize_ar(s))


# ─── BM25 ────────────────────────────────────────────────────────────────
class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: list[list[str]] = []
        self.df: Counter[str] = Counter()
        self.idf: dict[str, float] = {}
        self.avgdl = 0.0
        self.N = 0

    def add(self, tokens: list[str]) -> None:
        self.docs.append(tokens)

    def build(self) -> None:
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(1, self.N)
        self.df.clear()
        for d in self.docs:
            for t in set(d):
                self.df[t] += 1
        self.idf = {
            t: math.log((self.N - df + 0.5) / (df + 0.5) + 1)
            for t, df in self.df.items()
        }

    def score(self, q: list[str], idx: int) -> float:
        d = self.docs[idx]
        if not d:
            return 0.0
        tf = Counter(d)
        dl = len(d)
        s = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = self.idf.get(term, 0.0)
            f = tf[term]
            s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

    def topk(self, q: list[str], k: int = 10) -> list[tuple[int, float]]:
        scored = []
        for i in range(self.N):
            sc = self.score(q, i)
            if sc > 0:
                scored.append((i, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


# ─── Engine ──────────────────────────────────────────────────────────────
class RAGEngine:
    """Loads chunks + builds BM25 index + (optionally) dense FAISS index."""

    def __init__(self, use_dense: bool = True) -> None:
        self.chunks: list[dict] = []
        self.bm25 = BM25Index()
        self.dense = None  # type: ignore[assignment]
        self.artifacts_index: dict[str, dict] = {}
        self.full_records_cache: dict[str, dict] = {}
        self.museums: list[dict] = []
        self.relations: dict[str, list[str]] = {}
        self.use_dense = use_dense
        # alias_to_artifact[normalized_alias] = artifact_id
        self.alias_to_artifact: dict[str, str] = {}
        self._load()
        if self.use_dense:
            try:
                from embeddings import DenseRetriever
                self.dense = DenseRetriever(self.chunks)
                print(f"[RAG] dense retriever ready ({len(self.chunks)} chunks, dim {self.dense.dim})")
            except Exception as e:
                print(f"[RAG] dense retriever DISABLED ({type(e).__name__}: {e})")
                self.dense = None

    def _load(self) -> None:
        with CHUNKS_PATH.open(encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                self.chunks.append(c)

        idx_path = DATA_DIR / "artifacts_index.json"
        if idx_path.exists():
            for r in json.loads(idx_path.read_text(encoding="utf-8")):
                self.artifacts_index[r["id"]] = r

        m_path = DATA_DIR / "_museums.json"
        if m_path.exists():
            self.museums = json.loads(m_path.read_text(encoding="utf-8"))

        r_path = DATA_DIR / "_relations.json"
        if r_path.exists():
            self.relations = json.loads(r_path.read_text(encoding="utf-8"))

        # Augment with museum + hall summaries as virtual chunks.
        for m in self.museums:
            mid = m["id"]
            for lang in ("ar", "en"):
                summary = (m.get("summary") or {}).get(lang, "")
                opened = m.get("opened", "")
                name_ar = m["names"]["ar"]
                name_en = m["names"]["en"]
                city = (m.get("city") or {}).get(lang, "")
                if summary:
                    text = (
                        f"{name_ar} ({name_en}) في {city}. "
                        + (f"افتُتح: {opened}. " if opened and lang == "ar" else (f"Opened: {opened}. " if opened else ""))
                        + summary
                    )
                    self.chunks.append({
                        "chunk_id": f"MUSEUM_{mid}__{lang}__0",
                        "artifact_id": f"MUSEUM_{mid}",
                        "lang": lang,
                        "text": text,
                        "name_ar": name_ar,
                        "name_en": name_en,
                        "museum_id": mid,
                        "primary_image": None,
                    })
            for h in m.get("halls", []):
                for lang in ("ar", "en"):
                    s = (h.get("summary") or {}).get(lang, "")
                    if s:
                        self.chunks.append({
                            "chunk_id": f"{h['id']}__{lang}__0",
                            "artifact_id": h["id"],
                            "lang": lang,
                            "text": f"{h['names'].get('ar', '')} - {h['names'].get('en', '')}: {s}",
                            "name_ar": h["names"].get("ar"),
                            "name_en": h["names"].get("en"),
                            "museum_id": mid,
                            "primary_image": None,
                        })

        # Inject ALIAS chunks so common alternative names are findable.
        from aliases import ALIASES
        for aid, names in ALIASES.items():
            ai = self.artifacts_index.get(aid) or {}
            primary_image = ai.get("primary_image")
            museum_id = ai.get("museum_id") or ""
            name_ar = ai.get("name_ar") or names[0]
            name_en = ai.get("name_en") or ""
            text = " · ".join(names + [name_ar, name_en])
            self.chunks.append({
                "chunk_id": f"ALIAS_{aid}",
                "artifact_id": aid,
                "lang": "ar",
                "text": text,
                "name_ar": name_ar,
                "name_en": name_en,
                "museum_id": museum_id,
                "primary_image": primary_image,
                "is_alias_chunk": True,
            })
            for n in names:
                self.alias_to_artifact[normalize_ar(n)] = aid

        # Build BM25
        for c in self.chunks:
            self.bm25.add(tokenize(c["text"]))
        self.bm25.build()

    def get_full_record(self, artifact_id: str) -> Optional[dict]:
        if artifact_id in self.full_records_cache:
            return self.full_records_cache[artifact_id]
        # Synthetic IDs for museums + halls
        if artifact_id.startswith("MUSEUM_"):
            mid = artifact_id.removeprefix("MUSEUM_")
            m = next((m for m in self.museums if m["id"] == mid), None)
            if m is None:
                return None
            rec = {
                "id": artifact_id,
                "kind": "museum",
                "names": {"ar": m["names"]["ar"], "en": m["names"]["en"]},
                "category": "متحف",
                "current_location": {
                    "city_ar": m["city"]["ar"],
                    "city_en": m["city"]["en"],
                    "country": m.get("country", ""),
                },
                "description": {
                    "ar": (m.get("summary") or {}).get("ar", ""),
                    "en": (m.get("summary") or {}).get("en", ""),
                },
                "halls": m.get("halls", []),
                "opened": m.get("opened", ""),
                "coordinates": m.get("coordinates"),
                "images": [],
                "qa_pairs_ar": [],
            }
            self.full_records_cache[artifact_id] = rec
            return rec
        for m in self.museums:
            for h in m.get("halls", []):
                if h["id"] == artifact_id:
                    rec = {
                        "id": artifact_id,
                        "kind": "hall",
                        "names": {"ar": h["names"]["ar"], "en": h["names"]["en"]},
                        "category": "قاعة عرض",
                        "current_location": {
                            "museum_id": m["id"],
                            "museum_ar": m["names"]["ar"],
                            "museum_en": m["names"]["en"],
                        },
                        "description": {
                            "ar": (h.get("summary") or {}).get("ar", ""),
                            "en": (h.get("summary") or {}).get("en", ""),
                        },
                        "images": [],
                        "qa_pairs_ar": [],
                    }
                    self.full_records_cache[artifact_id] = rec
                    return rec
        path = DATA_DIR / f"{artifact_id}.json"
        if not path.exists():
            return None
        rec = json.loads(path.read_text(encoding="utf-8"))
        self.full_records_cache[artifact_id] = rec
        return rec

    # ─── Hybrid retrieval ──────────────────────────────────────────────
    # Relevance thresholds tuned empirically against the eval set:
    #   * BM25 for an on-topic query about a known artifact lands at 15-35.
    #     Off-topic queries that incidentally share Arabic stop-words ("من هو",
    #     "مصر") inflate to 6-12 — that's the danger zone we need to filter out.
    #   * E5-small cosine on L2-normalized vectors: >=0.85 means truly topical
    #     (proper-noun hits land 0.88-0.92). Off-topic queries that just share
    #     domain-flavor (Egypt-related but irrelevant) hover at 0.78-0.83.
    # Either signal passing is enough — they fail differently. An alias-forced
    # match short-circuits both.
    MIN_BM25_FOR_CONFIDENT = 14.0
    MIN_DENSE_FOR_CONFIDENT = 0.85

    def retrieve(self, query: str, k: int = 5, lang: Optional[str] = None) -> list[dict]:
        """Hybrid BM25 + dense embeddings + alias lookup, fused via Reciprocal
        Rank Fusion. Annotates each returned chunk with `score` (RRF score) and
        the first item additionally carries `_top_bm25` / `_top_dense` so the
        caller can decide whether the result set is confident."""
        if not query.strip():
            return []

        # Step 0 — exact alias match (highest priority).
        q_norm = normalize_ar(query)
        forced_artifact: Optional[str] = self.alias_to_artifact.get(q_norm)
        # also try any subphrase match
        if not forced_artifact:
            for alias_norm, aid in self.alias_to_artifact.items():
                if alias_norm and alias_norm in q_norm and len(alias_norm) >= 4:
                    forced_artifact = aid
                    break

        # Step 1 — sparse BM25
        q_tokens = tokenize(query)
        bm25_results = self.bm25.topk(q_tokens, k=k * 6) if q_tokens else []
        top_bm25 = bm25_results[0][1] if bm25_results else 0.0

        # Step 2 — dense
        dense_results: list[tuple[int, float]] = []
        if self.dense is not None:
            try:
                dense_results = self.dense.search(query, k=k * 6)
            except Exception as e:
                print(f"[RAG] dense search error: {e}")
        top_dense = dense_results[0][1] if dense_results else 0.0

        # Step 3 — Reciprocal Rank Fusion
        rrf: dict[int, float] = {}
        K_RRF = 60
        for rank, (idx, _) in enumerate(bm25_results):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (K_RRF + rank)
        for rank, (idx, _) in enumerate(dense_results):
            rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (K_RRF + rank)

        # Title-match boost
        for idx in list(rrf.keys()):
            c = self.chunks[idx]
            name_ar = normalize_ar(c.get("name_ar") or "")
            if name_ar and name_ar in q_norm:
                rrf[idx] += 0.05  # tip-the-scales boost
            if forced_artifact and c["artifact_id"] == forced_artifact:
                rrf[idx] += 0.10  # alias-forced match

        # If forced_artifact has no chunks in rrf, add at least one.
        if forced_artifact and not any(self.chunks[i]["artifact_id"] == forced_artifact for i in rrf):
            for i, c in enumerate(self.chunks):
                if c["artifact_id"] == forced_artifact:
                    rrf[i] = 0.5
                    break

        # Lang preference (soft)
        if lang:
            for idx in list(rrf.keys()):
                if self.chunks[idx].get("lang") == lang:
                    rrf[idx] += 0.005

        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)
        out: list[dict] = []
        seen_chunk_ids: set[str] = set()
        for idx, score in ranked:
            c = self.chunks[idx]
            if c.get("is_alias_chunk"):
                continue  # alias chunks are routing helpers only
            if c["chunk_id"] in seen_chunk_ids:
                continue
            seen_chunk_ids.add(c["chunk_id"])
            r = {**c, "score": round(score, 4)}
            out.append(r)
            if len(out) >= k:
                break

        # Stash raw retriever signals on the first chunk so the caller can
        # decide whether the top hit is confident enough to surface.
        if out:
            out[0]["_top_bm25"] = round(top_bm25, 3)
            out[0]["_top_dense"] = round(top_dense, 3)
            out[0]["_alias_forced"] = forced_artifact is not None
        return out

    def is_confident(self, retrieved: list[dict]) -> bool:
        """Decide whether the top retrieval is good enough to claim a primary
        artifact. Off-topic queries get filtered out here so the UI doesn't
        attach a random artifact card to a "not found" answer."""
        if not retrieved:
            return False
        top = retrieved[0]
        # Alias-forced matches always win (the user typed a known synonym).
        if top.get("_alias_forced"):
            return True
        bm25_strong = top.get("_top_bm25", 0.0) >= self.MIN_BM25_FOR_CONFIDENT
        dense_strong = top.get("_top_dense", 0.0) >= self.MIN_DENSE_FOR_CONFIDENT
        # Either retriever is enough — they fail in different ways.
        return bm25_strong or dense_strong

    def answer(self, query: str, k: int = 5, mode: str = "extractive", lang: str = "ar") -> dict:
        retrieved = self.retrieve(query, k=k, lang=lang)
        confident = self.is_confident(retrieved)

        # Off-topic / low-confidence: return a clean "not found" response
        # without attaching an unrelated artifact card or fake sources.
        if not confident:
            no_match_ar = (
                "لم أجد معلومات كافية للإجابة عن هذا السؤال في قاعدة بياناتي. "
                "هذه القاعدة تغطي قطعًا أثرية مصرية محفوظة في المتحف المصري الكبير، "
                "المتحف المصري بالتحرير، والمتحف القومي للحضارة المصرية، إضافة إلى "
                "مجموعات مصرية مختارة في المتاحف العالمية. جرّب سؤالًا عن قطعة أو متحف بعينه."
            )
            return {
                "query": query,
                "answer": no_match_ar,
                "answer_en": (
                    "I couldn't find enough information to answer that in my knowledge "
                    "base, which covers Egyptian artifacts in the GEM, EMC, NMEC, and "
                    "selected world museums. Try asking about a specific artifact or museum."
                ),
                "sources": [],
                "primary_artifact_id": None,
                "primary_artifact": None,
                "related": [],
                "mode": "extractive",
                "low_confidence": True,
                "debug_scores": {
                    "top_bm25": retrieved[0].get("_top_bm25") if retrieved else None,
                    "top_dense": retrieved[0].get("_top_dense") if retrieved else None,
                },
            }

        primary_id = retrieved[0]["artifact_id"]
        primary_record = self.get_full_record(primary_id)

        has_llm_key = any(os.environ.get(k) for k in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"))
        if mode == "generative" and has_llm_key:
            answer_text, used_llm = self._generative_answer(query, retrieved, lang=lang)
            if not used_llm:
                mode = "extractive"  # LLM call failed; downgrade so UI knows
        else:
            answer_text = self._extractive_answer(query, retrieved, lang=lang)
            mode = "extractive"

        related_ids = self.relations.get(primary_id, [])[:6]
        related = [self.artifacts_index[rid] for rid in related_ids if rid in self.artifacts_index]

        sources_by_artifact: dict[str, dict] = {}
        for r in retrieved:
            aid = r["artifact_id"]
            if aid in sources_by_artifact:
                continue
            ai = self.artifacts_index.get(aid, {})
            sources_by_artifact[aid] = {
                "artifact_id": aid,
                "chunk_id": r["chunk_id"],
                "lang": r["lang"],
                "score": r["score"],
                "text": r["text"],
                "name_ar": r.get("name_ar") or ai.get("name_ar"),
                "name_en": r.get("name_en") or ai.get("name_en"),
                "primary_image": r.get("primary_image") or ai.get("primary_image"),
                "museum_id": r.get("museum_id") or ai.get("museum_id"),
                "museum_ar": ai.get("museum_ar"),
            }
        sources = list(sources_by_artifact.values())

        return {
            "query": query,
            "answer": answer_text,
            "sources": sources,
            "primary_artifact_id": primary_id,
            "primary_artifact": primary_record,
            "related": related,
            "mode": mode,
            "low_confidence": False,
            "debug_scores": {
                "top_bm25": retrieved[0].get("_top_bm25"),
                "top_dense": retrieved[0].get("_top_dense"),
                "alias_forced": retrieved[0].get("_alias_forced"),
            },
        }

    # ─── Answer generation ────────────────────────────────────────────
    def _extractive_answer(self, query: str, retrieved: list[dict], lang: str) -> str:
        top = retrieved[0]
        rec = self.get_full_record(top["artifact_id"])
        if rec is None:
            return _first_sentence(top["text"])
        if rec.get("kind") in ("museum", "hall"):
            return rec["description"].get("ar") or rec["description"].get("en") or _first_sentence(top["text"])

        q = normalize_ar(query)
        name_ar = rec["names"].get("ar") or rec["names"].get("en", "")
        loc = rec["current_location"]
        period = rec["period"]
        materials = rec.get("material") or []

        if any(k in q for k in ["اين", "موقع", "مكان", "في اي متحف", "في اي مدينه"]):
            place = (loc.get("museum_ar") or loc.get("museum_en") or "").strip()
            city = (loc.get("city_ar") or loc.get("city_en") or "").strip()
            hall = (loc.get("hall_ar") or "").strip()
            if not place:
                return _first_sentence(rec["description"].get("ar", "") or top["text"])
            parts = [f"تُعرض {name_ar} في {place}"]
            if city:
                parts.append(f"بمدينة {city}")
            if hall:
                parts.append(f"داخل {hall}")
            return "، ".join(parts) + "."

        if any(k in q for k in ["متي", "تاريخ", "اي عصر", "اي اسره", "تاريخ"]):
            p_ar = period.get("ar") or period.get("en") or ""
            d_ar = rec["dynasty"].get("ar") or rec["dynasty"].get("en") or ""
            yr_min = period.get("year_min")
            yr_max = period.get("year_max")
            yr = ""
            if yr_min is not None:
                yr = f" (حوالي {abs(yr_min)} {'ق.م' if yr_min < 0 else 'م'}"
                if yr_max and yr_max != yr_min:
                    yr += f"–{abs(yr_max)} {'ق.م' if yr_max < 0 else 'م'}"
                yr += ")"
            parts = [f"تعود {name_ar} إلى {p_ar}{yr}"]
            if d_ar:
                parts.append(f"خلال {d_ar}")
            return "، ".join(parts) + "."

        if any(k in q for k in ["مم", "مما", "اي ماده", "صنع", "مادتها"]):
            if materials:
                ms_ar_map = {
                    "gold": "الذهب", "silver": "الفضة", "bronze": "البرونز", "copper": "النحاس",
                    "limestone": "الحجر الجيري", "granite": "الجرانيت", "diorite": "الديوريت",
                    "basalt": "البازلت", "granodiorite": "الجرانوديوريت",
                    "wood": "الخشب", "cedar": "خشب الأرز", "ebony": "خشب الأبنوس",
                    "faience": "الفاينس", "lapis lazuli": "اللازورد",
                    "carnelian": "العقيق الأحمر", "turquoise": "الفيروز", "obsidian": "السبج",
                    "glass": "الزجاج", "glass paste": "عجينة زجاجية",
                    "linen": "الكتان", "papyrus": "ورق البردي",
                    "ivory": "العاج", "calcite": "الكالسيت", "greywacke": "الغريواكي",
                    "alabaster": "المرمر", "quartzite": "الكوارتزيت",
                    "anorthosite gneiss": "صخر الأنورثوزيت النيسي",
                    "pottery": "الفخار", "ceramic": "السيراميك", "earthenware": "الفخار",
                    "iron": "الحديد", "lead": "الرصاص",
                }
                ar_mats = [ms_ar_map.get(m.strip().lower(), m.strip()) for m in materials]
                return f"صُنعت {name_ar} من {' و'.join(ar_mats)}."

        if any(k in q for k in ["من اكتشف", "من وجد", "من العالم"]):
            year = rec.get("discovery", {}).get("year")
            who_en = rec.get("discovery", {}).get("by_en") or ""
            if year:
                if who_en:
                    return f"اكتُشفت {name_ar} عام {year} على يد {who_en}."
                return f"اكتُشفت {name_ar} عام {year}."

        if any(k in q for k in ["ما هي", "ما هو", "ماهي", "ماهو", "اخبرني", "احكي", "احك", "اوصف"]):
            intro = rec["description"].get("ar_intro") or _first_sentence(rec["description"].get("ar", ""))
            return intro

        return _first_two_sentences(top["text"])

    def _generative_answer(self, query: str, retrieved: list[dict], lang: str) -> tuple[str, bool]:
        """Returns (answer_text, used_llm). When the LLM call fails, returns
        the extractive answer and used_llm=False so the API can downgrade the
        `mode` field accordingly.
        """
        ctx = []
        for i, r in enumerate(retrieved[:5], start=1):
            name = r.get("name_ar") or r.get("name_en", "")
            ctx.append(f"[مرجع {i} — {name}]\n{r['text']}")
        context = "\n\n".join(ctx)

        system = (
            "أنت دليل سياحي خبير في الآثار المصرية القديمة والمتاحف. "
            "تجيب باللغة العربية الفصحى المبسطة. "
            "اعتمد فقط على المراجع المرفقة. إذا لم تكن المعلومات كافية، قل ذلك صراحة. "
            "اجعل الإجابة موجزة (٢-٤ جمل)، دقيقة، وموثوقة، دون افتراضات. "
            "لا تخترع أسماء أو تواريخ غير موجودة في المراجع."
        )
        user = (
            f"== المراجع ==\n{context}\n\n"
            f"== السؤال ==\n{query}\n\n"
            f"اكتب الإجابة فقط، بدون مقدمات."
        )
        try:
            grq = os.environ.get("GROQ_API_KEY")
            if grq:
                return _call_groq(system, user, grq), True
            ant = os.environ.get("ANTHROPIC_API_KEY")
            if ant:
                return _call_anthropic(system + "\n\n" + user, ant), True
            oai = os.environ.get("OPENAI_API_KEY")
            if oai:
                return _call_openai_chat(system, user, oai), True
        except Exception as e:
            print(f"[RAG] generative call failed: {e}")
        return self._extractive_answer(query, retrieved, lang), False


def _first_sentence(text: str) -> str:
    m = re.search(r"^(.{40,400}?[\.\!\؟])\s", text)
    return m.group(1).strip() if m else text[:300]


def _first_two_sentences(text: str) -> str:
    parts = re.split(r"(?<=[\.\!\؟])\s+", text.strip())
    return " ".join(parts[:2])[:600]


def _call_anthropic(prompt: str, key: str) -> str:
    import urllib.request
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return d["content"][0]["text"]


def _call_openai_chat(system: str, user: str, key: str) -> str:
    import urllib.request
    body = json.dumps({
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"].strip()


def _call_groq(system: str, user: str, key: str) -> str:
    """Groq's chat-completions API is OpenAI-compatible. Default model is the
    Llama 3.3 70B variant — strong multilingual including Arabic.
    """
    import urllib.request
    import urllib.error
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # Cloudflare blocks the default urllib UA. Use a real browser UA.
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return d["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        # Surface the actual Groq error message for easier debugging.
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            err_body = ""
        raise RuntimeError(f"Groq HTTP {e.code} (model={model}): {err_body}") from None
