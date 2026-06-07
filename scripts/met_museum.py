"""Met Museum Open Access — fetch Egyptian Department (departmentId=10) objects.

We pull a curated set of HIGHLIGHT public-domain on-view Egyptian objects.
The Met has a clean public API; we save artifact records in the same schema as
the Wikipedia-sourced ones, so the final corpus is unified.

This is a SECONDARY source: it adds breadth (objects in NY, not Cairo) and provides
high-quality public-domain photos and good English provenance text. We do NOT have
Arabic text from the Met — for that we synthesize a brief Arabic summary from the
English fields using a deterministic glossary.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import wiki_client as wc  # for download helper
from schema import empty_record

DATA_DIR = ROOT / "data"
IMG_DIR = ROOT / "images"
LOG_DIR = ROOT / "logs"
DATA_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

LOG_PATH = LOG_DIR / "met.log"
MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
DEPT_EGYPT = 10
MAX_OBJECTS = 250  # cap to keep dataset focused
REQUEST_DELAY = 0.3


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": wc.UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def list_egyptian_object_ids() -> list[int]:
    """List object IDs from the Egyptian dept that are highlights / on view with images."""
    queries = [
        # Highlight objects (curator-picked)
        f"{MET_BASE}/search?departmentId={DEPT_EGYPT}&isHighlight=true&hasImages=true&q=*",
        # On-view objects with images (broader)
        f"{MET_BASE}/search?departmentId={DEPT_EGYPT}&isOnView=true&hasImages=true&q=*",
    ]
    seen: list[int] = []
    seen_set: set[int] = set()
    for q in queries:
        try:
            d = get_json(q)
        except Exception as e:
            log(f"search err {q}: {e}")
            continue
        ids = d.get("objectIDs") or []
        for oid in ids:
            if oid not in seen_set:
                seen.add(oid) if False else None  # keep linter happy
                seen_set.add(oid)
                seen.append(oid)
        time.sleep(REQUEST_DELAY)
    return seen


# ─── Glossary for deterministic AR summaries ─────────────────────────────
DYNASTY_AR_BASE = {
    1: "الأسرة الأولى", 2: "الأسرة الثانية", 3: "الأسرة الثالثة",
    4: "الأسرة الرابعة", 5: "الأسرة الخامسة", 6: "الأسرة السادسة",
    7: "الأسرة السابعة", 8: "الأسرة الثامنة", 9: "الأسرة التاسعة",
    10: "الأسرة العاشرة", 11: "الأسرة الحادية عشرة", 12: "الأسرة الثانية عشرة",
    13: "الأسرة الثالثة عشرة", 14: "الأسرة الرابعة عشرة", 15: "الأسرة الخامسة عشرة",
    16: "الأسرة السادسة عشرة", 17: "الأسرة السابعة عشرة", 18: "الأسرة الثامنة عشرة",
    19: "الأسرة التاسعة عشرة", 20: "الأسرة العشرون", 21: "الأسرة الحادية والعشرون",
    22: "الأسرة الثانية والعشرون", 23: "الأسرة الثالثة والعشرون", 24: "الأسرة الرابعة والعشرون",
    25: "الأسرة الخامسة والعشرون", 26: "الأسرة السادسة والعشرون", 27: "الأسرة السابعة والعشرون",
    28: "الأسرة الثامنة والعشرون", 29: "الأسرة التاسعة والعشرون", 30: "الأسرة الثلاثون",
    31: "الأسرة الحادية والثلاثون",
}
ORD_SUFFIXES = ["", "st", "nd", "rd"] + ["th"] * 8 + ["th"] * 20  # 1..31

DYNASTY_AR = {}
for n, ar in DYNASTY_AR_BASE.items():
    s = ORD_SUFFIXES[n] if n < len(ORD_SUFFIXES) else "th"
    DYNASTY_AR[f"{n}{s} Dynasty"] = ar
    DYNASTY_AR[f"Dynasty {n}"] = ar
    DYNASTY_AR[f"dynasty {n}"] = ar

PERIOD_AR = {
    "Predynastic Period": "عصر ما قبل الأسرات",
    "Early Dynastic Period": "العصر العتيق",
    "Old Kingdom": "الدولة القديمة",
    "First Intermediate Period": "عصر الانتقال الأول",
    "Middle Kingdom": "الدولة الوسطى",
    "Second Intermediate Period": "عصر الانتقال الثاني",
    "New Kingdom": "الدولة الحديثة",
    "Third Intermediate Period": "عصر الانتقال الثالث",
    "Late Period": "العصر المتأخر",
    "Ptolemaic Period": "العصر البطلمي",
    "Roman Period": "العصر الروماني",
    "Coptic": "العصر القبطي",
    "Byzantine": "العصر البيزنطي",
}

MATERIAL_AR = {
    "Limestone": "حجر جيري", "Sandstone": "حجر رملي", "Granite": "جرانيت",
    "Granodiorite": "جرانوديوريت", "Basalt": "بازلت", "Diorite": "ديوريت",
    "Quartzite": "كوارتزيت", "Schist": "شيست", "Travertine": "ترافرتين",
    "Calcite": "كالسيت", "Greywacke": "غريواكي", "Anorthosite": "أنورثوزيت",
    "Serpentine": "سربنتين", "Alabaster": "مرمر", "Marble": "رخام",
    "Wood": "خشب", "Cedar": "خشب الأرز", "Ebony": "خشب الأبنوس",
    "Sycamore": "خشب الجميز", "Ivory": "عاج", "Bone": "عظم",
    "Bronze": "برونز", "Copper": "نحاس", "Gold": "ذهب", "Silver": "فضة",
    "Electrum": "إلكتروم", "Iron": "حديد", "Lead": "رصاص",
    "Faience": "خزف فاينس", "Glass": "زجاج", "Linen": "كتان",
    "Papyrus": "ورق البردي", "Pottery": "فخار", "Ceramic": "سيراميك",
    "Earthenware": "فخار", "Terracotta": "تيراكوتا",
    "Lapis lazuli": "حجر اللازورد", "Carnelian": "عقيق أحمر", "Turquoise": "فيروز",
    "Obsidian": "سبج", "Amethyst": "جمشت", "Jasper": "يشب", "Quartz": "كوارتز",
    "Steatite": "حجر صابوني", "Soapstone": "حجر صابوني",
    "Plaster": "جص", "Stucco": "ستوكو", "Pigment": "صبغة",
    "Reed": "بوص", "Leather": "جلد", "Gilded": "مذهَّب",
}

CITY_AR = {"New York": "نيويورك", "Cairo": "القاهرة", "London": "لندن"}

# Common object classifications → Arabic
CLASS_AR = {
    "Statue": "تمثال", "Statuette": "تمثال صغير", "Figurine": "تمثال صغير",
    "Bust": "تمثال نصفي", "Stele": "لوحة", "Stela": "لوحة",
    "Relief": "نقش بارز", "Plaque": "لوحة منقوشة",
    "Sarcophagus": "تابوت حجري", "Coffin": "تابوت",
    "Mummy": "مومياء", "Cartonnage": "كرتوناج",
    "Mask": "قناع", "Funerary mask": "قناع جنائزي",
    "Amulet": "تميمة", "Scarab": "جعران", "Ring": "خاتم",
    "Necklace": "قلادة", "Pendant": "تعليقة", "Bracelet": "سوار",
    "Earring": "قرط", "Ushabti": "تمثال أوشابتي", "Shabti": "تمثال أوشابتي",
    "Canopic jar": "إناء كانوبي", "Canopic": "إناء كانوبي",
    "Vessel": "إناء", "Jar": "إناء", "Dish": "طبق",
    "Bowl": "وعاء", "Cup": "كأس", "Pot": "إناء فخاري",
    "Papyrus": "بردية", "Scroll": "لفافة",
    "Ostracon": "كسرة فخارية", "Tablet": "لوح",
    "Knife": "سكين", "Dagger": "خنجر", "Axe": "فأس",
    "Mace": "صولجان", "Macehead": "رأس صولجان",
    "Mirror": "مرآة", "Comb": "مشط",
    "Wig": "شعر مستعار", "Sandals": "صندل",
    "Headrest": "مسند رأس",
    "Cosmetic": "أدوات تجميل",
    "Inlay": "ترصيع", "Bead": "خرزة",
    "Chair": "كرسي", "Stool": "مقعد",
    "Boat model": "نموذج مركب", "Tomb model": "نموذج مقبرة",
    "Architectural element": "عنصر معماري",
    "Pyramidion": "هرم رأسي", "Obelisk": "مسلة",
    "Sphinx": "تمثال أبو الهول",
    "Door": "باب", "Stelophorous": "حامل لوحة",
}


def ar_classify(class_en: str, name_en: str) -> str:
    """Heuristic Arabic name based on EN classification + EN title."""
    if not class_en and not name_en:
        return ""
    text = f"{class_en} {name_en}".lower()
    for k in sorted(CLASS_AR.keys(), key=len, reverse=True):
        if k.lower() in text:
            return CLASS_AR[k]
    return class_en or ""


def ar_translate_dict(text: str, mapping: dict[str, str]) -> str:
    """Translate string with longest-key-first replacement."""
    if not text:
        return ""
    keys = sorted(mapping.keys(), key=len, reverse=True)
    out = text
    for k in keys:
        out = re.sub(re.escape(k), mapping[k], out, flags=re.I)
    return out


def ar_summary(obj: dict) -> tuple[str, str]:
    """Return (ar_name, ar_description). The ar_name is a heuristic Arabic title."""
    title_en = obj.get("title", "").strip()
    classification = obj.get("classification", "") or obj.get("objectName", "")
    period = obj.get("period", "")
    dynasty = obj.get("dynasty", "")
    date = obj.get("objectDate", "")
    medium = obj.get("medium", "") or ""
    geog = obj.get("country") or obj.get("city") or ""
    location = "متحف المتروبوليتان للفنون، نيويورك"
    period_ar = ar_translate_dict(period, PERIOD_AR) or period
    dyn_ar = ar_translate_dict(dynasty, DYNASTY_AR) or dynasty
    medium_ar = ar_translate_dict(medium, MATERIAL_AR) or medium
    geog_ar = "مصر القديمة" if (geog and "egypt" in geog.lower()) else (geog or "")

    cls_ar = ar_classify(classification, title_en) or "قطعة أثرية"
    ar_name = f"{cls_ar} ({title_en})" if title_en else cls_ar

    parts = [f"{cls_ar} مصرية قديمة"]
    if title_en:
        parts.append(f"معروفة بـ«{title_en}»")
    if period_ar:
        parts.append(f"تعود إلى {period_ar}")
    if dyn_ar:
        parts.append(f"({dyn_ar})")
    if date:
        # Translate "B.C." → "ق.م"; "ca." → "نحو"
        date_ar = date.replace("B.C.", "ق.م").replace("BC", "ق.م").replace("ca.", "نحو").replace("ca ", "نحو ")
        parts.append(f"وتؤرخ {date_ar}")
    if medium_ar:
        parts.append(f"مصنوعة من {medium_ar}")
    if geog_ar:
        parts.append(f"عُثر عليها في {geog_ar}")
    parts.append(f"محفوظة حاليًا في {location}")
    desc = "، ".join(parts) + "."
    return ar_name, desc


def safe_filename(artifact_id: str, idx: int, url: str) -> str:
    ext = ".jpg"
    m = re.search(r"\.([A-Za-z0-9]+)(?:\?|$)", url)
    if m and m.group(1).lower() in ("jpg", "jpeg", "png", "gif"):
        ext = "." + m.group(1).lower()
        if ext == ".jpeg":
            ext = ".jpg"
    return f"{artifact_id}_{idx:02d}{ext}"


def build_record_from_met(obj: dict) -> Optional[dict]:
    if not obj.get("isPublicDomain"):
        return None
    if not obj.get("primaryImage"):
        return None
    aid = f"MET_{obj['objectID']}"
    rec = empty_record(aid)
    rec["names"]["en"] = obj.get("title", "")
    rec["names"]["alt_en"] = [t for t in (obj.get("titleSecondary"),) if t]
    rec["category"] = obj.get("classification", "") or obj.get("objectName", "")
    rec["period"]["en"] = obj.get("period", "")
    rec["period"]["ar"] = ar_translate_dict(obj.get("period", ""), PERIOD_AR)
    rec["dynasty"]["en"] = obj.get("dynasty", "")
    rec["dynasty"]["ar"] = ar_translate_dict(obj.get("dynasty", ""), DYNASTY_AR)
    rec["material"] = [m.strip() for m in re.split(r",|;", obj.get("medium", "") or "") if m.strip()]
    if obj.get("dimensions"):
        rec["dimensions"]["text"] = obj["dimensions"]
    rec["provenance"]["site_en"] = obj.get("excavation", "") or obj.get("country", "") or obj.get("city", "")
    rec["discovery"]["year"] = None
    rec["current_location"]["museum_id"] = "MET"
    rec["current_location"]["museum_en"] = "The Metropolitan Museum of Art"
    rec["current_location"]["museum_ar"] = "متحف المتروبوليتان للفنون"
    rec["current_location"]["city_en"] = "New York"
    rec["current_location"]["city_ar"] = "نيويورك"
    rec["current_location"]["country"] = "USA"
    rec["current_location"]["hall_en"] = obj.get("GalleryNumber", "") and f"Gallery {obj['GalleryNumber']}"

    title = obj.get("title", "")
    desc_en = title
    if obj.get("objectName") and obj["objectName"].lower() != title.lower():
        desc_en += f" — {obj['objectName']}"
    if obj.get("period"):
        desc_en += f". Period: {obj['period']}"
    if obj.get("dynasty"):
        desc_en += f", {obj['dynasty']}"
    if obj.get("objectDate"):
        desc_en += f", dated to {obj['objectDate']}"
    if obj.get("medium"):
        desc_en += f". Medium: {obj['medium']}"
    if obj.get("dimensions"):
        desc_en += f". Dimensions: {obj['dimensions']}"
    if obj.get("excavation"):
        desc_en += f". Excavation: {obj['excavation']}"
    if obj.get("country"):
        desc_en += f". Country of origin: {obj['country']}"
    if obj.get("creditLine"):
        desc_en += f". Credit: {obj['creditLine']}"
    desc_en += "."
    rec["description"]["en"] = desc_en
    rec["description"]["en_intro"] = title
    ar_name, ar_desc = ar_summary(obj)
    rec["names"]["ar"] = ar_name
    rec["description"]["ar"] = ar_desc
    rec["description"]["ar_intro"] = ar_desc

    # Images: primary + 1 additional view to keep download volume sane.
    img_urls: list[str] = []
    if obj.get("primaryImageSmall"):
        img_urls.append(obj["primaryImageSmall"])
    elif obj.get("primaryImage"):
        img_urls.append(obj["primaryImage"])
    for u in (obj.get("additionalImages") or [])[:1]:
        img_urls.append(u)

    chosen: list[dict] = []
    for i, url in enumerate(img_urls, start=1):
        out_name = safe_filename(aid, i, url)
        dest = IMG_DIR / out_name
        try:
            raw = wc._request(url, timeout=40)
            dest.write_bytes(raw)
        except Exception as e:
            log(f"  ! image dl failed {url}: {e}")
            continue
        chosen.append({
            "filename": out_name,
            "source": "met_museum_oa",
            "source_url": url,
            "credit": "The Metropolitan Museum of Art, Open Access",
            "license": "CC0 1.0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "is_primary": (i == 1),
            "caption_en": title,
            "object_name": obj.get("objectName", ""),
        })
        time.sleep(0.15)
    rec["images"] = chosen

    rec["sources"] = [{
        "type": "met_museum_oa",
        "url": obj.get("objectURL", ""),
        "title": title,
        "license": "CC0 1.0",
    }]

    rec["tags"] = []
    for t in (obj.get("tags") or [])[:8]:
        if t.get("term"):
            rec["tags"].append(t["term"].lower())

    return rec


def main(limit: int = MAX_OBJECTS) -> None:
    ids = list_egyptian_object_ids()
    log(f"Egyptian object candidates: {len(ids)}")
    built = 0
    skipped = 0
    for oid in ids:
        if built >= limit:
            break
        out_path = DATA_DIR / f"MET_{oid}.json"
        if out_path.exists():
            built += 1
            continue
        try:
            obj = get_json(f"{MET_BASE}/objects/{oid}")
        except Exception as e:
            log(f"  ! object fetch failed {oid}: {e}")
            skipped += 1
            continue
        if obj.get("message"):
            skipped += 1
            continue
        rec = build_record_from_met(obj)
        if rec is None:
            skipped += 1
            time.sleep(REQUEST_DELAY)
            continue
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        built += 1
        if built % 10 == 0:
            log(f"  progress: built={built} skipped={skipped} (last: {rec['names']['en'][:50]})")
        time.sleep(REQUEST_DELAY)
    log(f"DONE. built={built} skipped={skipped}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else MAX_OBJECTS
    main(limit=n)
