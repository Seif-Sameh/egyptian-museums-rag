"""Test Arabic Wikipedia API access via Python (handles unicode properly)."""
import urllib.request
import urllib.parse
import json

UA = "ArabicRAGProject/1.0 (educational; vipegi9@gmail.com)"


def get_json(url, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


# 1) REST summary endpoint
title = "قناع_دفن_توت_عنخ_آمون"
url = f"https://ar.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
print("URL:", url)
try:
    d = get_json(url)
    print("Title:", d.get("title"))
    print("Description:", d.get("description"))
    print("Extract:", (d.get("extract") or "")[:400])
    img = d.get("originalimage")
    print("Image:", img.get("source") if img else None)
except Exception as e:
    print("ERR:", e)

print("\n=== Action API ===")
params = {
    "action": "query",
    "titles": title,
    "prop": "extracts|pageimages|info",
    "exintro": "",
    "explaintext": "",
    "format": "json",
    "inprop": "url",
    "piprop": "original",
}
url2 = "https://ar.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
try:
    d = get_json(url2)
    pages = d["query"]["pages"]
    for pid, p in pages.items():
        print("Page:", p.get("title"))
        print("Extract:", (p.get("extract") or "")[:400])
        if p.get("original"):
            print("Image:", p["original"].get("source"))
        print("URL:", p.get("fullurl"))
except Exception as e:
    print("ERR:", e)
