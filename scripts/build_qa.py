"""Generate Arabic Q&A pairs from each artifact record.

Templates are deterministic — they read structured fields and create natural
Arabic questions with literal answers from the data. This produces a clean
evaluation set for the RAG pipeline (questions an end-user might really ask).

Output: writes `qa_pairs_ar` field into each per-artifact JSON, and produces
a flat `data/_qa_eval.jsonl` for retrieval evaluation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

# Inline copy of frequent-material translation (avoid cross-script import).
_MATERIAL_AR: dict[str, str] = {
    "Limestone": "حجر جيري", "Sandstone": "حجر رملي", "Granite": "جرانيت",
    "Granodiorite": "جرانوديوريت", "Basalt": "بازلت", "Diorite": "ديوريت",
    "Quartzite": "كوارتزيت", "Wood": "خشب", "Cedar": "خشب الأرز",
    "Ebony": "خشب الأبنوس", "Ivory": "عاج", "Bone": "عظم",
    "Bronze": "برونز", "Copper": "نحاس", "Gold": "ذهب",
    "Silver": "فضة", "Electrum": "إلكتروم", "Faience": "خزف فاينس",
    "Glass": "زجاج", "Linen": "كتان", "Papyrus": "ورق البردي",
    "Pottery": "فخار", "Lapis lazuli": "لازورد", "Carnelian": "عقيق أحمر",
    "Turquoise": "فيروز", "Obsidian": "سبج", "Steatite": "حجر صابوني",
    "Calcite": "كالسيت", "obsidian": "سبج", "carnelian": "عقيق أحمر",
    "lapis lazuli": "لازورد", "turquoise": "فيروز", "glass paste": "عجينة زجاجية",
}


def first_sentence(text: str) -> str:
    if not text:
        return ""
    # Arabic full-stop is "."; periods, !, ? all close
    m = re.search(r"^(.{30,400}?[\.\!\؟])\s", text)
    if m:
        return m.group(1).strip()
    return text.strip()[:300]


def gen_qa(rec: dict) -> list[dict]:
    """Return a list of Q&A pairs, each with q, a, evidence."""
    qa: list[dict] = []
    name_ar = rec["names"].get("ar") or rec["names"].get("en", "")
    name_en = rec["names"].get("en", "")
    desc_ar = rec["description"].get("ar", "") or rec["description"].get("ar_intro", "")
    desc_intro = first_sentence(desc_ar)

    if not name_ar:
        return qa

    # Q1: identity
    if desc_intro:
        qa.append({
            "q": f"ما هي {name_ar}؟",
            "a": desc_intro,
            "evidence": "description.ar_intro",
            "type": "identity",
        })

    # Q2: location
    loc = rec.get("current_location", {})
    museum_ar = loc.get("museum_ar")
    city_ar = loc.get("city_ar")
    if museum_ar:
        place = museum_ar + (f" في {city_ar}" if city_ar else "")
        qa.append({
            "q": f"أين توجد {name_ar} حاليًا؟",
            "a": f"تُحفظ {name_ar} في {place}.",
            "evidence": "current_location",
            "type": "location",
        })

    # Q3: dynasty / period
    dynasty = rec.get("dynasty", {}).get("ar") or rec.get("period", {}).get("ar")
    if dynasty:
        qa.append({
            "q": f"إلى أي عصر تعود {name_ar}؟",
            "a": f"تعود {name_ar} إلى {dynasty}.",
            "evidence": "dynasty/period",
            "type": "period",
        })

    # Q4: material
    materials = rec.get("material") or []
    if materials:
        ar_materials = [_MATERIAL_AR.get(m.strip(), m.strip()) for m in materials]
        ar_list = " و".join(ar_materials)
        qa.append({
            "q": f"من أي مادة صُنعت {name_ar}؟",
            "a": f"صُنعت {name_ar} من {ar_list}.",
            "evidence": "material",
            "type": "material",
        })

    # Q5: discovery year
    disc_year = rec.get("discovery", {}).get("year")
    if disc_year:
        qa.append({
            "q": f"متى اكتُشفت {name_ar}؟",
            "a": f"اكتُشفت {name_ar} عام {disc_year}.",
            "evidence": "discovery.year",
            "type": "discovery",
        })

    # Q6: provenance
    site = rec.get("provenance", {}).get("site_ar") or rec.get("provenance", {}).get("site_en")
    if site:
        qa.append({
            "q": f"من أين أُحضرت {name_ar}؟",
            "a": f"أُحضرت {name_ar} من {site}.",
            "evidence": "provenance",
            "type": "provenance",
        })

    # Q7: hall (if known)
    hall_ar = loc.get("hall_ar")
    if hall_ar:
        qa.append({
            "q": f"في أي قاعة من {museum_ar} يمكن مشاهدة {name_ar}؟",
            "a": f"يمكن مشاهدة {name_ar} في {hall_ar}.",
            "evidence": "current_location.hall",
            "type": "hall",
        })

    # Q8: free-form summary if we have rich Arabic description
    if len(desc_ar) > 400:
        qa.append({
            "q": f"اعطني نبذة عن {name_ar}.",
            "a": desc_ar[:600] + ("..." if len(desc_ar) > 600 else ""),
            "evidence": "description.ar",
            "type": "summary",
        })

    return qa


def main() -> None:
    eval_lines: list[str] = []
    n_records = 0
    n_qa = 0
    SKIP = {"manifest.json", "artifacts_index.json", "dataset_card.json"}
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name in SKIP:
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict) or "names" not in rec:
            continue
        qa = gen_qa(rec)
        rec["qa_pairs_ar"] = qa
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        n_records += 1
        n_qa += len(qa)
        for q in qa:
            eval_lines.append(json.dumps({
                "artifact_id": rec["id"],
                "name_ar": rec["names"].get("ar"),
                "name_en": rec["names"].get("en"),
                "question": q["q"],
                "answer": q["a"],
                "type": q["type"],
                "evidence_field": q["evidence"],
            }, ensure_ascii=False))
    out = DATA_DIR / "_qa_eval.jsonl"
    out.write_text("\n".join(eval_lines) + "\n", encoding="utf-8")
    print(f"Generated {n_qa} Q&A pairs across {n_records} records → {out}")


if __name__ == "__main__":
    main()
