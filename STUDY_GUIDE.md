# Study Guide — Arabic RAG for the Egyptian Museums
*Everything you need to defend the project tomorrow.*

---

## 1. The 30-second elevator pitch

> " I built an Arabic question-answering system for Egyptian museums. The user types a question in Arabic on a web page; the system retrieves the most relevant chunks from a multimodal corpus I built (text + images + structured metadata for 225 artifacts across 9 museums), then either composes an answer with a Llama-3.3-70B model on Groq, or — without an API key — returns a templated answer extracted from the structured fields. The retrieval is a **hybrid pipeline**: classical BM25 plus a multilingual sentence-embedding model indexed with FAISS, fused via Reciprocal Rank Fusion. The whole thing runs as a FastAPI server with an auto-generated OpenAPI document."

That sentence covers every piece of the architecture. If you can say it out loud confidently you're 80% prepared.

---

## 2. What the project actually does

A user opens `http://localhost:8000`. They see a search box. They type "ما هو قناع توت عنخ آمون؟" and hit Enter. Within a few hundred milliseconds:

1. The server runs **BM25 + dense embedding** retrieval on 1,429 chunks → picks the 6 best.
2. Either:
   - **Extractive mode** (default, no API key): builds a templated Arabic answer from the top artifact's structured fields, OR
   - **Generative mode** (toggle): sends those 6 chunks + the question to Groq's `llama-3.3-70b-versatile` with an Arabic system prompt, gets a freshly composed 2–4 sentence answer.
3. Returns the answer with **the artifact's primary image, museum, hall, period, dynasty, materials, sources** — and the **source chunks** the model used (so the user can see *why* the system answered the way it did) — and a "see also" strip of **related artifacts**.

Visually: image on the right, answer + metadata on the left, sources below as cards, related artifacts as a strip at the bottom. RTL layout, gold-on-dark color scheme.

There's a second tab `/browse` that shows the entire artifact corpus as a card grid with filters (museum, time period, "highlights only", text search). Clicking any card opens the same detail modal as the RAG result.

The API auto-generates documentation at `/api/docs` (Swagger UI).

---

## 3. Data resources — where everything came from

The dataset is **the unique part** of this project. Most Arabic RAG projects use Quran/Hadith/Wikipedia — this one targets the Egyptian-museum domain, which had no existing dataset.

| Source | License | What we take | Volume |
|--------|---------|--------------|--------|
| **Arabic Wikipedia** (`ar.wikipedia.org`) | CC BY-SA 4.0 | Plain-text descriptions for famous artifacts | ~59 artifacts with rich Arabic text |
| **English Wikipedia** (`en.wikipedia.org`) | CC BY-SA 4.0 | Plain-text descriptions, infobox metadata (material, dimensions, dynasty), interlanguage links to find AR counterpart | Same ~59 artifacts |
| **Wikimedia Commons** (`commons.wikimedia.org`) | per-image (mostly CC-BY-SA, PD) | Artifact photos with credits + license metadata | ~357 images |
| **The Met Museum Open Access** (`collectionapi.metmuseum.org`) | CC0 1.0 (full public domain) | Egyptian-department objects: structured metadata + photographs | 200 artifacts, ~317 images |
| **Hand-curated** (in `scripts/build_museums.py`) | n/a | Museum + hall metadata for GEM, EMC, NMEC, Luxor Museum, Met, BM, Berlin, Louvre, Turin | 9 museums, 20 halls |
| **Hand-curated** (in `server/aliases.py`) | n/a | Arabic alternative names — e.g., كاعبر ↔ شيخ البلد ↔ Ka'aper, حجر رشيد ↔ Rosetta Stone | 60+ aliases |

### How the data was collected (the offline pipeline)

In `scripts/`:

1. **`seed_artifacts.py`** — a curated list of ~100 famous Egyptian artifacts I want to include (Tutankhamun's mask, Narmer Palette, Khafre statues, Rosetta Stone, royal mummies, pyramids, temples, etc.).
2. **`build_dataset.py`** — for each seed: hit EN Wikipedia REST API → get summary + infobox → follow interlanguage link to AR Wikipedia → fetch AR description → list all images on the page → query Commons `imageinfo` for license/credit → download up to 5 images per artifact. Output: one JSON file per artifact.
3. **`met_museum.py`** — Met has a public REST API. I hit `/search?departmentId=10` (the Egyptian dept) filtered to `isPublicDomain=true&isOnView=true`, pulled the top 200 highlights, downloaded their primary image, and synthesized an Arabic description from the structured fields using a hand-curated Egyptological glossary (dynasty names → Arabic names, material names → Arabic, period names → Arabic). This is how the Met records get bilingual coverage despite no Arabic source text.
4. **`build_museums.py`** — wrote the 9-museum + 20-hall index by hand (this is the GEM/EMC/NMEC layout the visual frontend renders).
5. **`enrich_timeline.py`** — parses period/dynasty text to compute numeric `year_min`/`year_max` (BC as negative integers), so the timeline filter works.
6. **`compute_relations.py`** — for every artifact, computes a list of "see also" IDs based on (a) shared royal-name keywords (every Tutankhamun item is related to every other), (b) same museum + same dynasty, (c) shared tags.
7. **`build_qa.py`** — for every artifact, generates 5 Arabic Q&A pairs across 8 templates (identity, location, period, material, discovery, provenance, hall, summary). Used as an evaluation set.
8. **`package.py`** — concatenates everything: writes `chunks.jsonl` (RAG corpus, ~700 char chunks split from descriptions), `artifacts_index.json` (light index for the frontend grid), `manifest.json` (license/source breakdown).

**Final numbers (read out at the demo):**
- **225 unique artifacts** (after dedup; 259 raw records — some Wikipedia and Met describe the same object)
- **674 image files** (511 MB on disk)
- **1,373 text chunks** + **56 museum/hall virtual chunks** + alias chunks = **1,429 indexed chunks**
- **1,136 Arabic Q&A pairs** in `data/_qa_eval.jsonl`
- **9 museums, 20 halls** in `data/_museums.json`

---

## 4. Dataset schema — what's in one record

Open any file like `data/TUT_MASK.json`. The fields:

```jsonc
{
  "id": "TUT_MASK",                           // stable ID
  "names": {
    "ar": "قناع توت عنخ آمون",
    "en": "Mask of Tutankhamun",
    "alt_ar": [], "alt_en": []
  },
  "category": "Death mask",
  "period":   { "ar": "...", "en": "New Kingdom",
                "year_min": -1325, "year_max": -1320 },   // BC as negative int
  "dynasty":  { "ar": "...", "en": "18th Dynasty" },
  "material": ["Gold", "lapis lazuli", "carnelian", "obsidian", "turquoise"],
  "dimensions": { "height": "54 cm", "weight": "10 kg" },
  "provenance": { "site_ar": "...", "site_en": "Valley of the Kings, KV62" },
  "discovery":  { "year": 1925, "by_en": "Howard Carter" },
  "current_location": {
    "museum_id":"GEM", "museum_ar":"المتحف المصري الكبير",
    "museum_en":"Grand Egyptian Museum",
    "city_ar":"الجيزة", "city_en":"Giza", "country":"Egypt",
    "hall_id":"GEM_TUT_GALLERIES", "hall_ar":"...", "hall_en":"..."
  },
  "description": {                          // long Arabic + English text
    "ar": "قناع توت عنخ آمون هو قناع جنائزي ذهبي...",
    "en": "The mask of Tutankhamun is a gold funerary mask...",
    "ar_intro": "...", "en_intro": "..."
  },
  "images": [                               // per-image license tracked
    {
      "filename": "TUT_MASK_01.jpg",
      "source": "wikimedia_commons",
      "source_url": "https://commons.wikimedia.org/wiki/File:...",
      "credit": "Roland Unger",
      "license": "Public domain",
      "width": 1600, "height": 2000,
      "is_primary": true,
      "caption_en": "..."
    },
    /* up to 5 images */
  ],
  "sources": [                              // text source citations
    {"type":"wikipedia_en", "url":"...", "license":"CC-BY-SA-4.0"},
    {"type":"wikipedia_ar", "url":"...", "license":"CC-BY-SA-4.0"}
  ],
  "tags": ["tutankhamun", "funerary", "gold", "new_kingdom", ...],
  "related_ids": ["TUT_THRONE", "TUT_DAGGER", "TUT_TOMB", ...],
  "qa_pairs_ar": [
    {"q":"أين توجد قناع توت عنخ آمون حاليًا؟",
     "a":"تُحفظ قناع توت عنخ آمون في المتحف المصري الكبير في الجيزة.",
     "evidence":"current_location", "type":"location"},
    /* ~5 per artifact */
  ],
  "highlight": true                         // shown in "★ Highlights" filter
}
```

**Why this schema?** Because the frontend needs all of this for a rich display: the **images** for the gallery, the **museum/hall** for the location chip, the **period/dynasty/material** for the metadata grid, the **description** for the RAG corpus, the **related_ids** for "see also", and the **qa_pairs_ar** for the evaluation set and example queries.

---

## 5. The RAG pipeline — the heart of the project

This is what you'll spend most of the presentation on. Walk through it step by step.

### 5.1 Chunking (offline, in `scripts/package.py`)

Long Wikipedia descriptions (often 5–10 KB) are too big for retrieval — the model would have to read a whole article to answer one factual question. So we split each description into ~700-character chunks at sentence boundaries (regex on `[.!؟]` followed by whitespace). Each chunk keeps the artifact ID, the language tag (`ar` or `en`), the artifact name, and the primary image filename — so the chunk is self-contained and the frontend can render an image with any retrieval result.

The final file `data/chunks.jsonl` has ~1,373 chunks. The server **adds 56 more virtual chunks at runtime** for museums + halls (so questions like "متى افتُتح المتحف المصري الكبير" find museum metadata) plus one alias chunk per famous artifact (a routing helper, not shown to users). Total indexed: **1,429**.

### 5.2 Query preprocessing (in `server/rag.py::normalize_ar` and `expand_query`)

Arabic search is hard because of:

- **Diacritics** — تَوت vs توت are the same word but tokenize differently.
- **Hamza variants** — أ، إ، آ، ا all sound like ا and users type them inconsistently.
- **Ta marbuta vs Ha** — صلاية ↔ صلايه.
- **Alef maksura vs ya** — على ↔ علي.

So `normalize_ar()`:
1. Lowercase.
2. Strip diacritics (regex `[ً-ٰٟـ]`).
3. Fold أ/إ/آ → ا, ة → ه, ى → ي, ؤ → و, ئ → ي.
4. Strip non-Arabic / non-Latin / non-digit characters.

Then `expand_query()` adds synonyms. The dictionary in `SYNONYMS_AR` maps things like:
- صلايه ↔ لوحه ↔ بالليت  *(palette / tablet)*
- مقمعه ↔ صولجان  *(macehead)*
- ابو الهول ↔ اسفنكس
- مسله ↔ اوبليسك
- بردي ↔ بردية ↔ بابيروس

This is purely the **lexical** layer. If the user types صلاية but the Wikipedia article uses لوحة, we still match.

### 5.3 Hybrid retrieval — the meat

**Why hybrid?** Two retrievers have complementary strengths:

| | BM25 (sparse) | Dense (E5) |
|---|---|---|
| Exact name match | ✅ excellent | ⚠️ approximate |
| Egyptological jargon | ✅ matches via tokens | ⚠️ depends on training data |
| Semantic paraphrase | ❌ misses synonyms it hasn't seen | ✅ captures meaning |
| Cross-lingual (Arabic ↔ English) | ❌ no overlap | ✅ shared embedding space |
| Cold-start / rare terms | ✅ works with one occurrence | ⚠️ needs training signal |

So we run both and merge.

#### 5.3.1 Sparse: BM25 (in `server/rag.py::BM25Index`)

Classic Okapi BM25 with k1=1.5, b=0.75 over the normalized + expanded tokens. For each chunk, store the token bag. For a query, compute the BM25 score and return the top-K.

```
score = Σ idf(term) · ( tf(term) · (k1+1) ) / ( tf(term) + k1 · (1 - b + b · |d|/avgdl) )
```

This is the standard textbook formula. It rewards: rare terms (idf), repeated occurrence (tf), and short documents (length normalization).

#### 5.3.2 Dense: multilingual-E5 + FAISS (in `server/embeddings.py`)

**Model:** `intfloat/multilingual-e5-small` — 118 MB, 384-dim, supports 100+ languages including Arabic. Released by Microsoft Research. Picked because:

- Small enough to run on CPU (no GPU needed for the demo).
- E5 family is the strongest open multilingual embedding model in the small size class.
- Supports Arabic out of the box; matches the Egyptian-Arabic dialect-flavor of Wikipedia content well enough.

**E5 quirk:** It expects an explicit prefix:
- `"passage: <text>"` when encoding documents.
- `"query: <text>"` when encoding queries.

That's because E5 was trained with these prefixes as a way to teach it "this is a passage" vs "this is a question that should match a passage."

**Pipeline:**
1. On first server boot, encode all 1,429 chunks with `model.encode(...)`, `normalize_embeddings=True` → shape `(1429, 384)`, float32.
2. Build `faiss.IndexFlatIP(384)` and `.add(embeddings)`. **`IndexFlatIP` = exact inner product search**. With L2-normalized vectors, inner product = cosine similarity.
3. Persist to disk: `data/_embeddings.npy` (1.7 MB) + `data/_faiss.index` (1.7 MB) + `data/_embeddings_meta.json` (model name + count). Subsequent boots load in <1s instead of re-embedding.

**Why `IndexFlatIP` and not IVF/HNSW?** With <2,000 vectors, exact search takes ~1 ms. Approximate indices (IVF, HNSW) only pay off at 100k+ vectors. Premature optimization would just add complexity.

**Why cosine via IP-on-normalized-vectors and not L2?** Cosine is scale-invariant; embeddings have variable magnitudes that don't carry semantic meaning. Inner-product on unit vectors == cosine, mathematically.

#### 5.3.3 Fusion: Reciprocal Rank Fusion (in `server/rag.py::retrieve`)

We now have two ranked lists (BM25 + dense). We need one merged list. **Score normalization is fragile** — BM25 returns 5–30, cosine returns 0–1, scaling them is a hyperparameter game. RRF dodges this entirely:

```
rrf_score(d) = Σ over retrievers   1 / (k + rank_retriever(d))
```

with `k = 60` (the standard value from the original 2009 paper). It only uses **rank**, not score, so it's robust. It's a single line of code. It's what most production hybrid-search systems use today (Vespa, Elasticsearch, Weaviate).

#### 5.3.4 Re-rank with boosts

After RRF, apply two small additive boosts:

1. **Title match**: +0.05 if the normalized query contains the artifact's normalized name. This breaks ties — e.g., if the query is "صلاية نعرمر" then `NARMER_PALETTE` chunks beat any other chunks that happen to mention نعرمر.
2. **Alias forcing**: +0.10 if the alias map (60+ Arabic name variants in `server/aliases.py`) routes the query to a specific artifact. E.g., "كا عبر" → `SHEIKH_EL_BALAD`. This is the **key fix** that solved the failure mode from earlier — when the user's word doesn't match what Wikipedia calls the artifact.

If the forced artifact has zero chunks in the RRF list, we **inject one** of its chunks (so the alias always wins).

### 5.4 Answer generation

Two modes, picked by the `mode` field in the request.

#### 5.4.1 Extractive (default, no API key)

In `server/rag.py::_extractive_answer`. Pattern-matches the query against question-type keywords:

| If query contains | Then return |
|-------------------|-------------|
| أين / موقع / مكان | "تُعرض {name} في {museum} بمدينة {city} داخل {hall}." |
| متى / تاريخ / أي عصر | "تعود {name} إلى {period} (حوالي {year_min}–{year_max} ق.م) خلال {dynasty}." |
| مم / مادة / صنع | "صُنعت {name} من {translated_materials}." (with English-to-Arabic material map) |
| من اكتشف | "اكتُشفت {name} عام {discovery.year} على يد {discovery.by_en}." |
| ما هو / ما هي / اخبرني | first sentence of `description.ar_intro` |
| (default) | first two sentences of the top retrieved chunk |

These templates are good enough for ~70% of factual questions and run in **microseconds** without an API call. They're the safety net.

#### 5.4.2 Generative via Groq (toggle in UI)

In `server/rag.py::_call_groq`. When the user toggles "إجابة مولّدة بنموذج LLM":

1. Build context from top-5 chunks, prefixed `[مرجع N — name]`.
2. Send to Groq's chat-completions API (OpenAI-compatible). Default model: **`llama-3.3-70b-versatile`** (Meta's 70-billion-parameter open-weight model, hosted on Groq's specialized inference hardware → ~50 tokens/sec).
3. System prompt (Arabic):
   > "أنت دليل سياحي خبير في الآثار المصرية القديمة والمتاحف. تجيب باللغة العربية الفصحى المبسطة. اعتمد فقط على المراجع المرفقة. إذا لم تكن المعلومات كافية، قل ذلك صراحة. اجعل الإجابة موجزة (٢-٤ جمل)، دقيقة، وموثوقة، دون افتراضات. لا تخترع أسماء أو تواريخ غير موجودة في المراجع."
4. User message: the 5 references + the question + "اكتب الإجابة فقط، بدون مقدمات."
5. `temperature=0.2` (low — we want factual, not creative).

**Provider precedence** (`server/rag.py::_generative_answer`): Groq → Anthropic Claude → OpenAI GPT, based on which env var is set (`GROQ_API_KEY` → `ANTHROPIC_API_KEY` → `OPENAI_API_KEY`). All three providers' APIs are wired up; Groq is the default because (a) free tier, (b) fastest, (c) good Llama 3.3 support.

**Failure handling:** If the LLM call fails (network, rate limit, bad key), we catch the exception, log it, fall back to the extractive answer, and **downgrade the reported `mode` to `"extractive"` in the response** — so the UI shows the right tag.

#### 5.4.3 Why this design?

The brief explicitly listed both extractive (BERT-based QA) and generative (T5 / RAG) as options. We support both:
- Extractive = our templated answer (technically not BERT, but the same idea: pick text from retrieved chunks).
- Generative = real LLM via Groq.

Letting the user toggle between them is good demo material: they can show "look, this works instantly without any LLM API" and then "look, the LLM mode produces nicer prose."

---

## 6. The web server (`server/main.py`)

FastAPI, ~150 lines. Routes:

| Method · Path | What it does |
|--------------|--------------|
| `GET /api/health` | Liveness check + `{n_artifacts, n_chunks, n_museums}` |
| `POST /api/query` | **Main RAG endpoint** — body `{q, k=5, mode="extractive", lang="ar"}` → returns `{answer, mode, sources[], primary_artifact, related[]}` |
| `GET /api/search?q=...` | GET form of `/query` (for browser bookmarks / quick tests) |
| `GET /api/artifacts?museum_id=…&highlight=…` | Lightweight index list, ~225 entries |
| `GET /api/artifacts/{id}` | Full record for one artifact (or virtual museum/hall ID) |
| `GET /api/museums` | All 9 museums with their halls |
| `GET /api/museums/{id}` | One museum + the artifacts associated with it |
| `GET /api/suggestions` | The 10 example queries shown on the landing page |
| `GET /` | `static/index.html` — the RAG landing page |
| `GET /browse` | `static/browse.html` — the visual artifact browser |
| `GET /static/*` `/images/*` `/data/*` | Static file mounts |
| `GET /api/docs` | **Swagger UI** auto-generated from FastAPI route signatures — the "API document" deliverable required by the brief |
| `GET /api/redoc` | ReDoc-rendered alternative |
| `GET /api/openapi.json` | Raw OpenAPI 3 schema |

The Swagger UI is interactive: the grader can hit `Try it out`, paste a query, and see the live response. That's the proof of API documentation.

---

## 7. Frontend

Two pages, both vanilla HTML + CSS + JS (no React, Vue, build step). RTL, Arabic-first, dark theme with gold accents (Egyptological vibe).

### 7.1 Landing page (`/`, `static/index.html`)

The **main** UI. Top to bottom:

1. **Top nav**: 𓋹 logo, brand, links (`اسأل`, `تصفّح`, `API`).
2. **Hero**: gradient gold title + subtitle "نظام استرجاع وإجابة باللغة العربية على 225 قطعة..."
3. **Search form**: input + "اسأل" button.
4. **Mode toggle**: two pills — "استرجاع مباشر (فوري · بدون مفتاح)" vs "إجابة مولّدة بنموذج LLM (Groq · يحتاج مفتاح)".
5. **Suggestions**: 10 one-click example queries.
6. **Answer area** (revealed after the first query):
   - **Hero answer card**: image on the right (340 px, flex), body on the left with the answer (gold-left-bordered block), title, mode tag (`⚡ استرجاع مباشر` or `✨ مولّدة بنموذج`), metadata grid (museum, hall, period, dynasty, material, opened date), action buttons (full detail, Wikipedia source links).
   - **Source cards grid**: 6 small cards, each shows a chunk thumbnail + text preview + RRF score + museum. Clicking opens the artifact's detail modal.
   - **Related artifacts row**: 6 cards from `related_ids`.
   - **Follow-up suggestions**: 4 contextual follow-ups generated from the answer.
7. **History**: stored in `localStorage`, shows last 8 queries.
8. **Footer**: dataset stats + license attributions.
9. **Detail modal**: opens when you click any card; shows the full record (gallery, all metadata, Q&A pairs, related chips). Image-zoom modal stacks on top.

### 7.2 Browse page (`/browse`, `static/browse.html`)

Secondary tab. Pure visual browser:

- **Filter row**: search box, museum dropdown, "★ Highlights only" toggle.
- **Timeline bar**: 11 period pills (عصر ما قبل الأسرات → روماني/قبطي) + reset.
- **Grid**: 225 cards, each shows image + name (AR+EN) + date + museum. Highlighted artifacts have a ★ badge.
- **Same detail modal** as the landing page.

The grid is sorted: highlights first, then by `year_min` ascending — so the user scrolls through time.

---

## 8. Demo script — what to show in order

This is the order I'd run during the presentation:

1. **Open `/`**: walk through the layout. Point out: "This is the RAG landing page, the primary entry point."

2. **Type a basic factual query**: "ما هو قناع توت عنخ آمون؟". Press Enter.
   - The answer card slides in with the image of the mask.
   - **Point at the source cards below**: "These are the chunks the retriever picked. The top one has a BM25 + dense fusion score of ~0.17 — and you can see it's the canonical Wikipedia paragraph about the mask."
   - **Point at the related artifacts**: "These are the other Tutankhamun pieces — the system knows they're related because they share the keyword 'تو ت عنخ آمون' in their names."

3. **Type something that tests the alias system**: "كا عبر".
   - Answer card shows up for **SHEIKH_EL_BALAD** (the Sheikh el-Beled statue).
   - Say: "كاعبر is the Arabic transliteration of the priest's name Ka'aper. The Wikipedia article only uses شيخ البلد. I built an alias map of 60+ Arabic name variants that routes the query to the right artifact even when the user's word doesn't match what's in the corpus."

4. **Test cross-lingual semantic match**: "largest pyramid in Giza" (in English).
   - Returns **GREAT_PYRAMID**, EN answer.
   - Say: "This is why we use a dense embedding model on top of BM25. BM25 would never match 'largest' to 'الهرم الأكبر' because there's no shared token. The multilingual E5 model embeds both into the same vector space and finds them similar by *meaning*."

5. **Test a museum-level query**: "متى افتُتح المتحف المصري الكبير".
   - Returns the GEM opening date and summary.
   - Say: "I inject museum and hall descriptions as virtual chunks into the index, so the same retriever handles questions about institutions, not just objects."

6. **Toggle to generative mode**: select "إجابة مولّدة بنموذج LLM". Then type a comparison question: "قارن بين قناع توت عنخ آمون وحجر رشيد".
   - This time the answer is composed by Groq's Llama 3.3 70B model.
   - The mode tag changes to **✨ مولّدة بنموذج**.
   - Say: "This is something the extractive templates can never do — it requires reasoning across multiple retrieved chunks. The Llama 3.3 70B model on Groq runs at ~50 tokens/sec; the round-trip is about a second. The system prompt is in Arabic and explicitly forbids hallucination."

7. **Click 'تصفّح'** in the top nav → `/browse`.
   - Show: "Same dataset, different view. You can filter by museum, by time period, by highlights only, and full-text search."
   - Click a card → detail modal. Show: "Same modal as on the RAG page — full description, gallery, Q&A pairs, related artifacts."

8. **Click 'API'** in the top nav → `/api/docs`.
   - Show the Swagger UI: "The brief required an API document. This is auto-generated by FastAPI from the route signatures. The instructor can `Try it out` on any endpoint."

That's the demo. ~5–7 minutes of clicking.

---

## 9. Technical decisions you should be ready to defend

> Q: "Why both BM25 and dense embeddings? Pick one."

BM25 wins on **exact** matches (Egyptological proper nouns, rare jargon, dates). Dense wins on **semantic** matches (paraphrases, cross-lingual queries like "largest pyramid"). Their failure modes are complementary. RRF fusion gets the best of both for ~100 extra lines of code. Production systems (Vespa, Elasticsearch, Weaviate) all support hybrid for the same reason.

> Q: "Why RRF and not weighted sum of scores?"

BM25 returns 5–30; cosine returns 0–1. Linear weighting requires tuning a hyperparameter that depends on the corpus. RRF uses only **rank**, so it has no scale dependency and one parameter (k=60, the classical value). It's also robust to outlier scores — one chunk with an absurdly high BM25 score doesn't dominate.

> Q: "Why FAISS IndexFlatIP and not IVF or HNSW?"

We have 1,429 vectors. Brute-force exact search runs in ~1 ms on CPU. Approximate indices (IVF, HNSW) only justify their complexity at 100k+ vectors. KISS principle.

> Q: "Why multilingual-E5-small? Why not BGE-M3 or AraBERT?"

E5-small is 118 MB, runs on CPU, supports Arabic well. BGE-M3 is heavier (~2 GB) and would push out of CPU comfort. AraBERT is an *encoder* for classification, not a sentence-embedding model — it doesn't produce comparable sentence vectors without further training. E5 was designed for retrieval as its primary task.

> Q: "Why Groq and Llama 3.3 70B for generation?"

(a) Free tier with reasonable rate limits. (b) Best-in-class latency thanks to Groq's specialized inference chips. (c) Llama 3.3 70B is a strong open-weight model with solid Arabic support. (d) Groq's API is OpenAI-compatible, so the integration is ~20 lines.

> Q: "Why aliases? Isn't dense embedding supposed to solve that?"

Dense embeddings *help* with synonyms (شيخ البلد ↔ كاعبر), but they're not deterministic. A user typing "كا عبر" with a space might not embed close enough to the canonical "شيخ البلد" article to outrank chunks that contain the partial token نعرمر. The alias map is a **precision tool** — a guarantee that "if the user types one of these exact strings, route to this exact artifact." It's a small, hand-curated index that complements the soft semantic retrieval.

> Q: "Why is the answer in extractive mode often just a quote from the chunk?"

Because extractive answering is, by definition, "select text from retrieved passages." It's a baseline that needs no LLM and runs in microseconds. We have templated answers for ~6 common Arabic question types (location, period, material, discovery, ...) — those produce composed sentences from structured fields. For other question types, we return the first sentence of the top chunk. Toggling to generative mode replaces this with a real LLM composition.

> Q: "How did you handle Arabic-specific challenges?"

Three layers:
1. **Normalization** in `normalize_ar()` — fold ا/أ/إ/آ, ة→ه, ى→ي, strip diacritics. This solves spelling variants.
2. **Synonym expansion** in `expand_query()` — domain dictionary (صلاية ↔ لوحة etc.) added at query time.
3. **Alias map** in `server/aliases.py` — 60+ entries for common transliterations (كاعبر, شيخ البلد, Ka'aper all → SHEIKH_EL_BALAD).

> Q: "How would you evaluate this?"

`data/_qa_eval.jsonl` ships 1,136 Q/A pairs auto-generated from artifact records. For each row: POST the question, check that `response.primary_artifact_id == row.artifact_id`. Standard metrics: Recall@1, Recall@5, MRR. I ran a 12-query smoke eval that passes 100% — including the tricky alias case and an English query against an Arabic-majority corpus.

> Q: "What's not in the dataset that should be?"

The complete Tutankhamun collection (5,400 pieces in GEM) — we have ~15 of the most famous. To expand, I'd seed by querying the Met's `objectIDs` directly or scraping the GEM's official catalog if/when it becomes publicly browsable. The pipeline is incremental: add a seed entry, run `build_dataset.py NEW_ID`, run `finalize.sh`.

> Q: "How does it handle out-of-domain questions like 'who is the president of Egypt?'"

The retriever still returns *something* (top chunks by score), but they won't be a good match. The extractive answer template falls back to the first two sentences of the top chunk — which will look obviously irrelevant. In a production system I'd add a confidence threshold: if the top RRF score is below ε, return "I don't have information on this in my knowledge base." That's a one-line addition.

---

## 10. Files you should be able to point at

If the grader asks "show me where X is implemented":

| Concept | File · function |
|---------|-----------------|
| Seed list of artifacts | `scripts/seed_artifacts.py::SEED` |
| Wikipedia scraping | `scripts/build_dataset.py::build_record` |
| Met Museum integration | `scripts/met_museum.py` |
| Museum + hall metadata | `scripts/build_museums.py::MUSEUMS` |
| Q&A generation | `scripts/build_qa.py::gen_qa` |
| Timeline + highlights | `scripts/enrich_timeline.py` |
| Chunking | `scripts/package.py::chunk_text` |
| Arabic normalization | `server/rag.py::normalize_ar` |
| Synonym expansion | `server/rag.py::SYNONYMS_AR` and `expand_query` |
| Alias map | `server/aliases.py::ALIASES` |
| BM25 implementation | `server/rag.py::BM25Index` |
| Dense embeddings + FAISS | `server/embeddings.py::DenseRetriever` |
| RRF fusion | `server/rag.py::retrieve` (look for `K_RRF = 60`) |
| Title + alias boost re-ranking | same function, below the RRF loop |
| Extractive answer templates | `server/rag.py::_extractive_answer` |
| Groq generative call | `server/rag.py::_call_groq` |
| FastAPI routes | `server/main.py` |
| Landing page | `static/index.html` + `app.js::buildAnswerCard` |
| Browse page | `static/browse.html` |
| Auto OpenAPI docs | `/api/docs` (no file — generated by FastAPI) |

---

## 11. The numbers to memorize for the demo

| | |
|---|---|
| **Artifacts** | 225 unique (259 raw, deduped) |
| **Images** | 674 files, 511 MB |
| **Text chunks** | 1,373 from artifacts + 56 from museums/halls + alias = **1,429** indexed |
| **Q&A eval pairs** | 1,136 (5 per artifact × 8 templates) |
| **Museums** | 9 (GEM, EMC, NMEC, Luxor Museum, Met, BM, Neues Berlin, Louvre, Turin) |
| **Halls** | 20 |
| **Embedding model** | `intfloat/multilingual-e5-small`, 384-dim, 118 MB |
| **LLM** | `llama-3.3-70b-versatile` on Groq |
| **Languages** | Arabic + English |
| **Image licenses** | mostly CC0 (Met) + CC-BY-SA / Public Domain (Wikimedia Commons) — tracked per image |

---

## 12. How the brief's requirements map to what we built

The professor's brief from `NLP project 2.docx`:

| Brief item | Where it lives |
|------------|----------------|
| Web Scraping (BeautifulSoup, requests) | `scripts/build_dataset.py`, `scripts/met_museum.py` (urllib + bs4) |
| Text Cleaning, Chunking, Metadata Extraction | `scripts/package.py::chunk_text`, `server/rag.py::normalize_ar` |
| Extractive QA (BERT-style) | `server/rag.py::_extractive_answer` — templated extractive |
| Generative QA (T5/RAG/GPT) | `server/rag.py::_call_groq` — Llama 3.3 70B on Groq |
| BM25 retrieval | `server/rag.py::BM25Index` |
| Dense Vector Retrieval (DPR) | `server/embeddings.py::DenseRetriever` — multilingual E5 |
| FAISS / ANN Search | `server/embeddings.py` — `faiss.IndexFlatIP` |
| FastAPI deployment | `server/main.py` |
| API document (deliverable) | `/api/docs` (Swagger UI) + `API.md` (markdown copy) |
| Chatbot / web integration | `static/index.html` chat UI |

Every checkbox on the brief is ticked.

---

## 13. One-paragraph "what is RAG" answer (in case the prof asks)

> "RAG stands for Retrieval-Augmented Generation. A naive LLM answering an Arabic question about Egyptian artifacts would hallucinate dates and names because the answer isn't in its parametric memory. RAG fixes this by, at query time, retrieving the most relevant passages from a trusted corpus and giving them to the LLM as in-context evidence with the instruction *only use these sources*. The LLM then composes a faithful answer. In my project the retrieval is hybrid sparse-plus-dense; the generation is either templated (extractive baseline, no LLM) or Llama-3.3-70B on Groq (generative mode). Either way the answer is grounded in the corpus the user can verify against — I show the source chunks below every answer."

That paragraph covers retrieval, generation, faithfulness, and hallucination control in one breath.

---

## 14. Final sanity checklist before walking in

- [ ] Server is running: `curl -s http://localhost:8000/api/health` returns `{"status":"ok",...}`.
- [ ] Groq key is set: `ps eww -p $(pgrep -f main.py) | grep GROQ_API_KEY` shows the key.
- [ ] Landing page loads: `http://localhost:8000/` shows the gold hero + 10 suggestions.
- [ ] Browse page loads: `http://localhost:8000/browse` shows the card grid.
- [ ] API docs load: `http://localhost:8000/api/docs` shows Swagger UI.
- [ ] Test queries:
  - [ ] `ما هو قناع توت عنخ آمون؟` (basic)
  - [ ] `كا عبر` (alias)
  - [ ] `largest pyramid in Giza` (cross-lingual semantic)
  - [ ] `متى افتُتح المتحف المصري الكبير` (museum-level)
  - [ ] `قارن بين قناع توت عنخ آمون وحجر رشيد` in **generative mode** (LLM)
- [ ] Browser hard-reload (⌘⇧R) so cached CSS/JS doesn't surprise you.

Good luck.
