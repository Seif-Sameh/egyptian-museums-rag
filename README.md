# Egyptian Museums Multimodal Dataset & RAG (Arabic)

A bilingual (Arabic / English) multimodal dataset of Egyptian artifacts plus a working **hybrid-retrieval RAG** server (BM25 + multilingual dense embeddings + FAISS) and a visual frontend. Built for a Website QA NLP project on the Grand Egyptian Museum, the Egyptian Museum at Tahrir, the National Museum of Egyptian Civilization, and Egyptian holdings in major world museums (the Met, British Museum, Berlin's Neues Museum, the Louvre, Turin).

## Quick start

```bash
cd "Arabic RAG Project/dataset"
pip3 install -r requirements.txt
python3 server/main.py
# → http://localhost:8000           (RAG landing page)
# → http://localhost:8000/browse    (visual artifact browser)
# → http://localhost:8000/api/docs  (Swagger UI / API document)
```

First run downloads `intfloat/multilingual-e5-small` (~118 MB) and embeds 1,400+ chunks (~30s).
Subsequent runs read the persisted FAISS index in <1s.

## Pipeline architecture

```
            ┌──────── User question (Arabic / English) ────────┐
            │                                                   │
            ▼                                                   ▼
   Arabic normalize + synonym expand              multilingual-E5 embedding
   + alias lookup (e.g. كا عبر → ID)                          │
            │                                                   ▼
            ▼                                          FAISS IndexFlatIP
   BM25 over 1,400+ chunks                            (cosine on L2-norm)
            │                                                   │
            └──────────── Reciprocal Rank Fusion ──────────────┘
                                  │
                                  ▼
                  Title-match + alias rank boost
                                  │
                                  ▼
            ┌─── extractive answer (no API key) ────┐
            │   templated from structured fields    │
            │                                        │
            └─── generative answer (Anthropic /     │
                 OpenAI key in env, optional) ──────┘
                                  │
                                  ▼
        Augment with primary artifact record + related artifacts
```

The dataset itself was built first; see "Building the dataset" below for the scraping pipeline.

## What's in here

```
dataset/
├── server/                       # FastAPI RAG server
│   ├── main.py                  # routes, OpenAPI docs
│   ├── rag.py                   # hybrid retrieval + answer generation
│   ├── embeddings.py            # E5 + FAISS dense retriever
│   └── aliases.py               # Arabic alias map (كا عبر → SHEIKH_EL_BALAD, …)
├── static/                       # frontend
│   ├── index.html               # RAG landing page (chat-style UI)
│   ├── browse.html              # visual artifact browser (secondary tab)
│   ├── app.css, app.js          # shared assets
├── data/
│   ├── artifacts.jsonl          # one record per line, full schema
│   ├── artifacts_index.json     # short index for the frontend list view
│   ├── chunks.jsonl             # RAG-ready text chunks (~700 chars each, AR + EN)
│   ├── _embeddings.npy          # cached 384-dim E5 embeddings
│   ├── _faiss.index             # cached FAISS IndexFlatIP
│   ├── _museums.json            # museums + halls (location, summary, GPS)
│   ├── _halls.json              # flat halls index
│   ├── _qa_eval.jsonl           # Arabic Q&A evaluation pairs (1136 pairs)
│   ├── _relations.json          # artifact-to-artifact relations
│   ├── manifest.json            # counts, license breakdown, source mix
│   └── <ARTIFACT_ID>.json       # per-artifact full record (canonical)
├── images/
│   └── <ARTIFACT_ID>_NN.jpg     # 674 downloaded artifact images
├── scripts/                      # offline build pipeline
│   ├── seed_artifacts.py        # curated seed list
│   ├── wiki_client.py           # Wikipedia / Commons API client
│   ├── build_dataset.py         # main pipeline (Wikipedia → JSON + images)
│   ├── met_museum.py            # Met Open Access integration (200 objects)
│   ├── build_museums.py         # museum + hall master index
│   ├── build_qa.py              # Arabic Q&A generator
│   ├── package.py               # validate / dedupe / produce chunks
│   ├── enrich_timeline.py       # derive year_min / year_max + highlights
│   ├── retry_failed.py          # retry timed-out seeds
│   └── search.py                # CLI BM25 search (sanity check)
├── API.md                        # API document (the project deliverable)
├── HOW_TO_USE.md                # frontend-integration recipes
├── EXAMPLES.md                  # sample queries
└── raw/, logs/                  # build artefacts
```

## Schema (per artifact)

Each artifact JSON contains:

| Field | Notes |
|-------|-------|
| `id` | Stable string ID (e.g. `TUT_MASK`, `MET_547802`) |
| `names.ar` / `names.en` | Canonical Arabic + English names |
| `names.alt_ar` / `alt_en` | Alternative spellings |
| `category` | `Death mask`, `Statue`, `Stele`, … |
| `period.ar` / `period.en` / `year_min` | Historical period |
| `dynasty.ar` / `dynasty.en` | Dynasty (Arabic + English) |
| `material[]` | Materials, normalized |
| `dimensions{}` | Height/width/length/weight where available |
| `provenance.site_ar` / `site_en` | Where it was found |
| `discovery.year` / `by_ar` / `by_en` | Discovery details |
| `current_location.museum_id` | Cross-key into `_museums.json` |
| `current_location.museum_ar/en`, `city_ar/en` | Museum + city in both languages |
| `current_location.hall_ar/en` | Hall when known |
| `description.ar` / `en` | Full plain-text description (up to 8 000 chars) |
| `description.ar_intro` / `en_intro` | One-paragraph summary |
| `images[]` | Per-image metadata (filename on disk, license, credit, source URL, dims, primary flag, AR/EN caption) |
| `sources[]` | List of source URLs and licenses (Wikipedia AR/EN, Met OA, …) |
| `tags[]` | Free-form tags from Wikipedia categories |
| `qa_pairs_ar[]` | Auto-generated Arabic Q&A: `{q, a, evidence, type}` |

## Sources & licenses

| Source | License | What we take |
|--------|---------|--------------|
| **Wikipedia (AR + EN)** | CC-BY-SA 4.0 | Plain-text descriptions, infobox metadata, interlanguage links |
| **Wikimedia Commons** | mostly CC-BY-SA / Public Domain (per-file recorded in `images[].license`) | Images, captions, credit lines |
| **The Met Museum** | CC0 1.0 (Open Access) | Object metadata + photographs (public-domain only) |

Each image record carries its own license — never assume a single license for the corpus. The `manifest.json` provides a license-count summary.

## Pipeline

```bash
# 1) Build core dataset from Wikipedia (AR+EN) + Commons images
python3 scripts/build_dataset.py

# 2) Add Met Museum public-domain Egyptian objects
python3 scripts/met_museum.py 200

# 3) Build museum/hall index for the frontend
python3 scripts/build_museums.py

# 4) Retry any seeds that timed out
python3 scripts/retry_failed.py

# 5) Generate Arabic Q&A pairs
python3 scripts/build_qa.py

# 6) Validate, dedupe, produce artifacts.jsonl + chunks.jsonl + manifest.json
python3 scripts/package.py
```

## Designed for the frontend

The dataset is structured so a visual frontend can render the museum experience richly:

- **List/grid view** — use `artifacts_index.json` for fast loading (small payload with `primary_image`, `name_ar`, `museum_id`).
- **Detail view** — load `<ID>.json` for full metadata + image gallery (multiple licensed images per artifact).
- **Map / floor-plan** — `_museums.json` carries GPS coordinates and hall lists; each artifact's `current_location.hall_id` cross-references a hall.
- **Search** — `chunks.jsonl` is RAG-ready; one chunk per ~700 characters of description, in both languages, with `artifact_id` and `primary_image` so you can render search results visually.
- **Q&A demo** — `_qa_eval.jsonl` ships pre-baked Arabic queries you can use as ready-made example prompts.

## Reproducibility

- All scripts are idempotent — re-running skips already-built artifacts (delete + set `FORCE=1` to rebuild).
- Image downloads use the Commons `iiurlwidth=1600` thumbnail to cap size.
- Polite User-Agent + 0.4s delay between Wikipedia requests.

---

Built by hand-curating ~100 famous artifacts and ~200 Met OA objects, then enriching each with bilingual text and CC-licensed images. Hand-curated material maps cover the most common Egyptological vocabulary (dynasties, periods, materials, gods).
