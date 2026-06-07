"""MediaWiki API client for Arabic + English Wikipedia and Commons.

Pulls full extracts, infoboxes, images, interlanguage links, license info.
Pure-stdlib + bs4 to keep dependencies minimal.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

UA = "ArabicRAGProject/1.0 (vipegi9@gmail.com; educational; built with Claude Code)"
REQUEST_DELAY = 0.4  # seconds between requests, polite default
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 12  # short — fail fast and move on


def _request(url: str, headers: Optional[dict] = None, timeout: Optional[int] = None) -> bytes:
    h = {"User-Agent": UA, "Accept-Language": "ar,en;q=0.7"}
    if headers:
        h.update(headers)
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            # don't retry 4xx
            if 400 <= e.code < 500:
                raise
            last_err = e
            time.sleep(min(1.5 * attempt, 6))
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(min(1.5 * attempt, 6))
    raise last_err  # type: ignore[misc]


def _get_json(url: str) -> dict:
    raw = _request(url)
    return json.loads(raw.decode("utf-8", errors="replace"))


# ─── REST summary ────────────────────────────────────────────────────────
def rest_summary(lang: str, title: str) -> Optional[dict]:
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title, safe='')}"
    try:
        return _get_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


# ─── Action API: full extracts, infobox source, langlinks, images ────────
def action_query(lang: str, params: dict) -> dict:
    base = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
    }
    base.update(params)
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(base)
    return _get_json(url)


def page_extract_plain(lang: str, title: str) -> Optional[dict]:
    """Plain-text extract (full article, sectioned), pageimage, infobox via parse."""
    q = action_query(lang, {
        "titles": title,
        "prop": "extracts|pageimages|info|categories|langlinks|pageprops",
        "explaintext": "1",
        "exsectionformat": "wiki",
        "inprop": "url",
        "pithumbsize": "1280",
        "lllimit": "max",
        "cllimit": "max",
        "redirects": "1",
    })
    pages = q.get("query", {}).get("pages", [])
    if not pages:
        return None
    return pages[0] if isinstance(pages, list) else next(iter(pages.values()))


def page_html_parse(lang: str, title: str) -> Optional[dict]:
    """Parse the page HTML to access infobox HTML + images list."""
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "redirects": "1",
        "prop": "text|images|displaytitle|categories",
    }
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    try:
        d = _get_json(url)
        return d.get("parse")
    except urllib.error.HTTPError:
        return None


# ─── Cross-language: get interlanguage link from EN to AR ────────────────
def lang_link(en_title: str, target_lang: str = "ar") -> Optional[str]:
    q = action_query("en", {
        "titles": en_title,
        "prop": "langlinks",
        "lllang": target_lang,
        "redirects": "1",
    })
    pages = q.get("query", {}).get("pages", [])
    if not pages:
        return None
    p = pages[0] if isinstance(pages, list) else next(iter(pages.values()))
    for ll in p.get("langlinks", []) or []:
        if ll.get("lang") == target_lang:
            return ll.get("title")
    return None


# ─── Image metadata via Commons (license, author, source) ────────────────
def commons_imageinfo(filenames: list[str]) -> dict[str, dict]:
    """Bulk fetch imageinfo for File: titles. Returns {filename: info}."""
    if not filenames:
        return {}
    out: dict[str, dict] = {}
    for chunk_start in range(0, len(filenames), 30):
        chunk = filenames[chunk_start:chunk_start + 30]
        titles = "|".join(f"File:{name}" if not name.startswith("File:") else name for name in chunk)
        params = {
            "action": "query",
            "titles": titles,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "1600",
            "format": "json",
            "formatversion": "2",
        }
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
        try:
            d = _get_json(url)
            for p in d.get("query", {}).get("pages", []):
                title = p.get("title", "")
                if not title.startswith("File:"):
                    continue
                ii = p.get("imageinfo") or []
                if not ii:
                    continue
                info = ii[0]
                ext = info.get("extmetadata", {}) or {}
                key = title.removeprefix("File:").replace(" ", "_")
                out[key] = {
                    "url": info.get("url"),
                    "thumburl": info.get("thumburl"),
                    "width": info.get("width"),
                    "height": info.get("height"),
                    "mime": info.get("mime"),
                    "license_short": (ext.get("LicenseShortName") or {}).get("value", ""),
                    "license_url": (ext.get("LicenseUrl") or {}).get("value", ""),
                    "artist": _strip_html((ext.get("Artist") or {}).get("value", "")),
                    "credit": _strip_html((ext.get("Credit") or {}).get("value", "")),
                    "description": _strip_html((ext.get("ImageDescription") or {}).get("value", "")),
                    "object_name": _strip_html((ext.get("ObjectName") or {}).get("value", "")),
                    "date": (ext.get("DateTimeOriginal") or {}).get("value", ""),
                }
        except urllib.error.HTTPError:
            pass
        time.sleep(REQUEST_DELAY)
    return out


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(s: str) -> str:
    if not s:
        return ""
    s = _TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ─── Filtering image relevance ───────────────────────────────────────────
ICON_SUFFIX_RE = re.compile(
    r"(?:icon|symbol|flag|logo|map|location|sound|audio|edit|commons-logo)",
    re.I,
)


def is_relevant_image(filename: str) -> bool:
    f = filename.lower()
    if not f.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".webp")):
        return False
    if ICON_SUFFIX_RE.search(f):
        return False
    if any(s in f for s in ("flag_of", "coat_of_arms", "blason")):
        return False
    if f.startswith("commons-logo") or f.startswith("wiki"):
        return False
    return True


# ─── Infobox parsing helpers ──────────────────────────────────────────────
def parse_wikitext_infobox(wikitext: str) -> dict[str, str]:
    """Extract template parameters from the first {{Infobox ...}} call."""
    if not wikitext:
        return {}
    m = re.search(r"\{\{\s*[Ii]nfobox", wikitext)
    if not m:
        return {}
    i = m.start()
    depth = 0
    end = None
    for j in range(i, len(wikitext)):
        if wikitext[j:j + 2] == "{{":
            depth += 1
        elif wikitext[j:j + 2] == "}}":
            depth -= 1
            if depth == 0:
                end = j + 2
                break
    if end is None:
        return {}
    body = wikitext[i + 2:end - 2]
    out: dict[str, str] = {}
    # naive split on top-level pipes
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    k = 0
    while k < len(body):
        c = body[k]
        nxt = body[k:k + 2]
        if nxt in ("{{", "[["):
            depth += 1
            cur.append(c)
            k += 1
        elif nxt in ("}}", "]]"):
            depth = max(0, depth - 1)
            cur.append(c)
            k += 1
        elif c == "|" and depth == 0:
            parts.append("".join(cur))
            cur = []
            k += 1
            continue
        else:
            cur.append(c)
            k += 1
    parts.append("".join(cur))
    parts = parts[1:]  # first is the template name
    for p in parts:
        if "=" in p:
            key, _, val = p.partition("=")
            out[key.strip().lower()] = _clean_wikitext(val.strip())
    return out


WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
TEMPLATE_RE = re.compile(r"\{\{[^{}]+\}\}")
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.S)
HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_wikitext(s: str) -> str:
    s = REF_RE.sub("", s)
    # strip nested templates iteratively
    prev = None
    while prev != s:
        prev = s
        s = TEMPLATE_RE.sub("", s)
    s = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), s)
    s = HTML_TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ─── Wikitext source ──────────────────────────────────────────────────────
def page_wikitext(lang: str, title: str) -> Optional[str]:
    q = action_query(lang, {
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "redirects": "1",
    })
    pages = q.get("query", {}).get("pages", [])
    if not pages:
        return None
    p = pages[0] if isinstance(pages, list) else next(iter(pages.values()))
    revs = p.get("revisions") or []
    if not revs:
        return None
    return revs[0].get("slots", {}).get("main", {}).get("content")
