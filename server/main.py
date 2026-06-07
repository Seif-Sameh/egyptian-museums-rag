"""FastAPI server: Arabic RAG over the Egyptian Museums dataset.

Endpoints
---------
GET   /api/health                        liveness check
POST  /api/query                         {q, k?, mode?, lang?} → answer + sources + primary artifact + related
GET   /api/search?q=...&k=5              same as /api/query but as GET
GET   /api/artifacts                     list of all artifacts (index entries)
GET   /api/artifacts/{id}                full record for one artifact
GET   /api/museums                       list of museums + halls
GET   /api/museums/{id}                  one museum + its artifacts
GET   /api/suggestions                   sample Arabic queries (for the UI)

Static
------
GET   /                                  index.html (RAG landing page)
GET   /browse                            browse.html (visual browser)
GET   /images/{file}                     downloaded artifact images
GET   /data/{file}                       raw dataset JSON (read-only)
GET   /api/docs                          interactive OpenAPI docs (Swagger UI)
GET   /api/redoc                         ReDoc-rendered docs
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag import RAGEngine

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMAGES_DIR = ROOT / "images"
STATIC_DIR = ROOT / "static"


app = FastAPI(
    title="Egyptian Museums RAG API",
    version="1.0.0",
    description=(
        "Bilingual (Arabic + English) Retrieval-Augmented Generation over the "
        "Grand Egyptian Museum, the Egyptian Museum at Tahrir, the National Museum "
        "of Egyptian Civilization, and Egyptian holdings in major world museums. "
        "Built for the Website QA NLP project."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ENGINE = RAGEngine()


# ─── Schemas ─────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    q: str = Field(..., description="Question, typically in Arabic", examples=["ما هو قناع توت عنخ آمون؟"])
    k: int = Field(5, ge=1, le=20, description="Number of source chunks to retrieve")
    mode: str = Field("extractive", description="`extractive` (default) or `generative`")
    lang: str = Field("ar", description="Preferred language for retrieval and answer (`ar` or `en`)")


class SourceCard(BaseModel):
    artifact_id: str
    chunk_id: str
    lang: str
    score: float
    text: str
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    primary_image: Optional[str] = None
    museum_id: Optional[str] = None
    museum_ar: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    mode: str
    sources: list[SourceCard]
    primary_artifact_id: Optional[str]
    primary_artifact: Optional[dict]
    related: list[dict]
    low_confidence: bool = False
    # Optional debug payload — top BM25/dense scores for the retrieved set.
    debug_scores: Optional[dict] = None

    class Config:
        # Accept and pass through the `_debug_scores` field name from the engine.
        populate_by_name = True
        extra = "allow"


# ─── API endpoints ──────────────────────────────────────────────────────
@app.get("/api/health", tags=["meta"], summary="Service health")
def health() -> dict:
    return {
        "status": "ok",
        "n_artifacts": len(ENGINE.artifacts_index),
        "n_chunks": len(ENGINE.chunks),
        "n_museums": len(ENGINE.museums),
    }


@app.post("/api/query", response_model=QueryResponse, tags=["rag"], summary="Ask a question")
def query(req: QueryRequest) -> QueryResponse:
    if not req.q.strip():
        raise HTTPException(400, "Query is empty")
    res = ENGINE.answer(req.q, k=req.k, mode=req.mode, lang=req.lang)
    return res


@app.get("/api/search", response_model=QueryResponse, tags=["rag"], summary="GET form of /query")
def search(
    q: str = Query(..., description="Question text"),
    k: int = Query(5, ge=1, le=20),
    mode: str = Query("extractive"),
    lang: str = Query("ar"),
) -> QueryResponse:
    res = ENGINE.answer(q, k=k, mode=mode, lang=lang)
    return res


@app.get("/api/artifacts", tags=["data"], summary="List all artifacts (lightweight index)")
def list_artifacts(museum_id: Optional[str] = None, highlight: Optional[bool] = None, limit: int = 1000) -> list[dict]:
    items = list(ENGINE.artifacts_index.values())
    if museum_id:
        items = [a for a in items if a.get("museum_id") == museum_id]
    if highlight is not None:
        items = [a for a in items if a.get("highlight") == highlight]
    return items[:limit]


@app.get("/api/artifacts/{artifact_id}", tags=["data"], summary="Full record for one artifact")
def get_artifact(artifact_id: str) -> dict:
    rec = ENGINE.get_full_record(artifact_id)
    if rec is None:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    return rec


@app.get("/api/museums", tags=["data"], summary="List museums + halls")
def list_museums() -> list[dict]:
    return ENGINE.museums


@app.get("/api/museums/{museum_id}", tags=["data"], summary="One museum + its artifacts grouped by hall")
def get_museum(museum_id: str) -> dict:
    m = next((m for m in ENGINE.museums if m["id"] == museum_id), None)
    if m is None:
        raise HTTPException(404, f"Museum {museum_id} not found")
    artifacts = [a for a in ENGINE.artifacts_index.values() if a.get("museum_id") == museum_id]
    return {**m, "artifacts": artifacts}


@app.get("/api/suggestions", tags=["meta"], summary="Suggested example queries for the UI")
def suggestions() -> list[dict]:
    return [
        {"q": "ما هو قناع توت عنخ آمون؟", "icon": "🪙"},
        {"q": "أين توجد صلاية نعرمر؟", "icon": "🗿"},
        {"q": "ما هو حجر رشيد ولماذا أهميته؟", "icon": "📜"},
        {"q": "ما القاعات الرئيسية في المتحف المصري الكبير؟", "icon": "🏛️"},
        {"q": "متى افتُتح المتحف المصري الكبير؟", "icon": "📅"},
        {"q": "من أي مادة صُنع تمثال خفرع؟", "icon": "🪨"},
        {"q": "ما هي مقتنيات يويا وتويا؟", "icon": "💎"},
        {"q": "ما تاريخ مومياء رمسيس الثاني؟", "icon": "👑"},
        {"q": "ما هو معبد دندور؟", "icon": "🏛️"},
        {"q": "احكِ لي عن الكاتب الجالس.", "icon": "✍️"},
    ]


# ─── Static frontend ────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/browse", response_class=HTMLResponse, include_in_schema=False)
def browse() -> FileResponse:
    return FileResponse(STATIC_DIR / "browse.html")


# Mount static asset directories last so they don't shadow API routes.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
