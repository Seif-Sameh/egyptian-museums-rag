"""Compute artifact-to-artifact relations for the frontend "see also" feature.

Heuristics:
  1) Same museum + same dynasty → related
  2) Same person/keyword in name (Tutankhamun, Hatshepsut, …) → related
  3) Shared tags (≥ 2 in common) → related

Writes data/_relations.json: {artifact_id: [related_id, …]} (top 8 each).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

KEY_PEOPLE = [
    "tutankhamun", "tut", "akhenaten", "nefertiti", "hatshepsut", "ramesses",
    "ramses", "thutmose", "amenhotep", "khufu", "khafre", "menkaure",
    "djoser", "narmer", "merneptah", "psamtik", "yuya", "thuya", "tjuyu",
    "psusennes", "imhotep", "seti",
]


def name_keys(rec: dict) -> set[str]:
    blob = (rec["names"].get("en", "") + " " + rec["names"].get("ar", "")).lower()
    out = set()
    for k in KEY_PEOPLE:
        if k in blob:
            out.add(k)
    return out


def main() -> None:
    records = []
    for p in sorted(DATA_DIR.glob("*.json")):
        if p.name.startswith("_") or p.name in ("artifacts.jsonl", "manifest.json", "artifacts_index.json"):
            continue
        records.append(json.loads(p.read_text(encoding="utf-8")))

    by_id = {r["id"]: r for r in records}

    # Buckets
    by_person: dict[str, list[str]] = defaultdict(list)
    by_museum_dyn: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_tag: dict[str, list[str]] = defaultdict(list)
    for r in records:
        for k in name_keys(r):
            by_person[k].append(r["id"])
        m = r["current_location"].get("museum_id", "")
        d = (r["dynasty"].get("ar") or r["dynasty"].get("en") or "").strip()
        if m and d:
            by_museum_dyn[(m, d)].append(r["id"])
        for t in r.get("tags", [])[:10]:
            by_tag[t].append(r["id"])

    relations: dict[str, list[str]] = {}
    for r in records:
        rid = r["id"]
        scores: Counter[str] = Counter()
        for k in name_keys(r):
            for other in by_person[k]:
                if other != rid:
                    scores[other] += 5  # strong signal
        m = r["current_location"].get("museum_id", "")
        d = (r["dynasty"].get("ar") or r["dynasty"].get("en") or "").strip()
        if m and d:
            for other in by_museum_dyn[(m, d)]:
                if other != rid:
                    scores[other] += 2
        for t in r.get("tags", [])[:10]:
            for other in by_tag[t]:
                if other != rid:
                    scores[other] += 1
        relations[rid] = [oid for oid, _ in scores.most_common(8)]

    # Write output and update each record's related_ids
    (DATA_DIR / "_relations.json").write_text(
        json.dumps(relations, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    n_updated = 0
    for r in records:
        rels = relations.get(r["id"], [])
        if rels and rels != r.get("related_ids", []):
            r["related_ids"] = rels
            (DATA_DIR / f"{r['id']}.json").write_text(
                json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            n_updated += 1
    print(f"Computed relations for {len(records)} artifacts; wrote {n_updated} updates → _relations.json")


if __name__ == "__main__":
    main()
