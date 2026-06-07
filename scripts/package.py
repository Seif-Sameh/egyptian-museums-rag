"""Validate, dedupe, and produce final corpus files for the RAG frontend.

Outputs (in dataset/data/):
  artifacts.jsonl       — one artifact per line, full record
  artifacts_index.json  — small index: id, names, museum_id, primary_image, tags
  chunks.jsonl          — RAG-ready text chunks (each ~ 500-800 chars)
  manifest.json         — counts, license summary, source breakdown

Validation: schema fields present, image files exist on disk, descriptions non-empty.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMG_DIR = ROOT / "images"


def chunk_text(text: str, max_chars: int = 700) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[\.\!\؟])\s+", text.strip())
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for p in parts:
        if cur_len + len(p) + 1 > max_chars and cur:
            chunks.append(" ".join(cur).strip())
            cur, cur_len = [p], len(p)
        else:
            cur.append(p)
            cur_len += len(p) + 1
    if cur:
        chunks.append(" ".join(cur).strip())
    return [c for c in chunks if c]


def main() -> None:
    artifacts: list[dict] = []
    issues: list[str] = []
    SKIP = {"manifest.json", "artifacts_index.json", "dataset_card.json"}
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name in SKIP:
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict) or "names" not in rec:
            continue
        # validate
        for img in rec.get("images", []):
            disk = IMG_DIR / img["filename"]
            if not disk.exists():
                issues.append(f"{rec['id']}: missing image file {img['filename']}")
        if not (rec["description"].get("ar") or rec["description"].get("en")):
            issues.append(f"{rec['id']}: empty description")
        artifacts.append(rec)

    # Dedupe by names_en (keep first)
    seen_names: set[str] = set()
    deduped: list[dict] = []
    for r in artifacts:
        key = (r["names"].get("en") or "").strip().lower()
        if not key or key in seen_names:
            continue
        seen_names.add(key)
        deduped.append(r)

    # 1) artifacts.jsonl
    out1 = DATA_DIR / "artifacts.jsonl"
    out1.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in deduped) + "\n",
        encoding="utf-8",
    )

    # 2) artifacts_index.json (light, for frontend list view)
    index = []
    for r in deduped:
        prim = next((i for i in r.get("images", []) if i.get("is_primary")), None) or (
            r.get("images") or [None]
        )[0]
        index.append({
            "id": r["id"],
            "name_ar": r["names"].get("ar"),
            "name_en": r["names"].get("en"),
            "museum_id": r["current_location"].get("museum_id"),
            "museum_ar": r["current_location"].get("museum_ar"),
            "category": r.get("category"),
            "period_ar": r["period"].get("ar"),
            "period_en": r["period"].get("en"),
            "year_min": r["period"].get("year_min"),
            "year_max": r["period"].get("year_max"),
            "highlight": r.get("highlight", False),
            "primary_image": prim["filename"] if prim else None,
            "n_images": len(r.get("images", [])),
            "tags": r.get("tags", [])[:5],
        })
    (DATA_DIR / "artifacts_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3) chunks.jsonl — RAG-ready
    chunks_out = []
    for r in deduped:
        for lang in ("ar", "en"):
            txt = r["description"].get(lang, "")
            for ci, c in enumerate(chunk_text(txt, max_chars=800)):
                chunks_out.append({
                    "chunk_id": f"{r['id']}__{lang}__{ci}",
                    "artifact_id": r["id"],
                    "lang": lang,
                    "text": c,
                    "name_ar": r["names"].get("ar"),
                    "name_en": r["names"].get("en"),
                    "museum_id": r["current_location"].get("museum_id"),
                    "primary_image": (
                        next((i["filename"] for i in r.get("images", []) if i.get("is_primary")), None)
                        or (r.get("images") or [{}])[0].get("filename")
                    ),
                })
    (DATA_DIR / "chunks.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in chunks_out) + "\n",
        encoding="utf-8",
    )

    # 4) Manifest with counts and licenses
    license_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    museum_counts: Counter[str] = Counter()
    n_images = 0
    for r in deduped:
        for img in r.get("images", []):
            license_counts[img.get("license", "?")] += 1
            source_counts[img.get("source", "?")] += 1
            n_images += 1
        museum_counts[r["current_location"].get("museum_id", "?")] += 1

    manifest = {
        "n_artifacts": len(deduped),
        "n_artifacts_total_unfiltered": len(artifacts),
        "n_images": n_images,
        "n_chunks": len(chunks_out),
        "image_licenses": dict(license_counts),
        "image_sources": dict(source_counts),
        "by_museum": dict(museum_counts),
        "files": {
            "artifacts": "data/artifacts.jsonl",
            "index": "data/artifacts_index.json",
            "chunks": "data/chunks.jsonl",
            "qa_eval": "data/_qa_eval.jsonl",
            "museums": "data/_museums.json",
            "halls": "data/_halls.json",
            "images_dir": "images/",
        },
        "validation_issues": issues[:50],
    }
    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Artifacts: {len(deduped)} (raw {len(artifacts)})")
    print(f"Images: {n_images}")
    print(f"Chunks: {len(chunks_out)}")
    print(f"Issues: {len(issues)}")
    if issues[:5]:
        print("First issues:")
        for x in issues[:5]:
            print("  -", x)


if __name__ == "__main__":
    main()
