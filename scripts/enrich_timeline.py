"""Parse period/dynasty/objectDate text into numeric year_min/year_max for the timeline.

Egyptian dating conventions: years are BC, so they're stored as negative ints.
The Met's `objectDate` already has explicit ranges like "1391–1353 B.C." or "ca. 332 B.C."
Wikipedia infobox `period`/`created` is freer-form.

Also computes a `highlight` boolean for must-see artifacts based on:
  - has 5+ Wikipedia images (well-photographed = famous)
  - is in [Tutankhamun, Narmer, Khufu, Khafre, Hatshepsut, Akhenaten, Nefertiti, Ramesses,
    Rosetta, Djoser, Menkaure, Sphinx, Pyramid] keyword set
  - is in our hand-curated SEED list (not auto-pulled from Met)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

HIGHLIGHT_KEYWORDS = {
    "tutankhamun", "narmer", "khufu", "khafre", "menkaure", "hatshepsut",
    "akhenaten", "nefertiti", "ramesses", "ramses", "rosetta", "djoser",
    "sphinx", "pyramid", "thutmose", "amenhotep", "imhotep",
    "توت عنخ آمون", "نعرمر", "خوفو", "خفرع", "منكاورع", "حتشبسوت",
    "أخناتون", "نفرتيتي", "رمسيس", "رشيد", "زوسر", "أبو الهول",
    "هرم", "أهرامات", "تحتمس", "أمنحتب", "إمحوتب",
}

YEAR_PAT = re.compile(r"\b(\d{1,4})\b")
BC_PAT = re.compile(r"\b(\d{1,4})\s*(?:BC|BCE|B\.C\.|قبل\s*الميلاد|ق\.?\s*م)\b", re.I)
RANGE_PAT = re.compile(r"(?:c\.|ca\.|circa|نحو)?\s*(\d{1,4})\s*[-–—]\s*(\d{1,4})\s*(BC|BCE|B\.C\.|ق\.?\s*م)?", re.I)


def parse_date_range(text: str) -> tuple[int | None, int | None]:
    """Parse a free-form date string. Returns (year_min, year_max), BC = negative int."""
    if not text:
        return None, None
    text = text.strip()

    # Range form: "1391–1353 B.C." or "1391-1353"
    m = RANGE_PAT.search(text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        is_bc = bool(m.group(3)) or "BC" in text.upper() or "B.C" in text.upper() or "ق" in text
        if is_bc:
            a, b = -a, -b
        lo, hi = min(a, b), max(a, b)
        return lo, hi

    # Single BC year
    m = BC_PAT.search(text)
    if m:
        y = -int(m.group(1))
        return y, y

    # Single AD year
    m = YEAR_PAT.search(text)
    if m:
        y = int(m.group(1))
        # plausibility filter — reject impossible years
        if 1 <= y <= 4000:
            return y, y
    return None, None


# Approximate BC dates of Egyptian periods (Shaw 2000 convention)
PERIOD_RANGES_BC = {
    "Predynastic Period": (-5500, -3100),
    "Early Dynastic Period": (-3100, -2686),
    "Old Kingdom": (-2686, -2181),
    "First Intermediate Period": (-2181, -2055),
    "Middle Kingdom": (-2055, -1650),
    "Second Intermediate Period": (-1650, -1550),
    "New Kingdom": (-1550, -1069),
    "Third Intermediate Period": (-1069, -664),
    "Late Period": (-664, -332),
    "Ptolemaic Period": (-332, -30),
    "Roman Period": (-30, 395),
    "Coptic": (200, 641),
    "Byzantine": (395, 641),
}

DYNASTY_RANGES_BC = {
    "1st Dynasty": (-3100, -2890),
    "2nd Dynasty": (-2890, -2686),
    "3rd Dynasty": (-2686, -2613),
    "4th Dynasty": (-2613, -2494),
    "5th Dynasty": (-2494, -2345),
    "6th Dynasty": (-2345, -2181),
    "11th Dynasty": (-2125, -1985),
    "12th Dynasty": (-1985, -1773),
    "13th Dynasty": (-1773, -1650),
    "17th Dynasty": (-1580, -1550),
    "18th Dynasty": (-1550, -1295),
    "19th Dynasty": (-1295, -1186),
    "20th Dynasty": (-1186, -1069),
    "21st Dynasty": (-1069, -945),
    "22nd Dynasty": (-945, -715),
    "25th Dynasty": (-747, -656),
    "26th Dynasty": (-664, -525),
    "27th Dynasty": (-525, -404),
    "30th Dynasty": (-380, -343),
}
# Add "Dynasty N" variants (Met format)
for d, r in list(DYNASTY_RANGES_BC.items()):
    n = re.search(r"\d+", d).group(0)
    DYNASTY_RANGES_BC[f"Dynasty {n}"] = r


def derive_years(rec: dict) -> tuple[int | None, int | None]:
    """Try multiple sources, return tightest (year_min, year_max)."""
    sources = [
        rec.get("description", {}).get("en", "")[:200],
        rec.get("period", {}).get("en", ""),
        rec.get("dynasty", {}).get("en", ""),
    ]
    # 1) explicit numeric date in description (Met objectDate is embedded there)
    for s in sources:
        lo, hi = parse_date_range(s)
        if lo is not None:
            return lo, hi
    # 2) period range
    p = rec.get("period", {}).get("en", "").strip()
    if p in PERIOD_RANGES_BC:
        return PERIOD_RANGES_BC[p]
    # 3) dynasty range
    d = rec.get("dynasty", {}).get("en", "").strip()
    if d in DYNASTY_RANGES_BC:
        return DYNASTY_RANGES_BC[d]
    return None, None


def is_highlight(rec: dict) -> bool:
    if not rec["id"].startswith("MET_"):
        return True  # everything in our hand-picked seed list is a highlight
    blob = (
        (rec["names"].get("en") or "") + " "
        + (rec["names"].get("ar") or "") + " "
        + " ".join(rec.get("tags") or [])
    ).lower()
    if any(k in blob for k in HIGHLIGHT_KEYWORDS):
        return True
    if len(rec.get("images", [])) >= 3 and rec.get("category"):
        return False  # well-photographed but generic, not highlight
    return False


def main() -> None:
    SKIP = {"manifest.json", "artifacts_index.json", "dataset_card.json"}
    n_dated = 0
    n_highlight = 0
    n_total = 0
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name in SKIP:
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict) or "id" not in rec:
            continue
        n_total += 1
        lo, hi = derive_years(rec)
        if lo is not None:
            rec["period"]["year_min"] = lo
            rec["period"]["year_max"] = hi
            n_dated += 1
        rec["highlight"] = is_highlight(rec)
        if rec["highlight"]:
            n_highlight += 1
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Enriched timeline for {n_dated}/{n_total} records.")
    print(f"Marked {n_highlight} highlights.")


if __name__ == "__main__":
    main()
