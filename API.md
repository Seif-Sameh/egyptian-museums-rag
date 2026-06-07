# API Documentation — Egyptian Museums RAG

The server is built with FastAPI and exposes both an interactive OpenAPI/Swagger console and a ReDoc-rendered version. While the server is running:

- **Interactive console:** http://localhost:8000/api/docs
- **ReDoc rendering:** http://localhost:8000/api/redoc
- **Raw OpenAPI schema:** http://localhost:8000/api/openapi.json

This document mirrors that schema in plain Markdown for the project submission.

---

## Base URL

```
http://localhost:8000
```

CORS is open (`*`) to simplify the demo. All endpoints return JSON unless noted. Arabic text is UTF-8 encoded; the responses set `Content-Type: application/json; charset=utf-8`.

---

## Endpoints

### `GET /api/health`

Liveness check + dataset size.

**Example**
```bash
curl http://localhost:8000/api/health
```
```json
{
  "status": "ok",
  "n_artifacts": 225,
  "n_chunks": 1373,
  "n_museums": 9
}
```

---

### `POST /api/query`  *(main RAG endpoint)*

Ask a question in Arabic (or English). Returns an answer plus the retrieved
source chunks, the primary artifact's full record, and related artifacts.

**Request body**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `q`    | string  | — (required) | The natural-language question. |
| `k`    | integer | `5` | Number of source chunks to return (1–20). |
| `mode` | string  | `"extractive"` | `"extractive"` (default, no API key needed) or `"generative"` (uses Anthropic/OpenAI key from env). |
| `lang` | string  | `"ar"` | Preferred language for retrieval and answer (`"ar"` or `"en"`). |

**Example**
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"q":"أين توجد صلاية نعرمر؟","k":5,"mode":"extractive","lang":"ar"}'
```

**Response shape**
```json
{
  "query": "أين توجد صلاية نعرمر؟",
  "answer": "تُعرض صلاية نعرمر في المتحف المصري بالقاهرة...",
  "mode": "extractive",
  "sources": [
    {
      "artifact_id": "NARMER_PALETTE",
      "chunk_id": "NARMER_PALETTE__ar__0",
      "lang": "ar",
      "score": 28.4,
      "text": "...full chunk text...",
      "name_ar": "لوحة نعرمر",
      "name_en": "Narmer Palette",
      "primary_image": "NARMER_PALETTE_01.jpg",
      "museum_id": "EMC",
      "museum_ar": "المتحف المصري بالتحرير"
    }
  ],
  "primary_artifact_id": "NARMER_PALETTE",
  "primary_artifact": { "id": "...", "names": {...}, "description": {...}, "images": [...], ... },
  "related": [ { "id": "BULL_PALETTE", "name_ar": "...", "primary_image": "..." } ]
}
```

**Generative mode**

To enable LLM-composed answers, set one of these environment variables before
starting the server and pass `"mode": "generative"` in the request:

```bash
# Groq (free, fast, recommended)
export GROQ_API_KEY=gsk_...
# Optional: override the model (default: llama-3.3-70b-versatile)
export GROQ_MODEL=llama-3.3-70b-versatile

# Or Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Or OpenAI
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini  # optional override

python3 server/main.py
```

Provider precedence: Groq → Anthropic → OpenAI. If no key is set, the request
silently falls back to `"extractive"` mode. The provider used is reflected in
the `mode` field of the response (`"generative"` or `"extractive"`).

The Arabic system prompt instructs the model to answer in MSA, only from the
retrieved chunks, in 2-4 sentences, without hallucinating. Get a free Groq key
at https://console.groq.com/keys.

---

### `GET /api/search`

GET form of `/api/query` — convenient for browser bookmarks and quick tests.

```bash
curl "http://localhost:8000/api/search?q=ما%20هو%20حجر%20رشيد&k=3"
```

Same query parameters as `POST /api/query`. Response is identical.

---

### `GET /api/artifacts`

Lightweight list of all artifacts (one entry per artifact). Use this for grid views.

**Query params**
| Param | Description |
|-------|-------------|
| `museum_id` | optional — filter to one museum (`"GEM"`, `"EMC"`, `"NMEC"`, `"MET"`, ...) |
| `highlight` | optional bool — only must-see pieces |
| `limit`     | default `1000` |

**Example**
```bash
curl "http://localhost:8000/api/artifacts?museum_id=GEM&highlight=true"
```
Response: array of small index records (`id`, `name_ar`, `name_en`, `primary_image`, `period_ar`, `year_min`, `year_max`, `highlight`, `museum_id`, `tags`, etc.).

---

### `GET /api/artifacts/{id}`

Full artifact record — used by the detail panel.

```bash
curl http://localhost:8000/api/artifacts/TUT_MASK
```

Returns the full schema (see `dataset/data/<ID>.json`): names (AR/EN/alt), period, dynasty, material, dimensions, provenance, discovery, current location (museum + hall + city), description (AR/EN, intro + full), images (filename + license + credit), sources, tags, related_ids, qa_pairs_ar.

Synthetic IDs starting with `MUSEUM_` (e.g. `MUSEUM_GEM`) and hall IDs (e.g. `GEM_GRAND_STAIRCASE`) are also routable — they return a record-like response for the museum or hall.

---

### `GET /api/museums`

List of all museums with their halls.

```bash
curl http://localhost:8000/api/museums
```

Each museum carries `id`, `names.ar/en`, `city.ar/en`, `country`, `coordinates`, `opened`, `summary.ar/en`, and a `halls[]` array.

---

### `GET /api/museums/{id}`

One museum + the artifacts currently associated with it.

```bash
curl http://localhost:8000/api/museums/GEM
```

Returns the museum record plus an `artifacts[]` array containing all index entries whose `museum_id == id`.

---

### `GET /api/suggestions`

A curated list of example queries shown on the landing page as one-click pills.

```bash
curl http://localhost:8000/api/suggestions
```

```json
[
  {"q": "ما هو قناع توت عنخ آمون؟", "icon": "🪙"},
  {"q": "أين توجد صلاية نعرمر؟", "icon": "🗿"},
  ...
]
```

---

## Static routes (web app)

| Path | What it serves |
|------|----------------|
| `/` | RAG landing page (`static/index.html`) — main UI |
| `/browse` | Visual browser (`static/browse.html`) — secondary tab |
| `/static/{file}` | CSS, JS for the frontend |
| `/images/{file}` | Downloaded artifact images |
| `/data/{file}` | Raw dataset files (per-artifact JSON, chunks.jsonl, etc.) |
| `/api/docs` | Interactive Swagger UI |
| `/api/redoc` | ReDoc rendering |
| `/api/openapi.json` | Raw OpenAPI 3 schema |

---

## Running

```bash
cd "Arabic RAG Project/dataset"
pip3 install fastapi uvicorn
python3 server/main.py
# → http://localhost:8000
```

---

## Retrieval pipeline (under the hood)

The pipeline matches the project brief's "Search & Retrieval Mechanism — BM25 or Dense Vector Retrieval (DPR), FAISS / ANN Search":

1. **Query preprocessing**
   - Arabic-aware normalization (drop diacritics, fold ا/أ/إ/آ, ة→ه, ى→ي)
   - Synonym expansion (e.g., "صلاية" ↔ "لوحة")
   - **Alias lookup** against a curated map (e.g., "كاعبر" → SHEIKH_EL_BALAD, "حجر رشيد" → ROSETTA_STONE) — see `server/aliases.py`

2. **Hybrid retrieval** — runs both retrievers in parallel:
   - **Sparse: BM25** — `server/rag.py::BM25Index`, classic tf-idf with k1=1.5, b=0.75 over normalized + expanded tokens.
   - **Dense: multilingual-E5 + FAISS** — `intfloat/multilingual-e5-small` (118MB, 384-dim, supports Arabic). Embeddings are persisted to `data/_embeddings.npy` and a FAISS `IndexFlatIP` (inner product on L2-normalized vectors = cosine similarity) is persisted to `data/_faiss.index`. First-run build is ~30s; subsequent starts load in <1s.
   - **Fusion: Reciprocal Rank Fusion (RRF)** — merges the two rankings via `Σ 1 / (60 + rank)`. RRF is the standard hybrid-search recipe and needs no score normalization.
   - **Title-match + alias boost** — small additive bonus when the user's query contains the artifact's name or matches a known alias.

3. **Answer generation**
   - *Extractive* (default, no API key required) — detects the question type (where / when / what material / who discovered / generic identity) and assembles a short Arabic answer using the top artifact's structured fields. Falls back to the first sentence of the top chunk.
   - *Generative* — set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in env and pass `"mode": "generative"` to call Claude Haiku 4.5 or GPT-4o-mini with the top-K chunks as RAG context.

4. **Augmentation** — the response carries the full artifact record (with image gallery, license info, museum/hall location), source-chunk cards (so the frontend can show *what* was retrieved), and related artifacts from `data/_relations.json`.

---

## Evaluation

A pre-baked Arabic eval set ships at `data/_qa_eval.jsonl`:

```json
{"artifact_id": "TUT_MASK", "name_ar": "قناع توت عنخ آمون",
 "question": "أين توجد قناع توت عنخ آمون حاليًا؟",
 "answer": "تُحفظ قناع توت عنخ آمون في المتحف المصري الكبير في الجيزة.",
 "type": "location", "evidence_field": "current_location"}
```

For each row, send `question` to `POST /api/query` and verify that `primary_artifact_id == artifact_id`. Standard metrics: Recall@1, Recall@5, MRR.
