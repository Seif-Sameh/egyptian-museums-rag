# How to use this dataset for the RAG project

## 1. Browse the data visually

```bash
cd "Arabic RAG Project/dataset"
python3 -m http.server 8000
# Open http://localhost:8000/viewer.html
```

You'll see a card grid of every artifact with its primary image. Click a card to open a detail panel with all images, full Arabic + English descriptions, museum/hall info, and the auto-generated Q&A pairs.

## 2. Use it as a RAG corpus

The retrieval-ready format is `data/chunks.jsonl` — one JSON line per ~700-character chunk:

```json
{
  "chunk_id": "TUT_MASK__ar__0",
  "artifact_id": "TUT_MASK",
  "lang": "ar",
  "text": "قناع توت عنخ آمون هو قناع جنائزي ذهبي ...",
  "name_ar": "قناع توت عنخ آمون",
  "name_en": "Mask of Tutankhamun",
  "museum_id": "GEM",
  "primary_image": "TUT_MASK_01.jpg"
}
```

Plug into your retriever:

- **BM25 baseline** (no embeddings needed): `python3 scripts/search.py "ما هو قناع توت عنخ آمون"`
- **Dense retrieval**: feed `text` to AraDPR / Cohere multilingual / OpenAI `text-embedding-3-large`, store IDs alongside vectors. Use `chunk_id` to look up the source artifact.
- **Hybrid**: BM25 + dense, then rerank with a cross-encoder.

When generating an answer, hand the retrieved chunks (with `name_ar`, `museum_id`, `primary_image`) to your LLM. The frontend can use `primary_image` to render the answer with a thumbnail of the cited artifact.

## 3. Evaluate

`data/_qa_eval.jsonl` is your evaluation set:

```json
{"artifact_id": "TUT_MASK", "name_ar": "قناع توت عنخ آمون",
 "question": "أين توجد قناع توت عنخ آمون حاليًا؟",
 "answer": "تُحفظ قناع توت عنخ آمون في المتحف المصري الكبير في الجيزة.",
 "type": "location", "evidence_field": "current_location"}
```

Standard evaluation: for each question, retrieve top-5 chunks; the gold chunk is anything matching `artifact_id` and the matching `evidence_field`. Compute Recall@1, Recall@5, MRR, Answer-F1.

## 4. Frontend integration recipes

### Card grid (museum browser)

```javascript
const idx = await fetch('data/artifacts_index.json').then(r => r.json());
idx.forEach(a => render({
  thumbnail: `images/${a.primary_image}`,
  title: a.name_ar,
  subtitle: a.name_en,
  museum: a.museum_ar,
  onClick: () => openDetail(a.id),
}));
```

### Detail page

```javascript
const full = await fetch(`data/${id}.json`).then(r => r.json());
// full.images[]  — gallery
// full.description.ar  — full text
// full.qa_pairs_ar[]  — example questions
// full.related_ids[]  — "see also" panel
// full.current_location.museum_id  — link to museum view
```

### Museum / hall view

```javascript
const museums = await fetch('data/_museums.json').then(r => r.json());
const gem = museums.find(m => m.id === 'GEM');
// gem.halls[] — list with names.ar, summary.ar
// gem.coordinates — for the map pin
// then filter artifacts by current_location.hall_id === hall.id
```

### Search (server-side or in-browser BM25)

Use `data/chunks.jsonl` directly — it's already the right shape. The reference implementation is `scripts/search.py` (~120 LOC, no deps).

## 5. Add more artifacts later

The pipeline is incremental:

1. Add a new entry to `scripts/seed_artifacts.py`.
2. Run `python3 scripts/build_dataset.py NEW_ID`. The pipeline skips records that already exist.
3. Re-run `scripts/finalize.sh` to refresh derived files (chunks, Q&A, manifest).

To add a Met-side artifact, just bump the limit in `scripts/met_museum.py` and rerun.

## 6. Citation / acknowledgements

Built from three openly licensed sources. Each artifact's `sources[]` carries the URL + license; each image's `license` field carries its individual license. When publishing the demo, cite:

- Wikipedia (CC BY-SA 4.0) — text content
- Wikimedia Commons — image content (per-file license)
- The Metropolitan Museum of Art Open Access (CC0 1.0) — Met records and photos

The `manifest.json` summarizes the license breakdown for the whole corpus.
