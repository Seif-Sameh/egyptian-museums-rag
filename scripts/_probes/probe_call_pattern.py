"""Find how the JS bundle calls these endpoints (method, prefix, payload shape)."""
import re
from pathlib import Path

js = Path("/tmp/em_main.js").read_text()

# Find the actual call site for GetAntiquitiesByMuseumId
keyword = "GetAntiquitiesByMuseumId"
i = js.find(keyword)
if i >= 0:
    print(js[max(0, i - 500): i + 500])
print("\n=== call sites for GetEgyptianTreasuresPage ===")
i = js.find("GetEgyptianTreasuresPage")
if i >= 0:
    print(js[max(0, i - 500): i + 500])
print("\n=== Search for this.http or this._http patterns ===")
for m in re.finditer(r"this\.(?:http|_http|httpClient)\.(get|post|put)\(['\"]([^'\"]+)['\"]", js):
    print(m.group(1).upper(), m.group(2))
print("\n=== fetch( calls ===")
for m in re.finditer(r"fetch\(['\"]([^'\"]+)['\"]", js):
    print(m.group(1))
print("\n=== Look for env / baseUrl / apiUrl assignment ===")
for m in re.finditer(r"(apiUrl|baseUrl|API_URL|environment\.\w+|this\.\w*[Uu]rl)\s*[:=]\s*['\"]([^'\"]+)['\"]", js):
    print(m.group(1), "=", m.group(2))
