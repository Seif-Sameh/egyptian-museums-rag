"""Enrichment pass: synthesize Arabic content where Arabic Wikipedia is missing.

Strategy:
  - If `description.ar` is empty but `description.en` exists, build a deterministic
    Arabic mini-description from the seed name + structured fields, and translate
    period/dynasty/material with the same glossary as met_museum.

  - If `current_location.museum_ar` is empty but museum_id matches our master, fill it.

  - If `period.ar` is empty but `period.en` is set, translate via glossary.

Operates in-place across data/<id>.json files (skips _museums.json / _halls.json).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from met_museum import PERIOD_AR, DYNASTY_AR, MATERIAL_AR, ar_translate_dict

DATA_DIR = ROOT / "data"


def load_museums() -> dict[str, dict]:
    p = DATA_DIR / "_museums.json"
    if not p.exists():
        return {}
    items = json.loads(p.read_text(encoding="utf-8"))
    return {m["id"]: m for m in items}


MUSEUMS = load_museums()


def synthesize_ar(rec: dict) -> str:
    name_ar = rec["names"].get("ar") or rec["names"].get("en", "")
    name_en = rec["names"].get("en", "")
    period_ar = rec["period"].get("ar") or ar_translate_dict(rec["period"].get("en", ""), PERIOD_AR)
    dyn_ar = rec["dynasty"].get("ar") or ar_translate_dict(rec["dynasty"].get("en", ""), DYNASTY_AR)
    materials_ar = [MATERIAL_AR.get(m.strip(), m.strip()) for m in (rec.get("material") or [])]
    site = rec["provenance"].get("site_ar") or rec["provenance"].get("site_en")
    museum_ar = rec["current_location"].get("museum_ar")
    city_ar = rec["current_location"].get("city_ar")

    parts = []
    if name_ar:
        parts.append(f"تُعد {name_ar} (بالإنجليزية: {name_en}) من القطع الأثرية المصرية القديمة المعروفة")
    if period_ar:
        parts.append(f"وتعود إلى {period_ar}")
    if dyn_ar:
        parts.append(f"خلال {dyn_ar}")
    if materials_ar:
        parts.append(f"وقد صُنعت من {' و'.join(materials_ar)}")
    if site:
        parts.append(f"عُثر عليها في {site}")
    if museum_ar:
        place = museum_ar + (f" بمدينة {city_ar}" if city_ar else "")
        parts.append(f"وتُعرض حاليًا في {place}")
    return "، ".join(parts) + "."


def main() -> None:
    n_synth = 0
    n_loc = 0
    n_period = 0
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name in ("artifacts.jsonl", "manifest.json", "artifacts_index.json"):
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        changed = False

        # Fill museum_ar from master
        loc = rec["current_location"]
        if loc.get("museum_id") in MUSEUMS:
            m = MUSEUMS[loc["museum_id"]]
            if not loc.get("museum_ar"):
                loc["museum_ar"] = m["names"]["ar"]
                changed = True
                n_loc += 1
            if not loc.get("museum_en"):
                loc["museum_en"] = m["names"]["en"]
                changed = True
            if not loc.get("city_ar"):
                loc["city_ar"] = m["city"]["ar"]
                changed = True
            if not loc.get("city_en"):
                loc["city_en"] = m["city"]["en"]
                changed = True
            if not loc.get("country"):
                loc["country"] = m["country"]
                changed = True

        # Fill period.ar from EN
        if not rec["period"].get("ar") and rec["period"].get("en"):
            tr = ar_translate_dict(rec["period"]["en"], PERIOD_AR)
            if tr and tr != rec["period"]["en"]:
                rec["period"]["ar"] = tr
                changed = True
                n_period += 1
        # Dynasty
        if not rec["dynasty"].get("ar") and rec["dynasty"].get("en"):
            tr = ar_translate_dict(rec["dynasty"]["en"], DYNASTY_AR)
            if tr and tr != rec["dynasty"]["en"]:
                rec["dynasty"]["ar"] = tr
                changed = True

        # Synthesize description.ar if empty
        if not rec["description"].get("ar"):
            rec["description"]["ar"] = synthesize_ar(rec)
            rec["description"]["ar_intro"] = rec["description"]["ar"]
            n_synth += 1
            changed = True

        if changed:
            path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Filled museum metadata: {n_loc} | period AR: {n_period} | synthesized AR descriptions: {n_synth}")


if __name__ == "__main__":
    main()
