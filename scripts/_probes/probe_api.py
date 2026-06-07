"""Probe egymonuments.gov.eg WebAPI endpoints."""
import json
import urllib.parse
import urllib.request
import time

BASE = "https://egymonuments.gov.eg"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ar,en;q=0.8",
    "Referer": BASE + "/ar/collections",
}


def get(path, params=None, lang="A"):
    qp = {"lan": lang}
    if params:
        qp.update(params)
    url = f"{BASE}{path}"
    if qp:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(qp)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status, body[:1500]
    except Exception as e:
        return "ERR", str(e)


probes = [
    ("/InnersWebAPI/GetPeriods", None),
    ("/MapsWebAPI/GetTimelineDynasties", None),
    ("/MapsWebAPI/GetFiltrationBoxLists", None),
    ("/MapsWebAPI/GetAllMapPins", None),
    ("/EgyptianTreasuresWebAPI/GetEgyptianTreasuresPage", {"pageNo": 1, "pageSize": 10}),
    ("/InnersWebAPI/GetAntiquitiesByMuseumId", {"museumId": 1, "pageNo": 1, "pageSize": 10}),
    ("/InnersWebAPI/GetAntiquitiesByMuseumId", {"museumId": 2, "pageNo": 1, "pageSize": 10}),
    ("/SearchResultWebAPI/GetSearchResult", {"keyword": "tutankhamun", "pageNo": 1, "pageSize": 10}),
]

for path, params in probes:
    print(f"\n--- GET {path} {params} ---")
    status, body = get(path, params)
    print(f"status={status}")
    print(body[:1200])
    time.sleep(0.5)
