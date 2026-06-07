"""Re-apply the latest Arabic translations to existing MET_*.json records.

The running scraper produced records with an older translation map. This pass
rewrites their `names.ar`, `dynasty.ar`, `period.ar`, and `description.ar`
without re-downloading images or hitting the network.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from met_museum import PERIOD_AR, DYNASTY_AR, MATERIAL_AR, ar_translate_dict, ar_classify

DATA_DIR = ROOT / "data"


def refresh(rec: dict) -> bool:
    if not rec["id"].startswith("MET_"):
        return False
    changed = False

    src = next((s for s in rec.get("sources", []) if s.get("type") == "met_museum_oa"), None)
    title_en = rec["names"].get("en", "")

    # Rebuild dynasty AR from EN
    dyn_en = rec["dynasty"].get("en", "")
    new_dyn_ar = ar_translate_dict(dyn_en, DYNASTY_AR)
    if new_dyn_ar and new_dyn_ar != rec["dynasty"].get("ar"):
        rec["dynasty"]["ar"] = new_dyn_ar
        changed = True

    # Period AR
    per_en = rec["period"].get("en", "")
    new_per_ar = ar_translate_dict(per_en, PERIOD_AR)
    if new_per_ar and new_per_ar != rec["period"].get("ar"):
        rec["period"]["ar"] = new_per_ar
        changed = True

    # Materials → AR list (stored alongside; we keep the EN list authoritative)
    materials_en = rec.get("material") or []
    materials_ar = [MATERIAL_AR.get(m.strip(), m.strip()) for m in materials_en]

    # Heuristic AR title
    cls_en = rec.get("category", "") or ""
    ar_cls = ar_classify(cls_en, title_en) or "قطعة أثرية"
    new_ar_name = f"{ar_cls} ({title_en})" if title_en else ar_cls
    if new_ar_name != rec["names"].get("ar"):
        rec["names"]["ar"] = new_ar_name
        changed = True

    # Rebuild AR description
    parts = [f"{ar_cls} مصرية قديمة"]
    if title_en:
        parts.append(f"معروفة بـ«{title_en}»")
    if rec["period"].get("ar"):
        parts.append(f"تعود إلى {rec['period']['ar']}")
    if rec["dynasty"].get("ar"):
        parts.append(f"({rec['dynasty']['ar']})")
    # Date was not stored separately; we left it embedded in description.en. Skip.
    if materials_ar:
        parts.append(f"مصنوعة من {' و'.join(materials_ar)}")
    parts.append("محفوظة حاليًا في متحف المتروبوليتان للفنون، نيويورك")
    new_desc_ar = "، ".join(parts) + "."
    if new_desc_ar != rec["description"].get("ar"):
        rec["description"]["ar"] = new_desc_ar
        rec["description"]["ar_intro"] = new_desc_ar
        changed = True

    return changed


def main() -> None:
    n = 0
    n_changed = 0
    for path in sorted(DATA_DIR.glob("MET_*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if refresh(rec):
            path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            n_changed += 1
        n += 1
    print(f"Refreshed {n_changed} of {n} MET records.")


if __name__ == "__main__":
    main()
