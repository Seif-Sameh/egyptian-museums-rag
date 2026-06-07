"""Main pipeline: build per-artifact JSON records with text+images.

For each seed entry:
  1) Resolve EN Wikipedia title (redirects).
  2) Get AR title via interlanguage links (fallback to seed hint).
  3) Fetch full plain-text extracts in both languages.
  4) Parse infobox from wikitext for structured fields.
  5) List images on each page; filter to relevant artifact images.
  6) Get Commons license/credit for each image; download top-N to disk.
  7) Write per-artifact JSON to dataset/data/<id>.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import wiki_client as wc
from schema import empty_record
from seed_artifacts import SEED, MUSEUMS

DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"
IMG_DIR = ROOT / "images"
LOG_DIR = ROOT / "logs"
for d in (DATA_DIR, RAW_DIR, IMG_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

LOG_PATH = LOG_DIR / "build.log"

MAX_IMAGES_PER_ARTIFACT = 5
MAX_IMAGE_BYTES = 6 * 1024 * 1024  # cap each image at ~6MB


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─── Infobox key mapping (artifact / monument / temple) ───────────────────
EN_KEY_MAP = {
    "material": ["material", "medium"],
    "size_height": ["height_metric", "height", "height_imperial"],
    "size_width": ["width_metric", "width"],
    "size_weight": ["weight"],
    "size_length": ["length_metric", "length"],
    "discovered_year": ["discovered", "discovered_date", "year_made"],
    "discovered_by": ["discovered_by"],
    "discovered_place": ["discovered_place", "place"],
    "current_location": ["location", "current_location"],
    "created_period": ["created", "period"],
    "dynasty": ["dynasty"],
    "culture": ["culture"],
    "type": ["type"],
    "writing": ["writing", "script"],
    "category": ["category"],
}


def pick(infobox: dict, keys: list[str]) -> str:
    for k in keys:
        v = infobox.get(k)
        if v:
            return v
    return ""


def parse_year(s: str) -> Optional[int]:
    """Parse '1922' or 'c. 1325 BC' into a signed int."""
    if not s:
        return None
    m = re.search(r"\b(\d{3,4})\s*(BC|BCE|قبل\s*الميلاد|ق\.?\s*م)?\b", s, re.I)
    if not m:
        return None
    y = int(m.group(1))
    if m.group(2):
        return -y
    return y


# ─── Image picking & download ────────────────────────────────────────────
def pick_images(pages_seen: list[Any], primary_image: Optional[str]) -> list[str]:
    """Return ordered list of File:names from the parsed pages.
    `pages_seen` is a list of parse() results; the first page's first images rank highest.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    if primary_image:
        # primary_image already has File: stripped from REST
        if wc.is_relevant_image(primary_image) and primary_image not in seen:
            seen.add(primary_image)
            ordered.append(primary_image)
    for page in pages_seen:
        if not page:
            continue
        imgs = page.get("images", [])
        for f in imgs:
            if not wc.is_relevant_image(f):
                continue
            if f in seen:
                continue
            seen.add(f)
            ordered.append(f)
    return ordered


def safe_filename(artifact_id: str, idx: int, original: str) -> str:
    ext = ""
    m = re.search(r"\.([A-Za-z0-9]+)$", original)
    if m:
        ext = "." + m.group(1).lower()
        if ext == ".jpeg":
            ext = ".jpg"
    return f"{artifact_id}_{idx:02d}{ext}"


def download_image(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 1024:
        return True
    try:
        raw = wc._request(url, timeout=40)
    except Exception as e:
        log(f"  ! download failed {url}: {e}")
        return False
    if len(raw) > MAX_IMAGE_BYTES:
        # try thumb instead — caller passes thumburl when available, so this is rare
        log(f"  ! image too big ({len(raw)//1024}KB), keeping anyway: {dest.name}")
    dest.write_bytes(raw)
    return True


# ─── Build one artifact record ───────────────────────────────────────────
def build_record(artifact_id: str, en_title: str, ar_hint: str, museum_hint: str) -> Optional[dict]:
    log(f"==> {artifact_id}  EN={en_title}")
    rec = empty_record(artifact_id)

    # 1) EN summary + extract
    en_summary = wc.rest_summary("en", en_title)
    if en_summary is None:
        log(f"  ! EN summary missing for '{en_title}'")
        return None
    canonical_en = en_summary.get("titles", {}).get("canonical") or en_summary.get("title")
    rec["names"]["en"] = en_summary.get("title", canonical_en or en_title)
    en_extract = wc.page_extract_plain("en", canonical_en or en_title)
    en_parsed = wc.page_html_parse("en", canonical_en or en_title)
    en_wikitext = wc.page_wikitext("en", canonical_en or en_title)
    time.sleep(wc.REQUEST_DELAY)

    # 2) AR title via langlinks, fallback to hint
    ar_title = wc.lang_link(canonical_en or en_title, "ar") or ar_hint
    ar_summary = None
    ar_extract = None
    ar_parsed = None
    ar_wikitext = None
    if ar_title:
        try:
            ar_summary = wc.rest_summary("ar", ar_title)
        except Exception:
            ar_summary = None
        if ar_summary:
            canonical_ar = ar_summary.get("titles", {}).get("canonical") or ar_title
            rec["names"]["ar"] = ar_summary.get("title", canonical_ar)
            ar_extract = wc.page_extract_plain("ar", canonical_ar)
            ar_parsed = wc.page_html_parse("ar", canonical_ar)
            ar_wikitext = wc.page_wikitext("ar", canonical_ar)
            time.sleep(wc.REQUEST_DELAY)
        else:
            log(f"  ~ no AR Wikipedia page for {ar_title}")

    # 3) Descriptions
    en_intro = (en_summary or {}).get("extract", "")
    en_full = (en_extract or {}).get("extract", "") or en_intro
    rec["description"]["en"] = en_full[:8000]
    rec["description"]["en_intro"] = en_intro

    ar_intro = (ar_summary or {}).get("extract", "") if ar_summary else ""
    ar_full = (ar_extract or {}).get("extract", "") if ar_extract else ar_intro
    rec["description"]["ar"] = ar_full[:8000]
    rec["description"]["ar_intro"] = ar_intro

    # 4) Infobox parsing — try EN first, then AR
    box_en = wc.parse_wikitext_infobox(en_wikitext or "")
    box_ar = wc.parse_wikitext_infobox(ar_wikitext or "") if ar_wikitext else {}

    rec["material"] = [
        m.strip() for m in re.split(r",|;|\band\b|/|·|،", pick(box_en, EN_KEY_MAP["material"]))
        if m.strip()
    ]
    if not rec["material"] and box_ar:
        rec["material"] = [
            m.strip() for m in re.split(r",|;|\bو\b|/|·|،", box_ar.get("material", "") or box_ar.get("مادة", ""))
            if m.strip()
        ]

    if pick(box_en, EN_KEY_MAP["size_height"]):
        rec["dimensions"]["height"] = pick(box_en, EN_KEY_MAP["size_height"])
    if pick(box_en, EN_KEY_MAP["size_width"]):
        rec["dimensions"]["width"] = pick(box_en, EN_KEY_MAP["size_width"])
    if pick(box_en, EN_KEY_MAP["size_length"]):
        rec["dimensions"]["length"] = pick(box_en, EN_KEY_MAP["size_length"])
    if pick(box_en, EN_KEY_MAP["size_weight"]):
        rec["dimensions"]["weight"] = pick(box_en, EN_KEY_MAP["size_weight"])

    rec["category"] = pick(box_en, EN_KEY_MAP["type"]) or pick(box_en, EN_KEY_MAP["category"])
    rec["dynasty"]["en"] = pick(box_en, EN_KEY_MAP["dynasty"])
    if box_ar:
        rec["dynasty"]["ar"] = box_ar.get("dynasty", "") or box_ar.get("الأسرة", "") or box_ar.get("أسرة", "")

    # period
    rec["period"]["en"] = pick(box_en, EN_KEY_MAP["created_period"])
    if box_ar:
        rec["period"]["ar"] = box_ar.get("period", "") or box_ar.get("العصر", "") or box_ar.get("الحقبة", "")
    rec["period"]["year_min"] = parse_year(rec["period"]["en"]) if rec["period"]["en"] else None

    # discovery
    disc_year = parse_year(pick(box_en, EN_KEY_MAP["discovered_year"]))
    if disc_year:
        rec["discovery"]["year"] = disc_year
    rec["discovery"]["by_en"] = pick(box_en, EN_KEY_MAP["discovered_by"])

    # provenance
    rec["provenance"]["site_en"] = pick(box_en, EN_KEY_MAP["discovered_place"])
    if box_ar:
        rec["provenance"]["site_ar"] = box_ar.get("discovered_place", "") or box_ar.get("مكان الاكتشاف", "")

    # current_location
    loc_en = pick(box_en, EN_KEY_MAP["current_location"])
    rec["current_location"]["museum_en"] = loc_en
    if box_ar:
        rec["current_location"]["museum_ar"] = box_ar.get("current_location", "") or box_ar.get("الموقع الحالي", "") or box_ar.get("الموقع", "")
    if museum_hint in MUSEUMS:
        rec["current_location"]["museum_id"] = museum_hint
        rec["current_location"]["museum_ar"] = MUSEUMS[museum_hint]["ar"]["name"] or rec["current_location"]["museum_ar"]
        rec["current_location"]["museum_en"] = MUSEUMS[museum_hint]["en"]["name"] or rec["current_location"]["museum_en"]
        rec["current_location"]["city_ar"] = MUSEUMS[museum_hint]["ar"]["city"]
        rec["current_location"]["city_en"] = MUSEUMS[museum_hint]["en"]["city"]
        rec["current_location"]["country"] = "Egypt"
    else:
        rec["current_location"]["museum_id"] = museum_hint  # textual hint only

    # 5) Images: combine primary thumbnail + parsed image lists
    primary = (en_summary or {}).get("originalimage", {}).get("source", "") if en_summary else ""
    primary_filename = ""
    if primary:
        m = re.search(r"/([^/?]+\.(?:jpg|jpeg|png|gif|tif|tiff|webp))", primary, re.I)
        if m:
            primary_filename = urllib.parse.unquote(m.group(1))

    candidates = pick_images([en_parsed, ar_parsed], primary_filename)[:30]
    info = wc.commons_imageinfo(candidates)
    chosen: list[dict] = []
    idx = 0
    for fname in candidates:
        if len(chosen) >= MAX_IMAGES_PER_ARTIFACT:
            break
        meta = info.get(fname)
        if not meta:
            continue
        if not meta.get("url"):
            continue
        # Choose thumbnail (1600px) when available to keep size sane
        download_url = meta.get("thumburl") or meta.get("url")
        idx += 1
        out_name = safe_filename(artifact_id, idx, fname)
        dest = IMG_DIR / out_name
        if not download_image(download_url, dest):
            continue
        chosen.append({
            "filename": out_name,
            "source": "wikimedia_commons",
            "source_url": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(fname)}",
            "credit": meta.get("artist") or meta.get("credit") or "",
            "license": meta.get("license_short") or "",
            "license_url": meta.get("license_url", ""),
            "width": meta.get("width"),
            "height": meta.get("height"),
            "is_primary": (idx == 1),
            "caption_en": meta.get("description") or "",
            "object_name": meta.get("object_name", ""),
            "original_filename": fname,
        })
        time.sleep(0.2)
    rec["images"] = chosen

    # 6) Sources
    if en_summary:
        rec["sources"].append({
            "type": "wikipedia_en",
            "url": en_summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "title": rec["names"]["en"],
            "license": "CC-BY-SA-4.0",
        })
    if ar_summary:
        rec["sources"].append({
            "type": "wikipedia_ar",
            "url": ar_summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "title": rec["names"]["ar"],
            "license": "CC-BY-SA-4.0",
        })

    # 7) Tags from categories
    cats = []
    for cat in (en_extract or {}).get("categories", []) or []:
        cats.append(cat.get("title", "").replace("Category:", "").lower())
    rec["tags"] = sorted({c for c in cats if c and len(c) < 60})[:25]

    return rec


def write_record(rec: dict) -> Path:
    path = DATA_DIR / f"{rec['id']}.json"
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(only_ids: Optional[set[str]] = None) -> None:
    skipped: list[str] = []
    built: list[str] = []
    for entry in SEED:
        artifact_id, en_title, ar_hint, museum_hint = entry
        if only_ids and artifact_id not in only_ids:
            continue
        out_path = DATA_DIR / f"{artifact_id}.json"
        if out_path.exists() and not os.environ.get("FORCE"):
            log(f"-- {artifact_id} already exists, skipping (set FORCE=1 to rebuild)")
            built.append(artifact_id)
            continue
        try:
            rec = build_record(artifact_id, en_title, ar_hint, museum_hint)
            if rec is None:
                skipped.append(artifact_id)
                continue
            write_record(rec)
            built.append(artifact_id)
            log(f"  ok {artifact_id}: AR={'Y' if rec['description']['ar'] else 'N'} imgs={len(rec['images'])}")
        except Exception as e:
            log(f"  XX FAILED {artifact_id}: {type(e).__name__}: {e}")
            skipped.append(artifact_id)
        time.sleep(wc.REQUEST_DELAY)

    log(f"\nDONE. built={len(built)} skipped={len(skipped)}")
    if skipped:
        log("skipped: " + ", ".join(skipped))


if __name__ == "__main__":
    only = set(sys.argv[1:]) or None
    main(only_ids=only)
