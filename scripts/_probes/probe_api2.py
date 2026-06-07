"""Probe egymonuments.gov.eg WebAPI endpoints — POST with culture header."""
import json
import urllib.parse
import urllib.request
import time

BASE = "https://egymonuments.gov.eg"
HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ar,en;q=0.8",
    "Content-Type": "application/json",
    "Origin": BASE,
    "Referer": BASE + "/ar/collections",
}


def post(path, payload=None, culture="ar"):
    headers = {**HEADERS_BASE, "culture": culture}
    body = json.dumps(payload).encode("utf-8") if payload is not None else b"{}"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as e:
        try:
            return e.code, getattr(e, "read", lambda: b"")().decode("utf-8", errors="replace")[:500]
        except Exception:
            return "ERR", str(e)


def get(path, culture="ar"):
    headers = {**HEADERS_BASE, "culture": culture}
    req = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as e:
        try:
            return e.code, getattr(e, "read", lambda: b"")().decode("utf-8", errors="replace")[:500]
        except Exception:
            return "ERR", str(e)


# 1) GetPeriods is GET
print("\n=== GET /InnersWebAPI/GetPeriods (ar) ===")
status, body = get("/InnersWebAPI/GetPeriods", "ar")
print("status:", status)
print(body[:1500])

# 2) try POST endpoints with empty/typical bodies
probes = [
    ("/MapsWebAPI/GetTimelineDynasties", {}),
    ("/MapsWebAPI/GetFiltrationBoxLists", {}),
    ("/MapsWebAPI/GetAllMapPins", {}),
    ("/EgyptianTreasuresWebAPI/GetEgyptianTreasuresPage", {"pageIndex": 0, "pageSize": 8}),
    ("/InnersWebAPI/GetAntiquitiesByMuseumId", {"museumId": 1, "pageIndex": 0, "pageSize": 8}),
    ("/InnersWebAPI/GetAntiquitiesByMuseumId", {"MuseumId": 1, "PageIndex": 0, "PageSize": 8}),
    ("/InnersWebAPI/GetDynastiesByPeriodId", {"periodId": 1}),
    ("/SearchResultWebAPI/GetSearchResult", {"keyword": "تابوت", "pageIndex": 0, "pageSize": 8}),
]

for path, payload in probes:
    print(f"\n--- POST {path} body={payload} ---")
    status, body = post(path, payload, "ar")
    print("status:", status)
    print(body[:1200])
    time.sleep(0.4)
